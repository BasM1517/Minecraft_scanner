const config = require('./config.json');

const usernameconfig = config.minecraft_username;
const passwordconfig = config.password;

const mineflayer = require('mineflayer');
const ip = process.argv[2];

const bot = mineflayer.createBot({
    host: ip, // optional
    port: 25565,       // optional
    // Account cosmicdolphin69
    username: usernameconfig, // email and password are required only for
    password: passwordconfig,          // online-mode=true servers
    version: false,                 // false corresponds to auto version detection (that's the default), put for example "1.8.8" if you need a specific version
    auth: 'microsoft'      // optional; by default uses mojang, if using a microsoft account, set to 'microsoft'
  })
  bot.on('spawn', () => {
    console.log('[Debug] Logged in as user: [' + bot._client.username + ']');
    console.log('[Debug] Logged in as user: [' + bot.username + ']');
    bot.end()
    console.log('Spawn event occurred!');
    return("succesfull")
});
bot.on('error', (err) => {
  //console.error('An error occurred:', err);
  console.error('An error occurred:', err);
  return("error")
});

bot.on('kicked', (reason, loggedIn) => {
  //console.error('Kicked for reason:', reason);
  //console.error(reason)
  console.error('Kicked for reason:', reason);
  return((reason))
});