from slack_bolt.adapter.socket_mode import SocketModeHandler

from shared import app
import parrotmaker_slack
import pong_slack
import gdrive_slack

@app.command("/parrotcheckhealth")
def parrotcheckhealth(client, ack, body, say):

    t = "I'm running! Here is my terminal output: \n" \
        "stdout\n```\n" \
      + open("/var/opt/slack-parrotbot/stdout").read() \
      + "```\nstderr\n```\n" \
      + open("/var/opt/slack-parrotbot/stderr").read() \
      + "```"

    if "quiet" in body['text']:
        ack(t)
    else:
        say(t)
        ack()

if __name__ == "__main__":
    for chan in app.client.conversations_list()['channels']:
        if not (chan['is_im'] or chan['is_member'] or chan['is_archived']):
            app.client.conversations_join(channel=chan['id'])

    SocketModeHandler(app, open("/opt/slack-parrotbot/secrets/SLACK_APP_TOKEN").read()).start()
    SocketModeHandler(app, open("/opt/slack-parrotbot/secrets/SLACK_APP_TOKEN").read()).start()
