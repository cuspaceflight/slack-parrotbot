from pathlib import Path
import aiohttp

from shared import *

@slack_app.event("file_shared")
async def handle_file_shared(client, event, say, ack):
	await ack()
	file_data = (await client.files_info(file = event["file_id"])).data["file"]
	user_data = (await client.users_info(user = event["user_id"])).data["user"]
	print("File shared by ", user_data['real_name'], flush=True, file=info_stream)

	normalised_name = user_data['real_name'].replace(" ", "_")
	dir_path = Path(f"{config['gdrive']['local_path']}") / f"{normalised_name}"
	dir_nice_name = f"{config['gdrive']['remote_nice_name']}/{normalised_name}"

	msg_data = (await say(f"File uploading to {dir_nice_name}...")).data

	await download_file(dir_path, file_data)
	rclone_log = Path(config['gdrive']['rclone_log_path'])
	rclone_log.parent.mkdir(exist_ok=True, parents=True)
	with open(rclone_log, 'a+') as rclone_log_file:
		process = await asyncio.create_subprocess_exec('rclone',
													   'sync', config['gdrive']['local_path'], config['gdrive']['remote_path'],
													   stdout=rclone_log_file, stderr=rclone_log_file)
	await process.wait()
	if process.returncode != 0:
		print(f"Error code {process.returncode} occured during uploading to the remote via rclone. "
			  f"See {str(rclone_log)} for details.", file=err_stream)

	await client.chat_update(
		channel  = msg_data['channel'],
		ts       = msg_data['ts'],
		text     = f"File uploaded to {dir_nice_name}" if process.returncode == 0 else f"File *failed* to upload to {dir_nice_name}"
	)


async def download_file(dir_path, file_data):
	header = {
		"Authorization": f"Bearer {config['slack_bot_token']}",
	}
	dir_path.mkdir(exist_ok=True, parents=True)
	async with aiohttp.ClientSession(headers=header) as session:
		async with session.get(file_data['url_private_download']) as resp:
			if resp.status == 200:
				with open(dir_path / file_data['name'], 'wb') as f:
					async for chunk in resp.content.iter_chunked(4096):
						f.write(chunk)

			else:
				print(f"Received non-200 response when downloading file "
					  f"{file_data['url_private_download']}", file=err_stream)
