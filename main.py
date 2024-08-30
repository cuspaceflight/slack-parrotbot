from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from shared import *

if config['features_enabled'] is not None:
	for feat in config['features_enabled']:
		exec(f"import {feat}")

print("Starting parrotbot...", flush=True, file=info_stream)


@slack_app.command("/parrotcheckhealth")
async def parrotcheckhealth(client, ack, body, say):
	user_id = body["user_id"]
	await ack(f"Hi <@{user_id}>!")
	MAX_CHARS=2500

	log = await async_check_output(config['log']['command'], shell=True)
	log = log.decode().replace('files.slack.com', '********')
	log_lines = log.split('\n')
	log_messages = []
	# incredibly jank but whatever
	while len(log_lines) > 0:
		msg = ""
		while len(log_lines) > 0 and len(msg) + len(log_lines[0]) <= MAX_CHARS:
			msg += log_lines.pop(0) + '\n'
		log_messages.append(msg)

	if "quiet" in body['text']:
		await ack("I'm running! Here is my latest log:" \
		    "\n```\n" + log_messages[-1] + '```')
	else:
		await say("I'm running! Here is my log:")
		for msg in log_messages:
			await say("\n```\n" + msg + '```', unfurl_media = False, unfurl_links=False)
		await ack()


async def main():
	# why no do while python??
	cursor = None
	while cursor != '':
		conversations = await slack_app.client.conversations_list(cursor=cursor)
		for chan in conversations['channels']:
			if not (chan['is_im'] or chan['is_member'] or chan['is_archived']):
				await slack_app.client.conversations_join(channel=chan['id'])
				print(f"Joined {chan['name']}", flush=True, file=info_stream)
		cursor = conversations['response_metadata']['next_cursor']
	slack_handler = AsyncSocketModeHandler(slack_app, config['slack_app_token'])
	await slack_handler.start_async()

if __name__ == "__main__":
	import asyncio
	asyncio.run(main())
