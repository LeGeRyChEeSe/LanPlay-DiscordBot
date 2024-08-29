<h1 align='center'>LanPlay-DiscordBot</h1>
<p align="center">
<img src="https://github.com/LeGeRyChEeSe/LanPlay-DiscordBot/blob/main/lansbot.jpg?raw=true" align="center" height=350 alt="LanPlay-DiscordBot" />
</p>
<p align="center">
<img src='https://visitor-badge.laobi.icu/badge?page_id=LeGeRyChEeSe.LanPlay-DiscordBot', alt='Visitors'/>
<a href="https://github.com/LeGeRyChEeSe/LanPlay-DiscordBot/stargazers">
<img src="https://img.shields.io/github/stars/LeGeRyChEeSe/LanPlay-DiscordBot" alt="Stars"/>
</a>
<a href="https://github.com/LeGeRyChEeSe/LanPlay-DiscordBot/issues">
<img src="https://img.shields.io/github/issues/LeGeRyChEeSe/LanPlay-DiscordBot" alt="Issues"/>
</a>

<p align="center">
A Discord bot that provides information on <a href="http://lan-play.com">LAN Play</a> servers, players, and games played.
<p align="center">

# Table of Contents
- [Get API Key](#get-api-key)
- [Create a Bot Account](#create-a-bot-account)
- [Invite the bot into your server](#invite-the-bot-into-your-server)
- [Run the Bot](#run-the-bot)
- [Commands Available](#commands-available)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Star History](#star-history)


## Get API Key

To use the LanPlay package you will need a specific, non-transferable API key that can be retrieved from <a href="http://www.lan-play.com">LanPlay</a>.<br>

Please follow these steps :

1. Open a Web Browser and go to http://www.lan-play.com

2. Open a Console Mode (<b>Ctrl + Shift + C</b> or <b>F12</b> should work, or Google is your friend to find how to access the Console Mode 🫠)

3. Go to `Network` tab and refresh the current page

4. Search a line named `getMonitors` and click on it

5. Open the `Payload` tab

6. Copy the `api_key` value and store it in safe location for the [Run the Bot](#run-the-bot) step.

## Create a Bot Account

1. Make sure you’re logged on to the [Discord website](https://discord.com/).

2. Navigate to the [Discord Application](https://discord.com/developers/applications) for developers.

3. Click on the `New Application` button.

4. Give the application a name and click `Create`.

5. Navigate to the `Bot` tab to configure it.

6. Make sure that `Public Bot` is ticked if you want others to invite your bot.

	- You should also make sure that `Require OAuth2 Code Grant` is unchecked.

7. Copy the token using the `Copy` button and store it in safe location for the [Run the Bot](#run-the-bot) step.

	- <b>This is not the Client Secret at the General Information page.</b>

		> It should be worth noting that this token is essentially your bot’s password. You should never share this with someone else. In doing so, someone can log in to your bot and do malicious things, such as leaving servers, ban all members inside a server, or pinging everyone maliciously.
		>
		> The possibilities are endless, so do not share this token.
		>
		> If you accidentally leaked your token, click the `Regenerate` button as soon as possible. This revokes your old token and re-generates a new one. Now you need to use the new token to login.

## Invite the bot into your server

1. Navigate to the [Discord Application](https://discord.com/developers/applications) for developers.

2. Open the App you previously created for the Bot.

3. Navigate to `OAuth2` tab.

4. Scroll down and in `OAuth2 URL Generator` -> `SCOPES`, tick these boxes:

	- `bot`
	- `applications.commands`

5. Scroll down and in `BOT PERMISSIONS`, tick these boxes:

	- `Manage Expressions`
	- `Create Expressions`
	- `Send Messages`
	- `Send Messages in Threads`
	- `Embed Links`
	- `Read Message History`

6. Make sure that `INTEGRATION TYPE` value is `Guild Install`.

7. Copy/Paste the `GENERATED URL` at bottom to a new Browser Tab and add it to your Discord Server.

## Run the Bot

- Download [Docker](https://www.docker.com) and install it on your computer.

- Make sure you got both [api_key](#get-api-key) and [token](#create-a-bot-account) values, and [invited the bot to your server](#invite-the-bot-into-your-server).

- Open a <b>Windows Terminal</b> and execute the following command to run the Discord Bot:

```docker
docker run -e API_LAN_KEY=<your_lan_api_key> -e TOKEN=<your_discord_token> garohrl/lanplay-discordbot:latest
```

- If you want the Discord Bot running in background:

```docker
docker run -d -e API_LAN_KEY=<your_lan_api_key> -e TOKEN=<your_discord_token> garohrl/lanplay-discordbot:latest
```

> Replace `<your_lan_api_key>` with your [`api_key`](#get-api-key) and replace `<your_discord_token>` with your [`token`](#create-a-bot-account).

## Commands Available

| Command | Input | Output | Permission |
| :-----: | :--------: | :----: | :--------: |
| `/help` | `None`     | ![Help Menu](https://github.com/LeGeRyChEeSe/LanPlay-DiscordBot/blob/main/ressources/help.png?raw=true) | `Everybody` |
| `/lan`  | <i>select a server</i> | ![LanPlay Server Infos](https://github.com/LeGeRyChEeSe/LanPlay-DiscordBot/blob/main/ressources/lan.png?raw=true) | `Everybody` |
| `/add`  | `server`<br><i>e.g. 'tekn0.net:11451'</i> | ![Status of server addition](https://github.com/LeGeRyChEeSe/LanPlay-DiscordBot/blob/main/ressources/add.png?raw=true) | `Admin` |
| `/delete` | `server`<br><i>e.g. 'tekn0.net:11451'</i> | ![Status of server deletion](https://github.com/LeGeRyChEeSe/LanPlay-DiscordBot/blob/main/ressources/delete.png?raw=true) | `Admin` |

## Contributing

Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/NewFeature`)
3. Commit your Changes (`git commit -m 'Add some NewFeature'`)
4. Push to the Branch (`git push origin feature/NewFeature`)
5. Open a Pull Request


<i>Thanks to every [contributors](https://github.com/LeGeRyChEeSe/LanPlay-DiscordBot/graphs/contributors) who have contributed in this project.</i>

## License

Distributed under the MIT License. See [LICENSE](https://github.com/LeGeRyChEeSe/LanPlay-DiscordBot/blob/main/LICENSE) for more information.

## Acknowledgements

Shoutout to <b>LizardByte</b> for the Sunshine repo: https://github.com/LizardByte/Sunshine

Shoutout to <b>itsmikethetech</b> for the Virtual Display Driver repo: https://github.com/itsmikethetech/Virtual-Display-Driver

Thanks to <b>Cynary</b> for the Sunshine Virtual Monitor scripts: https://github.com/Cynary/sunshine-virtual-monitor

Shoutout to <b>JosefNemec</b> for Playnite: https://github.com/JosefNemec/Playnite

Shoutout to <b>Nonary</b> for the PlayNiteWatcher script: https://github.com/Nonary/PlayNiteWatcher

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=LeGeRyChEeSe/LanPlay-DiscordBot&type=Date)](https://star-history.com/#LeGeRyChEeSe/LanPlay-DiscordBot&Date)

----

Author/Maintainer: [Garoh](https://github.com/LeGeRyChEeSe/) | Discord: garohrl