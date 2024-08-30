import json
from datetime import datetime
from pathlib import Path
import aiofiles

from shared import *

archive_path = Path(config['live_archive']['archive_path'])
file_locks = {}

def timestamp_to_date_string(ts):
	"""Converts a Slack timestamp into an ISO date (used in naming the daily JSON logs)"""
	if isinstance(ts, float):
		return datetime.fromtimestamp(ts).date().isoformat()
	elif isinstance(ts, str):
		return datetime.fromtimestamp(float(ts)).date().isoformat()
	else:
		raise TypeError("Expected either float or string timestamp")


async def channel_id_to_name(channel_id):
	"""Gets the current name of the channel with ID 'channel_id'"""
	res = await slack_app.client.conversations_info(channel=channel_id)
	if "ok" not in res.data or not res["ok"]:
		print(f"Error message:{res}", file=err_stream, flush=True)
		raise ConnectionError(f"conversations_info(channel={channel_id}) web request failed")
	channel_name = res["channel"]["name"]
	return channel_name

def create_lock(file_path):
	if file_path not in file_locks:
		file_locks[file_path] = asyncio.Lock()


async def log_file_path(channel_id, ts):
	"""Returns a Path object pointing to the JSON logfile of a message with timestamp 'ts' in channel 'channel_id'"""
	channel_name = await channel_id_to_name(channel_id)
	return archive_path / channel_name / (timestamp_to_date_string(ts) + ".json")

@slack_app.event("message")
async def archive_message(message):
	"""Runs on every message event and archives it if it's not hidden"""
	print("Message received", flush=True, file=debug_stream)

	# As message events are sent before 'channel_rename' events we're dealing with them here
	# Otherwise the program would still need to handle it to put it in the correct folder
	if "subtype" in message:
		if message['subtype'] == "channel_name":
			await rename_channel(message['channel'], message['old_name'], message['name'])
		elif message['subtype'] ==  "message_changed":
			await update_message(message['channel'], message['message']['ts'], message['message'])

	# Thread reply, need to edit parent message
	# Cannot filter on subtype as no subtype field is omitted due to bug in Slack API
	# See here: https://api.slack.com/events/message/message_replied
	if "thread_ts" in message:
		await add_thread_reply(message['channel'], message['thread_ts'],
						 message['user'], message['ts'])

	if "hidden" in message:
		if not message['hidden']:
			await add_to_archive(message)
			# This probably should not ever occur,
			# because if the message has a 'hidden' field it's probably always true
	else:
		await add_to_archive(message)


async def update_message(channel_id, ts, updated_message):
	"""Replaces message with timestamp 'ts' in channel 'channel_id' with updated message"""
	log_path = await log_file_path(channel_id, ts)
	create_lock(log_path)
	print(f"Attempting to acquire file lock for {log_path}",
		  file=debug_stream, flush=True)
	async with file_locks[log_path]:
		print(f"Acquired file lock for {log_path}",
			  file=debug_stream, flush=True)
		async with aiofiles.open(log_path, "r") as log_file:
			log_string = await log_file.read()

		message_list = json.loads(log_string) # No async way of doing this afaik
		for message in message_list:
			# Update fields of message
			# This is done via iteration instead of a complete replacement
			# As updated_message might not contain reactions and other stuff
			if message['ts'] == ts:
				for (key, value) in updated_message.items():
					message[key] = value
		log_string = json.dumps(message_list, indent=4)

		async with aiofiles.open(log_path, "w") as log_file:
			await log_file.write(log_string)
	print(f"Released file lock for {log_path}",
		  file=debug_stream, flush=True)

async def add_thread_reply(channel_id, thread_ts, reply_user, reply_ts):
	"""Adds a thread reply object to an archived message"""
	log_path = await log_file_path(channel_id, thread_ts)
	create_lock(log_path)
	print(f"Attempting to acquire file lock for {log_path}",
		  file=debug_stream, flush=True)
	async with file_locks[log_path]:
		print(f"Attempting to acquire file lock for {log_path}",
			  file=debug_stream, flush=True)
		async with aiofiles.open(log_path, 'r') as log_file:
			message_string = await log_file.read()

		message_list = json.loads(message_string)
		message = next((m for m in message_list if m['ts'] == thread_ts), None)
		if message is not None:
			if "reply_count" in message:
				message['reply_count'] += 1
			else:
				message['reply_count'] = 1

			reply = {"user": reply_user, "ts": reply_ts}
			if "replies" in message:
				message['replies'].append(reply)
			else:
				message['replies'] = [reply]

			if "reply_users" in message:
				if reply_user not in message['reply_users']:
					message['reply_users'].append(reply_user)
					if "reply_users_count" in message:
						message['reply_users_count'] += 1
					else:
						message['reply_users_count'] = len(message['reply_users'])
			else:
				message['reply_users'] = [reply_user]
				message['reply_users_count'] = 1
				# TODO: Cover the weird case of no reply users but an already existing reply_users_count
				# Though not sure how relevant this is, as slack-export-viewer does not seem to care
		else:
			print(f"Received reply to thread (channel={channel_id}, ts={reply_ts}) but have not found"
				  f"original thread with ts = {thread_ts}.", file=err_stream, flush=True)
		log_string = json.dumps(message_list, indent=4)
		async with aiofiles.open(log_path, "w") as log_file:
			await log_file.write(log_string)
	print(f"Released file lock for {log_path}",
		  file=debug_stream, flush=True)



