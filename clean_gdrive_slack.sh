#!/bin/sh

# Clean local files {{{
PREV_MD5=""
PREV_PATH=""
CURRENT_MD5=""
CURRENT_PATH=""

# get hashes, and sort by hash
find /var/opt/async-parrotbot/files -type f | xargs md5sum | sort \
		| while read current_line
do
    CURRENT_MD5=$(echo "$current_line" | awk '{print $1}')
    CURRENT_PATH=$(echo "$current_line" | awk '{print $2}')
    if [ "$CURRENT_MD5" = "$PREV_MD5" ] ; then
        echo "DELETE: $CURRENT_PATH"
		sudo rm $CURRENT_PATH
    else
        PREV_MD5=$CURRENT_MD5
        PREV_PATH=$CURRENT_PATH
    fi
done
# }}}
# Clean gdrive {{{
PREV_MD5=""
PREV_PATH=""
CURRENT_MD5=""
CURRENT_PATH=""

# get hashes, remove empty (gdocs etc) and sort by hash
rclone md5sum parrotbot-gdrive:slack-staging \
		| grep '[^0-9a-f]' | sort - \
| while read current_line ; do
    CURRENT_MD5=$(echo "$current_line" | cut -c -32)
    CURRENT_PATH=$(echo "$current_line" | cut -c 35-)
    if [ "$CURRENT_MD5" = "$PREV_MD5" ] ; then
        echo "DELETE: parrotbot-gdrive:slack-staging/$CURRENT_PATH"
        rclone -v delete "parrotbot-gdrive:slack-staging/$CURRENT_PATH"
    else
        PREV_MD5=$CURRENT_MD5
        PREV_PATH=$CURRENT_PATH
    fi
done
# }}}
# Resync
sudo rclone sync /var/opt/async-parrotbot/files parrotbot-gdrive:slack-staging

