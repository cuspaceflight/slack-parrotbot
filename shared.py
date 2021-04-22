from slack_bolt import App
app = App(token = open("/opt/slack-parrotbot/secrets/SLACK_BOT_TOKEN").read())
