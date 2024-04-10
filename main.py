# Press the green button in the gutter to run the script.
import json
import random
import socket
import struct
import subprocess
import time
import certifi
import masscan
import pymongo
from mcstatus import JavaServer
from discordwebhook import send_message_to_discord

import json

with open('config.json', 'r') as f:
    config = json.load(f)

mongo_uri = config['database_uri']


#Mongo url hide it in future
mongo_uri = config['database_uri']
# Create a MongoDB client with SSL certificate verification using certifi
client = pymongo.MongoClient(
    mongo_uri,
    tls=True,
    tlsCAFile=certifi.where()
)
#collections for mongo db
mydb = client['db_mcservers']
collection = mydb["cn_mcservers3"]
collection2 = mydb["cn_players"]

#global variable
global ip_ranges


class StatusPing:
    """ Get the ping status for the Minecraft server """

    def __init__(self, host='localhost', port=25565, timeout=5):
        """ Init the hostname and the port """
        self._host = host
        self._port = port
        self._timeout = timeout

    def _unpack_varint(self, sock):
        """ Unpack the varint """
        data = 0
        for i in range(5):
            ordinal = sock.recv(1)

            if len(ordinal) == 0:
                break

            byte = ord(ordinal)
            data |= (byte & 0x7F) << 7*i

            if not byte & 0x80:
                break

        return data

    def _pack_varint(self, data):
        """ Pack the var int """
        ordinal = b''

        while True:
            byte = data & 0x7F
            data >>= 7
            ordinal += struct.pack('B', byte | (0x80 if data > 0 else 0))

            if data == 0:
                break

        return ordinal

    def _pack_data(self, data):
        """ Page the data """
        if type(data) is str:
            data = data.encode('utf8')
            return self._pack_varint(len(data)) + data
        elif type(data) is int:
            return struct.pack('H', data)
        elif type(data) is float:
            return struct.pack('L', int(data))
        else:
            return data

    def _send_data(self, connection, *args):
        """ Send the data on the connection """
        data = b''

        for arg in args:
            data += self._pack_data(arg)

        connection.send(self._pack_varint(len(data)) + data)

    def _read_fully(self, connection, extra_varint=False):
        """ Read the connection and return the bytes """
        packet_length = self._unpack_varint(connection)
        packet_id = self._unpack_varint(connection)
        byte = b''

        if extra_varint:
            # Packet contained netty header offset for this
            if packet_id > packet_length:
                self._unpack_varint(connection)

            extra_length = self._unpack_varint(connection)

            while len(byte) < extra_length:
                byte += connection.recv(extra_length)

        else:
            byte = connection.recv(packet_length)

        return byte

    def get_status(self):
        """ Get the status response """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
            connection.settimeout(25)
            connection.connect((self._host, self._port))

            # Send handshake + status request
            self._send_data(connection, b'\x00\x00', self._host, self._port, b'\x01')
            self._send_data(connection, b'\x00')

            # Read response, offset for string length
            data = self._read_fully(connection, extra_varint=True)

            # Send and read unix time
            self._send_data(connection, b'\x01', time.time() * 1000)
            unix = self._read_fully(connection)

        # Load json and return
        response = json.loads(data.decode('utf8'))
        try:
            response['ping'] = int(time.time() * 1000) - struct.unpack('L', unix)[0]
            return response
        except struct.error:
            print("error")


#is responsible for generating the ip's 
def getip():
    #use the global variable
    global ip_ranges
    #set 2 lists to generate the ip's and shuffle them
    A = list(range(1, 0xff))
    B = list(range(1, 0xff))
    random.shuffle(B)
    random.shuffle(A)
    ip_ranges = []
    for a in A:
        for b in B:
            ip_range = "{}.{}.0.0/16".format(a, b)
            ip_ranges.append(ip_range)

#is responsible for scanning the ip's and saving them 
def Scanning():
    while True:
        #shuffle the ip's again
        random.shuffle(ip_ranges)
        for ip_range in ip_ranges:
            #print the ip range we are about to scan
            print(ip_range)
            try:
                mas = masscan.PortScanner()
                #masscan about to scan port 25565 with a rate limit of 15000 packages
                mas.scan(ip_range, ports='25565', arguments='--max-rate 5000')
                for ip in mas.scan_result['scan']:
                    host = mas.scan_result['scan'][ip]
                    print("{}&{}".format(ip, host))
                    if "tcp" in host and 25565 in host['tcp']:
                        print("====================================================================================")
                        print("{}".format(ip))

                        try:
                            #try getting information about server
                            status_ping = StatusPing(ip)
                            try:
                                
                                for i in status_ping.get_status()["players"]["sample"]:
                                    playerinfo = {
                                    "uuid": i["id"],
                                    "name": i["name"],
                                    "Ip": ip
                                    }
                                    #checks if player uuid is a bot
                                    if(i["id"] == "00000000-0000-0000-0000-000000000000"):
                                        continue
                                    print(playerinfo)
                                    collection2.insert_one(playerinfo)
                            except KeyError:
                                print("there are no players")
                            resultsglobal = "no value"
                            try:
                                result = subprocess.run(['node', 'mineflayerconnectnew.js', ip], capture_output=True, text=True)
                                print("Standard output:", result.stdout)
                                print("Error output:", result.stderr)
                                if "Spawn" in result.stdout:
                                    #check if we spawned on the minecraft server
                                    resultsglobal = "No Whitelist"
                                elif "Whitelisted" or "Whitelist" or "multiplayer.disconnect.not_whitelisted" in result.stdout:
                                    resultsglobal = "Does whitelist"
                                elif "Forge" or "mods" in result.stdout:
                                    resultsglobal = "Forge server"
                            except subprocess.CalledProcessError as e:
                                print("An error occurred while running the JavaScript script:", str(e))
                            print(resultsglobal)
                            serverinfo = {
                                "Ip": ip,
                                "description": status_ping.get_status()["description"],
                                "version": status_ping.get_status()["version"],
                                "players": status_ping.get_status()["players"],
                                "reason": resultsglobal
                            }
                            print(serverinfo)
                            #collection.update_one(serverinfo,serverinfo)
                            filter = { 'Ip': ip }
                            if(collection.count_documents(filter) >= 1):
                                #collection if found
                                print("we have updated the record")
                                newvalues = { "$set": { 'description': status_ping.get_status()["description"],
                                                        'version': status_ping.get_status()["version"],
                                                        'players': status_ping.get_status()["players"],
                                                        'reason': resultsglobal }}
                                collection.update_one(filter, newvalues)
                            else:
                                #collection if not found
                                print("new record has been inserted")
                                send_message_to_discord(f"deze server is: {resultsglobal} we hebben een server gevonden met dit ip: {ip} versie : {serverinfo['version']['name']} en zoveel speler {serverinfo['players']['online']}")
                                collection.insert_one(serverinfo)
                        except socket.timeout:
                            print("took to long")
                        except json.JSONDecodeError:
                            print("een vak was wss leeg")
            except masscan.NetworkConnectionError:
                print("error" + str(masscan.NetworkConnectionError))
            except ConnectionResetError:
                print("connectionerror")


def main():
    getip()
    Scanning()

main()
