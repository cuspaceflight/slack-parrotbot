from slack_bolt.adapter.socket_mode import SocketModeHandler

from shared import app
import parrotmaker_slack
import pong_slack
import gdrive_slack

if __name__ == "__main__":
    SocketModeHandler(app, open("SLACK_APP_TOKEN").read()).start()
