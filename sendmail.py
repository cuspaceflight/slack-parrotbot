from shared import app
from sys import stdin
import email
from email.policy import default as default_policy
from base64 import b64decode

channel_id = 'C02M8RJ4PGS'

mail_obj = email.message_from_file(stdin, policy=default_policy)

body = mail_obj.get_body(preferencelist=('plain','html'))

message=f"""
Received email on {mail_obj['Date']}:
From: {mail_obj['From']}
Subject: {mail_obj['Subject']}

{body.get_payload()}
"""
app.client.chat_postMessage(channel=channel_id, text=message)

for p in mail_obj.walk():
	if p == body or p.is_multipart(): continue
	name = p.get_filename()
	if name == None: name = "failed_to_get_name"
	if p['Content-transfer-encoding'] == 'base64':
		data = b64decode(p.get_payload())
	else:
		data = p.get_payload()
	app.client.files_upload(channels=channel_id,
							content=data,
							filename=name)