async def rename_channel(channel_id, old_name, new_name):
	"""Renames channel folders and updates channel.json"""
	channel_list_path = archive_path / "channels.json"
	create_lock(channel_list_path)
	print(f"Attempting to acquire file lock for {channel_list_path}",
		  file=debug_stream, flush=True)
	async with file_locks[channel_list_path]:
		print(f"Acquired file lock for {channel_list_path}",
			  file=debug_stream, flush=True)
		async with aiofiles.open(channel_list_path, 'r') as channel_list:
			old_channel_list_string = await channel_list.read()
		old_channel_list = json.loads(old_channel_list_string)
		channel = next((ch for ch in old_channel_list if ch['id'] == channel_id), None)
		if channel is not None:
			channel['name'] = new_name
		else:
			print(f"Renamed channel (id={channel_id}) from {old_name} to {new_name},"
				  f"but have not found channel with id on channels.json",
				  file=err_stream, flush=True)

		old_channel_list_string = json.dumps(old_channel_list, indent=4)
		async with aiofiles.open(channel_list_path, "w") as channel_list:
			await channel_list.write(old_channel_list_string)

		print(f"Channel rename event from {old_name} to {new_name}", flush=True,
				file=info_stream)
		if old_name is not None:
			old_path = archive_path / old_name
			new_path = archive_path / new_name
			old_path.rename(new_path)
		else:
			print(f"Attempted to rename channel id {channel_id}, but it doesn't exist",
				  flush=True, file=warn_stream)
	print(f"Released file lock for {channel_list_path}",
		  file=debug_stream, flush=True)


@slack_app.event("channel_created")
async def create_channel(client, payload):
	"""On channel creation, if it's an actual channel joins then adds it into channels.json"""
	channel = payload['channel']
	channel_id = channel['id']

	# Get all detailed channel object
	res = await client.conversations_info(channel=channel_id)
	if "ok" not in res.data or not res['ok']:
		print(f"Error message: {res}", file=err_stream, flush=True)
		raise ConnectionError(f"Could not get channel info with id = {channel_id}")
	full_channel_info = res["channel"]
	if full_channel_info['is_channel']:
		# Join channel if created
		res = await client.conversations_join(channel=channel_id)
		if "ok" not in res.data or not res['ok']:
			print(f"Error message: {res}", file=err_stream, flush=True)
			raise ConnectionError(f"Could not join channel with id = {channel_id}")

		print(f'Channel {channel["name"]} created', flush=True,
		      file=info_stream)

		channel_list_path = archive_path / "channels.json"
		create_lock(channel_list_path)
		print(f"Attempting to acquire file lock for {channel_list_path}",
			  file=debug_stream, flush=True)
		async with file_locks[channel_list_path]:
			print(f"Acquired file lock for {channel_list_path}",
				  file=debug_stream, flush=True)
			async with aiofiles.open(channel_list_path, 'r+') as channel_list:
				old_channel_list_string = await channel_list.read()
				old_channel_list = json.loads(old_channel_list_string)
				old_channel_list.append(full_channel_info)
				await channel_list.seek(0)
				old_channel_list_string = json.dumps(old_channel_list, indent=4)
				await channel_list.write(old_channel_list_string)
				await channel_list.truncate()
		print(f"Released file lock for {channel_list_path}",
			  file=debug_stream, flush=True)


@slack_app.event("reaction_added")
async def add_reaction(payload):
	"""Adds reaction to the archived message"""
	reaction = payload['reaction']
	reacting_user = payload['user']

	if payload['item']['type'] == "message":
		# Get which message was reacted to
		parent_channel_id = payload['item']['channel']
		parent_ts = payload['item']['ts']

		log_path = await log_file_path(parent_channel_id, parent_ts)
		create_lock(log_path)
		print(f"Attempting to acquire file lock for {log_path}",
			  file=debug_stream, flush=True)
		async with file_locks[log_path]:
			print(f"Acquired file lock for {log_path}",
				  file=debug_stream, flush=True)
			async with aiofiles.open(log_path, "r") as log_file:
				message_list_string = await log_file.read()

			message_list = json.loads(message_list_string)
			message = next((m for m in message_list if m['ts'] == parent_ts), None)
			if message is not None:
				new_reaction_entry = {'name': reaction, 'count': 1, 'users': [reacting_user]}
				if "reactions" in message:
					reaction_entry = next((r for r in message['reactions'] if r['name'] == reaction), None)
					if reaction_entry is not None:
						reaction_entry['count'] += 1
						# Checking just in case something stupid happened
						if reacting_user not in reaction_entry['user']:
							reaction_entry['users'].append(reacting_user)
					else:
						message['reactions'].append(new_reaction_entry)
				else:
					message['reactions'] = [new_reaction_entry]
			else:
				print(f"Reaction {reaction} added to message (ts={parent_ts}, channel={parent_channel_id}), "
					  f"but message not found in log. Ignoring...",
					  file=err_stream, flush=True)

			message_list_string = json.dumps(message_list, indent=4)
			async with aiofiles.open(log_path, "w") as log_file:
				await log_file.write(message_list_string)
		print(f"Released file lock for {log_path}",
			  file=debug_stream, flush=True)


