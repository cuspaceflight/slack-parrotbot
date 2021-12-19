#!/bin/sh
stdbuf -o0 -e0 /usr/bin/python3 /opt/slack-parrotbot/parrotbot.py \
	>/var/opt/slack-parrotbot/stdout \
	2>/var/opt/slack-parrotbot/stderr
