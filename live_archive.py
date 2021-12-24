import json
import sys
from datetime import datetime
from pathlib import Path
from threading import Lock, get_ident

from shared import app

archive_path = Path(open("ARCHIVE_PATH").read())
file_locks = {}

def timestamp_to_date_string(ts):
    """Converts a Slack timestamp into an ISO date (used in naming the daily JSON logs)"""
    if isinstance(ts, float):
        return datetime.fromtimestamp(ts).date().isoformat()
    elif isinstance(ts, str):
        return datetime.fromtimestamp(float(ts)).date().isoformat()
    else:
        raise TypeError("Expected either float or string timestamp")


def channel_id_to_name(channel_id):
    """Gets the current name of the channel with ID 'channel_id'"""
    res = app.client.conversations_info(channel=channel_id)
    if "ok" not in res.data or not res["ok"]:
        print(f"Error message:{res}", file=sys.stderr, flush=True)
        raise ConnectionError(f"conversations_info(channel={channel_id}) web request failed")
    channel_name = res["channel"]["name"]
    return channel_name


def log_file_path(channel_id, ts):
    """Returns a Path object pointing to the JSON logfile of a message with timestamp 'ts' in channel 'channel_id"""
    channel_name = channel_id_to_name(channel_id)
    return archive_path / channel_name / (timestamp_to_date_string(ts) + ".json")

@app.event("message")
def archive_message(message):
    """Runs on every message event and archives it if it's not hidden"""
    # print("Message received")

    # As message events are sent before 'channel_rename' events we're dealing with them here
    # Otherwise the program would still need to handle it to put it in the correct folder
    if "subtype" in message:
        if message['subtype'] == "channel_name":
            rename_channel(message['channel'], message['old_name'], message['name'])
        elif message['subtype'] ==  "message_changed":
            update_message(message['channel'], message['message']['ts'], message['message'])

    # Thread reply, need to edit parent message
    # Cannot filter on subtype as no subtype field is omitted due to bug in Slack API
    # See here: https://api.slack.com/events/message/message_replied
    if "thread_ts" in message:
        add_thread_reply(message['channel'], message['thread_ts'],
                         message['user'], message['ts'])

    if "hidden" in message:
        if not message['hidden']:
            add_to_archive(message)
            # This probably should not ever occur,
            # because if the message has a 'hidden' field it's probably always true
    else:
        add_to_archive(message)


def update_message(channel_id, ts, updated_message):
    """Replaces message with timestamp 'ts' in channel 'channel_id' with updated message"""
    with open(log_file_path(channel_id, ts), 'r+') as log_file:
        message_list = json.load(log_file)
        for message in message_list:
            # Update fields of message
            # This is done via iteration instead of a complete replacement
            # As updated_message might not contain reactions and other stuff
            if message['ts'] == ts:
                for (key, value) in updated_message.items():
                    message[key] = value

        log_file.seek(0)
        json.dump(message_list, log_file, indent=4)
        log_file.truncate()


def add_thread_reply(channel_id, thread_ts, reply_user, reply_ts):
    """Adds a thread reply object to an archived message"""
    with open(log_file_path(channel_id, thread_ts), 'r+') as log_file:
        message_list = json.load(log_file)
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
                   f"original thread with ts = {thread_ts}.", file=sys.stderr)
        # Go back to start and write
        log_file.seek(0)
        json.dump(message_list, log_file, indent=4)
        log_file.truncate()


def rename_channel(channel_id, old_name, new_name):
    """Renames channel folders and updates channel.json"""
    channel_list_path = archive_path / "channels.json"

    with open(channel_list_path, 'r+') as channel_list:
        old_channel_list = json.load(channel_list)
        channel = next((ch for ch in old_channel_list if ch['id'] == channel_id), None)
        if channel is not None:
            channel['name'] = new_name
        else:
            print(f"Renamed channel (id={channel_id}) from {old_name} to {new_name},"
                   f"but have not found channel with id on channels.json", file=sys.stderr)
        channel_list.seek(0)
        json.dump(old_channel_list, channel_list, indent=4)
        channel_list.truncate()

    print(f"Channel rename event from {old_name} to {new_name}")
    if old_name is not None:
        old_path = archive_path / old_name
        new_path = archive_path / new_name
        old_path.rename(new_path)
    else:
        print(f"Warning: Attempted to rename channel id {channel_id}, but it doesn't exist")


