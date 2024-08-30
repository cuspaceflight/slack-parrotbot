from util.parrotmaker import ParrotMaker
from shared import slack_app

pmaker = ParrotMaker(
	max_width  = 57,
)

@slack_app.command("/parrot")
async def parrot(client, ack, body, say):
	try:
		await ack()
		await say(f"<@{body['user_id']}> has summoned the parrot gods, "
			f"and in response they say")
		# Ideally the fg and bg would be taken from the command arguments
		# but Slack does not do argument parsing, and I am lazy to implement one
		await say(pmaker.to_parrots(body['text'], fg=":fireparrot:", bg=":hunt:"))
	except Exception as e:
		response = str(e)
		await ack(response)
