import json
import base64
import os

# filters = [
#     {
#         "criteria": "sender",
#         "keywords": ["thenguyenltv@gmail.com"],
#         "folder": "Project"
#     },
#     {
#         "criteria": "subject",
#         "keywords": ["urgent", "ASAP"],
#         "folder": "Important"
#     },
#     {
#         "criteria": "content",
#         "keywords": ["report", "meeting"],
#         "folder": "Work"
#     },
#     {
#         "criteria": "spam",
#         "keywords": ["virus", "hack", "crack"],
#         "folder": "Spam"
#     }
# ]

class Email:
    def __init__(self, id, sender, receiver, subject, content_text, attachments, attachment_byte, read, tag, date):
        self.id = id
        self.sender = sender
        self.receiver = receiver
        self.subject = subject
        self.content_text = content_text
        self.attachments = attachments
        self.attachment_byte = attachment_byte
        self.read = read
        self.tag = tag
        self.date = date

    def __str__(self):
        return f'Email: {self.id} - {self.sender} - {self.receiver} - {self.subject} - {self.content_text} - {self.attachments} - {self.attachment_byte} - {self.read} - {self.tag} - {self.date}'
        
# Hàm chuyển đổi đối tượng Email thành từ điển
def email_to_dict(email):
    return {
        "id": email.id,
        "sender": email.sender,
        "receiver": email.receiver,
        "subject": email.subject,
        "content_text": email.content_text,
        "attachments": email.attachments,
        "attachment_byte": email.attachment_byte, 
        "read": email.read,
        "tag": email.tag,
        "date": email.date  
    }

# get informatin of email from email_data
def parse_email_data(id, email_data):
    date = email_data[email_data.find('Date:')+6:email_data.find('\r\n', email_data.find('Date:')+6)].strip()
    sender = email_data[email_data.find('From:')+6:email_data.find('\r\n', email_data.find('From:')+6)].strip()
    receiver = email_data[email_data.find('To:')+4:email_data.find('\r\n', email_data.find('To:')+4)].strip()
    subject = email_data[email_data.find('Subject:')+9:email_data.find('\r\n', email_data.find('Subject:')+9)].strip()
    # tìm multipart/mixed
    if email_data.find('multipart/mixed') != -1:
        have_attachment = get_attachment_name(email_data)
        attachment_byte = get_attachment_content(email_data)
    else:
        have_attachment = []
        attachment_byte = []
    read = False  
    
    content_text = read_data_mail(email_data)

    email = Email(id, sender, receiver, subject, content_text, have_attachment, attachment_byte, read, [], date)
    return email

# function to add to JSON
def add_data_json(new_data, filename='data.json'):
    with open(filename,'r+') as file:
        file_data = json.load(file)
        file_data.append(new_data)
        file.seek(0)
        json.dump(file_data, file, indent = 2)

def write_json(data, filename='data.json'):
    with open(filename,'w') as file:
        json.dump(data, file, indent = 2)

def read_json(filename):
    with open(filename,'r+') as file:
        file_data = json.load(file) 
    return file_data

def get_content(id, data):
    if data is None:
        return None
    for email in data:
        if email['id'] == id:
            return email['content_text']
    return None

def get_list_attachments(id, data):
    if data is None:
        return None
    for email in data:
        if email['id'] == id:
            return email['attachments']
    return None

def get_attachment_byte(id, index, data):
    if data is None:
        return None
    for email in data:
        if email['id'] == id:
            for i in range(len(email['attachments'])):
                if i == index:
                    return email['attachment_byte'][i]
    return None

def get_status(id, data):
    if data is None:
        return None
    for email in data:
        if email['id'] == id:
            return email['read']
    return None

def get_date(id, data):
    if data is None:
        return None
    for email in data:
        if email['id'] == id:
            return email['date']
    return None

def write_email_to_file(id, email, folder):
    # mailbox/folder/<id>.msg
    with open(f'mailbox/{folder}/{id}.msg', 'wb') as f:
        f.write(email.encode('utf-8'))

def get_list_ids(list_mail_json, tag):
    list_id = []
    for email in list_mail_json:
        if tag == 'All':
            list_id.append(email['id'])
        for t in email['tag']:
            if t == tag:
                list_id.append(email['id'])
                break
    return list_id

def show_list_mail(data, list_id):
    count = 0
    for email in data:
        if email['id'] in list_id or list_id == []:
            if email['read'] == True:
                status = 'Read'
            else:
                status = 'Unread'
            print(f'{count+1}. ({status}) From: {email["sender"]} - Subject: {email["subject"]} - Date: {email["date"]}')            
            count += 1
            
