from slack_bolt import App

from util.parrotmaker import ParrotMaker
from shared import app

pmaker = ParrotMaker(
    fg         = ':fireparrot:',
    bg         = ':hunt:',
    max_width  = 57,
)

@app.command("/parrot")
def parrot(client, ack, body, say):
    try:
        say(f"<@{body['user_id']}> has summoned the parrot gods, "
            f"and in response they say")
        say(pmaker.to_parrots(body['text']))
        ack()
    except Exception as e:
        response = str(e)
        ack(response)
