# ntu auto sign discord bot

## Project Overview

This project links a Discord bot with an automated system. It helps you manage daily tasks through Discord. It automatically interacting with a website at certain times (like morning and afternoon) and raise notice asking to interact or not last night.

## Important Note & Disclaimer
This project is an experiment. Things might be out of work.

The missing `auto_signing` contents can be found in other Github repo. Be aware that using automation like this might go against a website's rules and could cause unexpected issues. Users are responsible for anything that happens from using this project. The developer isn't responsible for any problems or losses. Please check the code carefully and test it in a safe place.


## Key Features
* Discord Bot: Use Discord commands to check and manage tasks.

* Automated Scheduling: The system runs tasks automatically at set times.

* Daily Task Assignment: The bot asks you on Discord if you want certain daily routines to run the next day.

* Status & Notifications: Get updates and alerts about task progress in your Discord channel.

## How to Set Up & Run

* Get Ready:
    * Install Python 3.8+ and pip.
    * Set your Discord Bot Token as an environment variable (discord_bot_token).
    * Install necessary Python libraries (like discord.py, loguru).

* Configure:
    * Edit configure.py to set up paths and your Discord channel ID.
    * Important: The auto_sign_in_path points to another script that handles automated web interactions at specific times. Make sure this script is set up correctly.

* Start:
    * Go to the discordBot directory.
    * Run python `discord_bot.py`.

## Commands In Discord Robot

`/check_tomorrow`: See tomorrow's task status.

`/check_today`: See today's task status.

`/reorder_tomorrow`: Force tomorrow's task to be assigned.

`/reorder_today`: Force today's task to be assigned.

`/check_running`: See if the automated tasks are active.

`/remove_cog`: Stop the task management part.

`/reload_cog`: Restart the task management part.