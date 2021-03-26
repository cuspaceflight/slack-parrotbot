import os
from time import sleep
from threading import Thread

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from parrotmaker import ParrotMaker
from pong import Pong

# Install the Slack app and get xoxb- token in advance
app = App(token=open("SLACK_BOT_TOKEN").read())

# Define our fore- and background emojis
fg = ':partyparrot:'
bg = ':fireparrot:'

# Create parrotmaker and pong
pmaker = ParrotMaker()
p = Pong()

slack_client = None
slack_channel = None
slack_ts = None


def refresh():
    global p, slack_client, slack_channel, slack_ts
    cache = ""
    while True:
        screen = p.screen
        if screen != cache:
            cache = screen
            slack_client.chat_update(
                channel=slack_channel,
                ts=slack_ts,
                text=screen)
        sleep(0.2)


def tick_handler():
    global p
    while True:
        sleep(0.6)
        p.tick()


thd_refresh = Thread(target=refresh)
thd_tick = Thread(target=tick_handler)


@app.command("/parrot")
def parrot(client, ack, body, say):
    global p, slack_client, slack_channel, slack_ts
    try:
        say(f"<@{body['user_id']}> has summoned the parrot gods, "
            f"and in response they say")
        say(pmaker.to_parrots(body['text']))
        ack()
    except Exception as e:
        response = str(e)
        ack(response)

@app.command("/pong")
def pong(client, ack, body, say):
    global p, slack_client, slack_channel, slack_ts
    try:
        say("pong")
        data = say("loading...").data

        slack_client = client
        slack_channel = data['channel']
        slack_ts = data['ts']

        p.callback = say

        if not thd_refresh.is_alive():
            thd_refresh.start()
            thd_tick.start()

        ack()
    except Exception as e:
        response = str(e)
        ack(response)


@app.command("/register")
def register(client, ack, body, say):
    global p
    try:
        if not p.start and len(p.players) < 2:
            user = body['user_id']
            if user not in p.players:
                p.players.append(user)
                say(f"<@{body['user_name']}> is now player {len(p.players)}")
        ack()
    except Exception as e:
        response = str(e)
        ack(response)


@app.command("/start")
def start(client, ack, body, say):
    global p
    try:
        if len(p.players) < 2:
            say("not enough players to start")
        else:
            p.reset_ball_pos()
            p.start = True
            p.vel = [1, 0]
        ack()
    except Exception as e:
        response = str(e)
        ack(response)

@app.command("/u")
def up(client, ack, body, say):
    global p
    try:
        user = body['user_id']
        if p.start and user in p.players:
            if p.players.index(user):
                if p.p2 > 1:
                    p.p2 -= 1
            else:
                if p.p1 > 1:
                    p.p1 -= 1
        ack()
    except Exception as e:
        response = str(e)
        ack(response)


@app.command("/d")
def down(client, ack, body, say):
    global p
    try:
        user = body['user_id']
        if p.start and user in p.players:
            if p.players.index(user):
                if p.p2 < p.h - p.paddlesize:
                    p.p2 += 1
            else:
                if p.p1 < p.h - p.paddlesize:
                    p.p1 += 1
        ack()
    except Exception as e:
        response = str(e)
        ack(response)



if __name__ == "__main__":
    SocketModeHandler(app, open("SLACK_APP_TOKEN").read()).start()

