import os
from threading import Thread

from shared import app

@app.event("file_shared")
def handle_file_shared(client, event, say, ack):
    file_data = client.files_info(file = event["file_id"]).data["file"]
    user_data = client.users_info(user = event["user_id"]).data["user"]

    dir_path = f"gdrive/.shared/CUSF/slack-staging/{user_data['real_name']}" \
            .replace(" ","_")

    # wrap in sh -c in case the system shell is something stupid and non-posix
    msg_data = say(f"File uploading to "
                   f"{dir_path[15:]}...").data
    Thread(target  = download_file,
           args    = (client, dir_path, file_data, msg_data)).start()
    ack()


def download_file(client, dir_path, file_data, msg_data):
    os.system(f"""sh -c '

        mkdir -p "{dir_path}"
        cd "{dir_path}"

        wget --header="Authorization: Bearer {open("SLACK_BOT_TOKEN").read()}"\
            {file_data["url_private_download"]}

        cd - >/dev/null
    '""")
    client.chat_update(
            channel  = msg_data['channel'],
            ts       = msg_data['ts'],
            text     = f"File uploaded to "
                       f"{dir_path[15:]}")
