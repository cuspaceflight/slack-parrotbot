import os
from threading import Thread

from shared import *

@app.event("file_shared")
def handle_file_shared(client, event, say, ack):
	file_data = client.files_info(file = event["file_id"]).data["file"]
	user_data = client.users_info(user = event["user_id"]).data["user"]
	print("File shared by ", user_data['real_name'], flush=True, file=info_stream)

	normalised_name = user_data['real_name'].replace(" ", "_")
	dir_path = f"{config['gdrive']['local_path']}/{normalised_name}"
	dir_nice_name = f"{config['gdrive']['remote_nice_name']}/{normalised_name}"

	msg_data = say(f"File uploading to {dir_nice_name}...").data
	Thread(target  = download_file,
	       args    = (client, dir_path, dir_nice_name, file_data, msg_data)).start()
	ack()

def download_file(client, dir_path, dir_nice_name, file_data, msg_data):
	# wrap in sh -c in case the system shell is something stupid and non-posix
	os.system(f"""sh -c '

		mkdir -p "{dir_path}"
		cd "{dir_path}"

		wget --header="Authorization: Bearer {config['slack_bot_token']}"\
			{file_data["url_private_download"]} >> /var/log/slack-parrotbot/wget-log

		cd - >/dev/null

		# wait for the last operation to finish
		while pgrep rclone; do sleep 1; done
		rclone sync {config['gdrive']['local_path']} {config['gdrive']['remote_path']} \
				>> /var/log/slack-parrotbot/rclone-log
	'""")
	client.chat_update(
			channel  = msg_data['channel'],
			ts       = msg_data['ts'],
			text     = f"File uploaded to {dir_nice_name}"
		)
