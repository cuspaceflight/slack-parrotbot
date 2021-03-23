import os
from time import sleep
from threading import Thread

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from fontmap import parrots_fontmap, font_henry
from display import FrameBuffer, TextBuffer

# Install the Slack app and get xoxb- token in advance
app = App(token=open("SLACK_BOT_TOKEN").read())
tb = TextBuffer(parrots_fontmap, 40)
tb_cache = ""

fg = ':partyparrot:'
bg = ':fireparrot:'

@app.command("/parrot")
def parrot_command(client, ack, body, say):
    try:
        user_message = body['text']
        
        # recreate the textbuffer on a new message
        # so only the latest message will update
        tb = TextBuffer(parrots_fontmap, 40)

        say(f"Message from <@{body['user_id']}>:")
        data = say(".").data # will be overriden
        Thread(target = refresh, kwargs = dict(
                client   = client,
                channel  = data['channel'],
                ts       = data['ts']),
            name="update_thread").start()
        ack()
    except Exception as e:
        response = str(e)
        ack(response)

@app.command("/parrot-update")
def update(client, ack, body, say):
    try:
        tb.update_text(body['text'])
        ack()
    except Exception as e:
        response = str(e)
        ack(response)


def refresh(client, channel, ts):
    while True:
        sleep(0.2)
        tb_str = str(tb)
        if tb_str != tb_cache:
            tb_cache = tb_str
            client.chat_update(channel=channel, ts=ts,
                               text=tb_str.replace('x', fg).replace('.', bg))


if __name__ == "__main__":
    pmaker = ParrotMaker(parrot_fg=":fireparrot:", parrot_bg=":hunt:")
    SocketModeHandler(app, open("SLACK_APP_TOKEN").read()).start()

