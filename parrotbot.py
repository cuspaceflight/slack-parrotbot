import os
from time import sleep
from threading import Thread

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from parrot_maker import ParrotMaker

# Install the Slack app and get xoxb- token in advance
app = App(token=open("SLACK_BOT_TOKEN").read())

@app.command("/parrot")
def parrot_command(client, ack, body, say):
    try:
        user_message = body['text']

        say(f"Message from <@{body['user_id']}>:")
        data = say(".").data # will be overriden
        Thread(target = update, kwargs = dict(
                client   = client,
                channel  = data['channel'],
                ts       = data['ts']),
            name="update_thread").start()
        ack()
    except Exception as e:
        response = str(e)
        ack(response)

def update(client, channel, ts):
    i = 0
    while True:
        i = (i + 1) % 26
        c = chr(i + ord('A'))
        sleep(0.2)
        client.chat_update(channel=channel, ts=ts, text=pmaker.to_parrots(c))


if __name__ == "__main__":
    pmaker = ParrotMaker(parrot_fg=":fireparrot:", parrot_bg=":hunt:")
    SocketModeHandler(app, open("SLACK_APP_TOKEN").read()).start()
