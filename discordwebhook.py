import requests
import json
import json

with open('config.json', 'r') as f:
    config = json.load(f)

# Replace with your webhook URL
webhook_url = config['webhook_url']

def send_message_to_discord(message_content):
    username = 'Spiffo'

    # Construct the payload
    payload = {
        'content': message_content,
        'username': username
    }

    # Send the POST request to the webhook URL
    response = requests.post(
        webhook_url,
        data=json.dumps(payload),
        headers={'Content-Type': 'application/json'}
    )

    # Check the response
    if response.status_code ==  204:
        print('Message sent successfully.')
    else:
        print(f'Failed to send message, status code: {response.status_code}, response: {response.text}')
