from datetime import datetime
from subprocess import check_output

from slack_bolt.adapter.socket_mode import SocketModeHandler

from shared import *

import parrotmaker_slack
import pong_slack
import gdrive_slack
import live_archive

print("Starting parrotbot...", flush=True)

@app.command("/parrotcheckhealth")
def parrotcheckhealth(client, ack, body, say):
	MAX_CHARS=2500

	log = check_output(config['log']['command'], shell=True, text=True).replace('files.slack.com', '********')
	log_lines = log.split('\n')
	log_messages = []

	# incredibly jank but whatever
	while len(log_lines) > 0:
		msg = ""
		while len(log_lines) > 0 and len(msg) + len(log_lines[0]) <= MAX_CHARS:
			msg += log_lines.pop(0) + '\n'
		log_messages.append(msg)

	if "quiet" in body['text']:
		ack("I'm running! Here is my latest log:" \
			"\n```\n" + log_messages[-1] + '```')
	else:
		say("I'm running! Here is my log:")
		for msg in log_messages:
			say("\n```\n" + msg + '```', unfurl_media = False, unfurl_links=False)
		ack()


if __name__ == "__main__":
	# why no do while python??
	cursor = None
	while cursor != '':
		conversations = app.client.conversations_list(cursor=cursor)
		for chan in conversations['channels']:
			if not (chan['is_im'] or chan['is_member'] or chan['is_archived']):
				app.client.conversations_join(channel=chan['id'])
				print(f"Joined {chan['name']}", flush=True)
		cursor = conversations['response_metadata']['next_cursor']

	SocketModeHandler(app, open("/opt/slack-parrotbot/secrets/SLACK_APP_TOKEN").read()).start()

