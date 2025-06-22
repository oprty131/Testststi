const { Client, GatewayIntentBits, Collection, Events, REST, Routes, SlashCommandBuilder } = require('discord.js');
const express = require('express');
require('dotenv').config(); // Make sure to create a .env file with your token

// Setup express (keeps bot alive on Replit/UptimeRobot)
const app = express();
app.get('/', (req, res) => res.send('Bot is alive!'));
app.listen(3000, () => console.log('Web server running on port 3000'));

// Create Discord client
const client = new Client({
    intents: [GatewayIntentBits.Guilds]
});

client.commands = new Collection();

// Define the /aide command
const aideCommand = new SlashCommandBuilder()
    .setName('aide')
    .setDescription('Affiche de l’aide')
    .setDMPermission(true);

client.commands.set(aideCommand.name, {
    data: aideCommand,
    async execute(interaction) {
        await interaction.reply('Voici de l’aide en message privé !');
    }
});

// Register commands globally (or use guild ID for testing)
client.once(Events.ClientReady, async (c) => {
    console.log(`✅ Logged in as ${c.user.tag}`);

    const rest = new REST({ version: '10' }).setToken(process.env.TOKEN);

    try {
        console.log('🔁 Refreshing slash commands...');
        await rest.put(
            Routes.applicationCommands(c.user.id),
            { body: [aideCommand.toJSON()] }
        );
        console.log('✅ Slash commands registered!');
    } catch (error) {
        console.error('❌ Error registering commands:', error);
    }
});

// Listen for slash commands
client.on(Events.InteractionCreate, async (interaction) => {
    if (!interaction.isChatInputCommand()) return;

    const command = client.commands.get(interaction.commandName);
    if (!command) return;

    try {
        await command.execute(interaction);
    } catch (err) {
        console.error(err);
        await interaction.reply({ content: 'There was an error executing this command.', ephemeral: true });
    }
});

// Login bot
client.login(process.env.TOKEN);
