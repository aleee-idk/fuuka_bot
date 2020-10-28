#!/bin/bash

sleep 60
cd /home/pi/scripts/bots/discord/radio/
pip3 install discord.py --upgrade
/usr/bin/python3 bot.py