@slack_app.event("reaction_removed")
async def remove_reaction(payload):
	"""Removes reaction from an archived message"""
	reaction = payload['reaction']
	reacting_user = payload['user']

	if payload['item']['type'] == "message":
		# Get which message the reaction was removed from
		parent_channel_id = payload['item']['channel']
		parent_ts = payload['item']['ts']

		log_path = await log_file_path(parent_channel_id, parent_ts)
		create_lock(log_path)
		print(f"Attempting to acquire file lock for {log_path}",
			  file=debug_stream, flush=True)
		async with file_locks[log_path]:
			print(f"Acquired file lock for {log_path}",
				  file=debug_stream, flush=True)
			async with aiofiles.open(log_path, "r+") as log_file:
				message_list_string  = await log_file.read()

			message_list = json.loads(message_list_string)
			message = next((m for m in message_list if m['ts'] == parent_ts), None)
			if message is not None:
				if "reactions" in message:
					# Should not need to check, but just in case
					reaction_entry = next((r for r in message['reactions'] if r['name'] == reaction), None)
					if reaction_entry is not None:
						if reaction_entry['count'] > 1:
							reaction_entry['count'] -= 1
							reaction_entry['users'].remove(reacting_user)
						else:
							message['reactions'].remove(reaction_entry)
							if len(message['reactions']) == 0:
								message.pop('reactions')
					else:
						print(f"Reaction {reaction} removed from message (ts={parent_ts}, channel={parent_channel_id}), "
							  f"but not in message's reaction list. Ignoring...",
							  file=err_stream, flush=True)
				else:
					print(f"Reaction {reaction} removed from message (ts={parent_ts}, channel={parent_channel_id}), "
						  f"but message does not have reactions in log. Ignoring...",
						  file=err_stream, flush=True)
			else:
				print(f"Reaction {reaction} removed from message (ts={parent_ts}, channel={parent_channel_id}), "
					  f"but message not found. Ignoring...",
					  file=err_stream, flush=True)

			message_list_string = json.dumps(message_list, indent=4)
			async with aiofiles.open(log_path, "w") as log_file:
				await log_file.write(message_list_string)
		print(f"Released file lock for {log_path}",
			  file=debug_stream, flush=True)

async def add_to_archive(message):
	"""Archives a message"""

	channel_id = message['channel']
	ts = message['ts']

	channel_name = await channel_id_to_name(channel_id)
	directory_path = archive_path / channel_name
	directory_path.mkdir(exist_ok=True, parents=True)
	current_day_path = await log_file_path(channel_id, ts)

	# Reading an entire day's messages and rewriting is incredibly lazy and inefficient
	# However it will do for now
	# Alternatives are
	# A) manually remove last ] in JSON file with file.seek() and append last message object and add ] again
	# B) manage an internal Archive object which writes to disk periodically (say at the end of each day / every 100 message)
	# B seems to be preferable at the moment to me
	# This does not change with asyncio really, B is still preferable but the lazy method worked fine so far
	# and it will not be used a lot anyway from now on

	print(f"Attempting to acquire file lock for {current_day_path}",
			file=debug_stream, flush=True)

	# Lock file in case other threads try to write data to it at the same time

	create_lock(current_day_path)

	async with file_locks[current_day_path]:
		print(f"Acquired file lock for {current_day_path}",
				file=debug_stream, flush=True)

		# Create file if it does not exist
		if not current_day_path.is_file():
			async with aiofiles.open(current_day_path, "w") as current_day:
				current_day_string = json.dumps([message], indent=4)
				await current_day.write(current_day_string)

		else:
			async with aiofiles.open(current_day_path, 'r') as current_day:
				message_list_string = await current_day.read()

			message_list = json.loads(message_list_string)
			message_list.append(message)
			message_list_string = json.dumps(message_list, indent=4)

			async with aiofiles.open(current_day_path, "w") as current_day:
				await current_day.write(message_list_string)

	print(f"Released file lock for {current_day_path}",
			file=debug_stream, flush=True)