#*******************************************************
# Hàm read_data_mail() để đọc nội dung email
# Input: id, email_data
# id: id của email cần đọc
# email_data: <id>.msg
# Output: nội dung plain/text của email và câp nhật lại trạng thái email đã đọc
#*******************************************************
def read_data_mail(email_data):
    if 'Content-Type: multipart' in email_data:
        track_boundary = email_data.split('boundary="')[1].split('"')[0]
        parts = email_data.split(f'--{track_boundary}')
        text_index = parts[1].find('Content-Type: text/plain')
        double_line_break_index = parts[1].find('\r\n\r\n', text_index)
        plain_body = '\n'.join(parts[1][double_line_break_index + len('\r\n\r\n'):].split('\r\n\r\n'))
    else:
        text_index = email_data.find('Content-Type: text/plain')
        double_line_break_index = email_data.find('\r\n\r\n', text_index)
        end_of_email_index = email_data.find('\r\n.\r\n')
        plain_body = '\n'.join(email_data[double_line_break_index + len('\r\n\r\n'):end_of_email_index].split('\r\n\r\n'))

    return plain_body

#******************************************************
# Hàm save_attachment() để lưu file đính kèm
# Input: email_data, src_name, dst_path
# email_data: <id>.msg
# src_name: tên file đính kèm cần lưu. None nếu muốn lưu tất cả các file đính kèm
# dst_path: đường dẫn FOLDER lưu file đính kèm
#******************************************************
def save_attachment(file_data, file_name, dst_path):
    # check dst_path
    if dst_path is None or not os.path.exists(dst_path):
        # check mailbox/attachments
        if not os.path.exists('mailbox/attachments'):
            os.makedirs('mailbox/attachments')
        dst_path = 'mailbox/attachments'
    
    with open(os.path.join(dst_path, file_name), 'wb') as f:
        f.write(base64.b64decode(file_data))  

#******************************************************
# Hmà set_tag() để đánh dấu thư thuộc thư mục nào
# Input: st_email_data là object của class Email
# Output: True nếu thành công, False nếu thất bại
# Thành công: Tag của email được cập nhật
# Thất bại: st_email_data is None
#******************************************************
def set_tag(st_email_data, filters):
    # check email_data_json
    if st_email_data is None:
        return False
    
    # check spam email: have "virus", "hack", "ads" in body
    for filter in filters:
        if filter['criteria'] == 'spam':
            for keyword in filter['keywords']:
                if keyword in st_email_data.content_text:
                    st_email_data.tag = [filter['folder']]
                    return True
    
    # if email no spam
    # check sender, subject, body
    for filter in filters:
        if filter['criteria'] == 'from':
            for keyword in filter['keywords']:
                if keyword in st_email_data.sender:
                    st_email_data.tag.append(filter['folder'])
        elif filter['criteria'] == 'subject':
            for keyword in filter['keywords']:
                if keyword in st_email_data.subject:
                    st_email_data.tag.append(filter['folder'])
        elif filter['criteria'] == 'content':
            for keyword in filter['keywords']:
                if keyword in st_email_data.content_text:
                    st_email_data.tag.append(filter['folder'])
    
    # if email no spam, no sender, no subject, no body
    if st_email_data.tag == []:
        st_email_data.tag = ['Inbox']
    
    return True

# Hàm để cập nhật trạng thái đã đọc
def mark_as_read(email_id, data):
    # get length of data
    length = len(data)
    for i in range(length):
        if data[i]['id'] == email_id:
            data[i]['read'] = True
            break
            
def check_attachment(email_data):
    if email_data.find('Content-Type: multipart/mixed') != -1:
        return True
    else:
        return False
    
def get_attachment_name(email_data):
    track_boundary = email_data.split('boundary="')[1].split('"')[0]
    parts = email_data.split(f'--{track_boundary}')
    
    attachment_name = []
    for part in parts:
        attachment_index = part.find('Content-Disposition: attachment')
        if attachment_index == -1:
            continue

        attachment_name.append(part.split('filename="')[1].split('"')[0])
        
    return attachment_name

def get_attachment_content(email_data):
    track_boundary = email_data.split('boundary="')[1].split('"')[0]
    parts = email_data.split(f'--{track_boundary}')
    
    attachment_content = []
    for part in parts:
        attachment_index = part.find('Content-Disposition: attachment')
        if attachment_index == -1:
            continue
        attachment_content.append(part.split('\r\n\r\n')[1].split('\r\n--')[0])
        
    return attachment_content