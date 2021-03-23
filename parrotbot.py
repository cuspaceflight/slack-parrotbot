import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from parrot_maker import ParrotMaker

# Install the Slack app and get xoxb- token in advance
app = App(token=open("SLACK_BOT_TOKEN").read())

@app.command("/parrot")
def parrot_command(ack, body, say):
    try:
        response = pmaker.to_parrots(body['text'])
        say(response)
        ack()
    except Exception as e:
        response = str(e)
        ack(response)

if __name__ == "__main__":
    pmaker = ParrotMaker()
    SocketModeHandler(app, open("SLACK_APP_TOKEN").read()).start()
