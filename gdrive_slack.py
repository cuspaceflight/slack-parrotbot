import os
from threading import Thread

from shared import app

@app.event("file_shared")
def handle_file_shared(client, event, say, ack):
    file_data = client.files_info(file = event["file_id"]).data["file"]
    user_data = client.users_info(user = event["user_id"]).data["user"]

    dir_path = f"/var/opt/slack-parrotbot/files/{user_data['real_name']}" \
            .replace(" ","_")

    # Hardcoded slice here
    msg_data = say(f"File uploading to "
                   f"CUSF/slack-staging{dir_path[30:]}...").data
    Thread(target  = download_file,
           args    = (client, dir_path, file_data, msg_data)).start()
    ack()


def download_file(client, dir_path, file_data, msg_data):
    # wrap in sh -c in case the system shell is something stupid and non-posix
    os.system(f"""sh -c '

        mkdir -p "{dir_path}"
        cd "{dir_path}"

        wget --header="Authorization: Bearer {open("/opt/slack-parrotbot/secrets/SLACK_BOT_TOKEN").read()}"\
            {file_data["url_private_download"]}

        cd - >/dev/null

        # wait for the last operation to finish
        while pgrep rclone; do sleep 1; done
        rclone sync /var/opt/slack-parrotbot/files parrotbot-gdrive:slack-staging
    '""")
    # Hardcoded slice here
    client.chat_update(
            channel  = msg_data['channel'],
            ts       = msg_data['ts'],
            text     = f"File uploaded to "
                       f"CUSF/slack-staging{dir_path[30:]}")
