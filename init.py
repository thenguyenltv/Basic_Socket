import os
import json

# mail box in client
#===============================================================================
# mailbox
#   list_mails.json
#     [
#      {
#        "id": 1,
#        "sender": "thenguyenltv@gmail",
#        "receiver": "",
#        "subject": "test",
#        "body": "test",
#        "attachments": [],
#        "status": "unread",
#        "tag": ["inbox", "important"]
#      }
#    ]
#
#   <id1>.msg
#   <id2>.msg
#   ...
#===============================================================================

# khởi tạo các thư mục cần thiết
def init():
    # tạo thư mục chứa các file tin nhắn
    if not os.path.exists('mailbox'):
        os.makedirs('mailbox')
    # tạo file list_mails.json
    if not os.path.exists('mailbox/list_mails.json'):
        with open('mailbox/list_mails.json', 'w') as f:
            json.dump([], f, indent = 2)
    # tạo các folder chứa thư
    if not os.path.exists('mailbox/Inbox'):
        os.makedirs('mailbox/Inbox')
    if not os.path.exists('mailbox/Important'):
        os.makedirs('mailbox/Important')
    if not os.path.exists('mailbox/Project'):
        os.makedirs('mailbox/Project')
    if not os.path.exists('mailbox/Work'):
        os.makedirs('mailbox/Work')
    if not os.path.exists('mailbox/Spam'):
        os.makedirs('mailbox/Spam')