@app.event("channel_created")
def create_channel(client, payload):
    """On channel creation, if it's an actual channel joins then adds it into channels.json"""
    channel = payload['channel']
    channel_id = channel['id']

    # Get all detailed channel object
    res = client.conversations_info(channel=channel_id)
    if "ok" not in res.data or not res['ok']:
        print(f"Error message: {res}", file=sys.stderr, flush=True)
        raise ConnectionError(f"Could not get channel info with id = {channel_id}")
    full_channel_info = res["channel"]
    if full_channel_info['is_channel']:
        # Join channel if created
        res = client.conversations_join(channel=channel_id)
        if "ok" not in res.data or not res['ok']:
            print(f"Error message: {res}", file=sys.stderr, flush=True)
            raise ConnectionError(f"Could not join channel with id = {channel_id}")

        print(f'Channel {channel["name"]} created')

        channel_list_path = archive_path / "channels.json"
        with open(channel_list_path, 'r+') as channel_list:
            old_channel_list = json.load(channel_list)
            old_channel_list.append(full_channel_info)
            channel_list.seek(0)
            json.dump(old_channel_list, channel_list, indent=4)
            channel_list.truncate()


@app.event("reaction_added")
def add_reaction(payload):
    """Adds reaction to the archived message"""
    reaction = payload['reaction']
    reacting_user = payload['user']

    if payload['item']['type'] == "message":
        # Get which message was reacted to
        parent_channel_id = payload['item']['channel']
        parent_ts = payload['item']['ts']

        with open(log_file_path(parent_channel_id, parent_ts), "r+") as log_file:
            message_list = json.load(log_file)
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
                      f"but message not found in log. Ignoring...", file=sys.stderr)

            log_file.seek(0)
            json.dump(message_list, log_file, indent=4)
            log_file.truncate()


@app.event("reaction_removed")
def remove_reaction(payload):
    """Removes reaction from an archived message"""
    reaction = payload['reaction']
    reacting_user = payload['user']

    if payload['item']['type'] == "message":
        # Get which message the reaction was removed from
        parent_channel_id = payload['item']['channel']
        parent_ts = payload['item']['ts']

        with open(log_file_path(parent_channel_id, parent_ts), "r+") as log_file:
            message_list = json.load(log_file)
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
                              f"but not in message's reaction list. Ignoring...", file=sys.stderr)
                else:
                    print(f"Reaction {reaction} removed from message (ts={parent_ts}, channel={parent_channel_id}), "
                          f"but message does not have reactions in log. Ignoring...", file=sys.stderr)
            else:
                print(f"Reaction {reaction} removed from message (ts={parent_ts}, channel={parent_channel_id}), "
                      f"but message not found. Ignoring...", file=sys.stderr)

            log_file.seek(0)
            json.dump(message_list, log_file, indent=4)
            log_file.truncate()


def add_to_archive(message):
    """Archives a message"""

    channel_id = message['channel']
    ts = message['ts']

    channel_name = channel_id_to_name(channel_id)
    directory_path = archive_path / channel_name
    directory_path.mkdir(exist_ok=True, parents=True)
    current_day_path = log_file_path(channel_id, ts)

    # Reading an entire day's messages and rewriting is incredibly lazy and inefficient
    # However it will do for now
    # Alternatives are
    # A) manually remove last ] in JSON file with file.seek() and append last message object and add ] again
    # B) manage an internal Archive object which writes to disk periodically (say at the end of each day / every 100 message)
    # B seems to be preferable at the moment to me

    print(f"Attempting to acquire file lock for {current_day_path}, thread id = {get_ident()}")

    # Lock file in case other threads try to write data to it at the same time
    if current_day_path in file_locks:
        file_locks[current_day_path].acquire()
    else:
        file_locks[current_day_path] = Lock()
        file_locks[current_day_path].acquire()

    print(f"Acquired file lock for {current_day_path}, thread id = {get_ident()}")

    # Create file if it does not exist
    if not current_day_path.is_file():
        with open(current_day_path, "w") as current_day:
            json.dump([message], current_day, indent=4)

    else:
        with open(current_day_path, 'r+') as current_day:
            message_list = json.load(current_day)
            message_list.append(message)

            # Go back to start
            current_day.seek(0)

            json.dump(message_list, current_day, indent=4)
            current_day.truncate()

    # Release file lock
    file_locks[current_day_path].release()

    print(f"Released file lock for {current_day_path}, thread id = {get_ident()}")
