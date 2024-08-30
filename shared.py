import asyncio
import sys
import argparse

import yaml
from slack_bolt.app.async_app import AsyncApp

parser = argparse.ArgumentParser()
parser.add_argument('--journald', action='store_true',
                    help='Use systemd journal outputs instead of stdout and stderr')
parser.add_argument('-c', '--config',
                    help='Specify a path for a config.yaml',
                    default='/etc/slack-parrotbot/config.yaml')
args = parser.parse_args()

async def async_check_output(cmd, **kwargs):
	process = await asyncio.create_subprocess_shell(
		cmd,
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.PIPE,
		**kwargs
	)
	stdout, stderr = await process.communicate()
	if process.returncode == 0:
		return stdout
	else:
		print(f"Error occured while executing command "
			  f"`{cmd}` during /parrotcheckhealth:", file=err_stream)
		print(stderr, file=err_stream)

if args.journald:
	from systemd import journal
	debug_stream  = journal.stream('slack-parrotbot', priority=7)
	info_stream   = journal.stream('slack-parrotbot', priority=6)
	warn_stream   = journal.stream('slack-parrotbot', priority=4)
	err_stream    = journal.stream('slack-parrotbot', priority=3)

	sys.stdout = info_stream
	sys.stderr = err_stream

else:
	debug_stream  = sys.stdout
	info_stream   = sys.stdout
	warn_stream   = sys.stderr
	err_stream    = sys.stderr

if args.config is not None:
	config_file = args.config
	if args.config == '/etc/slack-parrotbot/config.yaml':
		print("No config file specified, defaulting to /etc/slack-parrotbot/config.yaml...",
		      file = warn_stream)
else:
	print("argparse is broken, I am confused, abort.", file=err_stream)
	raise SystemExit(1)


config = yaml.load(open(config_file), Loader=yaml.loader.FullLoader)

slack_app = AsyncApp(token = config['slack_bot_token'])
