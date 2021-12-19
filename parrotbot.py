from datetime import datetime

from slack_bolt.adapter.socket_mode import SocketModeHandler

from shared import app
import parrotmaker_slack
import pong_slack
import gdrive_slack

print("Starting parrotbot...", flush=True)

@app.command("/parrotcheckhealth")
def parrotcheckhealth(client, ack, body, say):
    MAX_CHARS=3600

    stderr = open("/var/opt/slack-parrotbot/stderr").read().replace('files.slack.com', '********')
    stdout = open("/var/opt/slack-parrotbot/stdout").read().replace('files.slack.com', '********')

    stderr_lines = stderr.split('\n')
    stdout_lines = stdout.split('\n')

    stderr_messages = []
    stdout_messages = []

    # incredibly jank but whatever
    while len(stderr_lines) > 0:
        msg = ""
        while len(stderr_lines) > 0 and len(msg) + len(stderr_lines[0]) <= MAX_CHARS:
            msg += stderr_lines.pop(0) + '\n'
        stderr_messages.append(msg)

    while len(stdout_lines) > 0:
        msg = ""
        while len(stdout_lines) > 0 and len(msg) + len(stdout_lines[0]) <= MAX_CHARS:
            msg += stdout_lines.pop(0) + '\n'
        stdout_messages.append(msg)

    if "quiet" in body['text']:
        ack("I'm running! Here is my latest stderr:" \
            "\n```\n" + stderr_messages[-1] + '```'
            "\nAnd stdout:" \
            "\n```\n" + stdout_messages[-1] + '```')
    else:
        say("I'm running! Here is my terminal output:" \
            "\nstdout:")
        for msg in stdout_messages:
            say("\n```\n" + msg + '```', unfurl_media = False, unfurl_links=False)
        say("\nstderr:")
        for msg in stderr_messages:
            say("\n```\n" + msg + '```', unfurl_media = False, unfurl_links=False)
        ack()

####### TODO: THIS ISN'T WORKING
@app.event("channel_created")
def handle_file_shared(client, event, ack):
    print('hello there', flush=True)
    if not chan['is_im']:
        chan=event['channel']
        app.client.conversations_join(channel=chan['id'])
        print(f"{datetime.now().isoformat()}: Joined {chan['name']}",
                flush=True)
    ack()


if __name__ == "__main__":
    # why no do while python??
    cursor = None
    while cursor != '':
        conversations = app.client.conversations_list(cursor=cursor)
        for chan in conversations['channels']:
            if not (chan['is_im'] or chan['is_member'] or chan['is_archived']):
                app.client.conversations_join(channel=chan['id'])
                print(f"{datetime.now().isoformat()}: Joined {chan['name']}",
                        flush=True)
        cursor = conversations['response_metadata']['next_cursor']

    SocketModeHandler(app, open("/opt/slack-parrotbot/secrets/SLACK_APP_TOKEN").read()).start()

