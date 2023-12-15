import datetime
import socket
import base64
import os
import random
import string
import threading 
import schedule 
import time


from init import *
from utils import *

config = read_json('config.json')

SMTP_SERVER = config['SMTP_SERVER']
SMTP_PORT = config['SMTP_PORT']

POP3_SERVER = config['POP3_SERVER']
POP3_PORT = config['POP3_PORT']

SENDER_EMAIL = config['SENDER_EMAIL']
USERNAME = config['USERNAME']
PASSWORD = config['PASSWORD']

filter = config['filters']

def send_email(subject, body, to_list,cc_list=None, bcc_list=None, attachments=None):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SMTP_SERVER, SMTP_PORT))
        data = s.recv(1024).decode('utf-8')
        s.sendall(b'EHLO example.com\r\n')
        data = s.recv(1024).decode('utf-8')
        s.sendall(f'MAIL FROM: <{SENDER_EMAIL}>\r\n'.encode())
        data = s.recv(1024).decode('utf-8')
        
        # lọc bỏ các email nhận trùng lặp trong cc và to
        to_list = to_list + cc_list if cc_list else to_list
        to_list = list(set(to_list))
        if to_list:
            for recipient in to_list:
                s.sendall(f'RCPT TO: <{recipient}>\r\n'.encode())
                data = s.recv(1024).decode('utf-8')

        if bcc_list:
            for bcc_email in bcc_list:
                s.sendall(f'RCPT TO: <{bcc_email}>\r\n'.encode())
                data = s.recv(1024).decode('utf-8')

        s.sendall(b'DATA\r\n')
        data = s.recv(1024).decode('utf-8')

        # Xây dựng phần header của email
        # Nếu có attachments thì thêm dòng Content-Type: multipart/mixed; boundary=boundary vào đầu email:
        boundary = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(30))
        email_data = ''
        if attachments:
            email_data += f'Content-Type: multipart/mixed; boundary="{boundary}"\r\n'
        email_data += f'Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\r\n'
        email_data += f'From: <{SENDER_EMAIL}>\r\n'
        email_data += f'To: {", ".join(to_list)}\r\n'
        
        if cc_list:
            email_data += f'Cc: {", ".join(cc_list)}\r\n'

        email_data += f'Subject: {subject}\r\n'

        # Xử lý phần content:
        if attachments:
            email_data += f'--{boundary}\r\n'
            email_data += f'Content-Type: text/plain; charset="utf-8"\r\n'
            email_data += f'Content-Transfer-Encoding: 7bit\r\n\r\n{body}\r\n'
        else:
            email_data += f'Content-Type: text/plain; charset="utf-8"\r\n'
            email_data += f'Content-Transfer-Encoding: 7bit\r\n\r\n{body}\r\n'

        # Tạo biến lưu độ dài attachment
        attachment_length = 0

        # Thêm các file đính kèm vào email
        if attachments:
            for attachment_path in attachments:
                filename = os.path.basename(attachment_path)
                with open(attachment_path, 'rb') as attachment_file:
                    attachment_content = base64.b64encode(attachment_file.read()).decode('utf-8')
                    attachment_length += len(attachment_content)
                email_data += f'\r\n--{boundary}\r\n'
                email_data += f'Content-Type: application/octet-stream; name="{filename}"\r\n'
                email_data += f'Content-Disposition: attachment; filename="{filename}"\r\n'
                # xử lý phần content
                email_data += 'Content-Transfer-Encoding: base64\r\n\r\n'
                for i in range(0, len(attachment_content), 72):
                    frame_data = attachment_content[i:i+72]
                    email_data += frame_data + '\r\n'
                email_data += '\r\n'

        # Nếu attachment_length > 1 MB thì thông báo dung lượng file vượt quá mức cho phép (1MB) và đóng kết nối
        if attachment_length > 1024 * 1024:
            print('attachment too large')
            s.sendall(b'QUIT\r\n')
            data = s.recv(1024).decode('utf-8')
            print(data) # 221 Closeing connecting
            return

        if attachments:
            email_data += f'--{boundary}--\r\n.\r\n'
        else:
            email_data += '\r\n.\r\n'

        s.sendall(email_data.encode())
        data = s.recv(1024).decode('utf-8')

        s.sendall(b'QUIT\r\n')
        data = s.recv(1024).decode('utf-8')

#*******************************************************
# Hàm receive_email() để nhận email
# Input: ids[]
# ids: id của email cần nhận
# Output: toàn bộ email_data [] lấy từ hàm RETR
#*******************************************************
def load_email(sock, id):
    if id is None:
        return None
    
    sock.sendall(f'RETR {id}\r\n'.encode())
    email_data = sock.recv(1024).decode()
    # read to end of email (end with .)
    while not email_data.endswith('\r\n.\r\n'):
        email_data += sock.recv(1024).decode()
                
    return email_data

#*******************************************************
# Hàm read_email() để đọc email từ file trong folder mailbox
# Input: id
# Output: nội dung plain/text của email và câp nhật lại trạng thái email đã đọc
#*******************************************************
def read_email(id):
    if id is None:
        return None
    
    with open(f'mailbox/{id}.msg', 'rb') as f:
        email_data = f.read()
    
    # decode email_data
    email_data = email_data.decode('utf-8')
    return email_data

#*******************************************************
# Hàm fetch_email() để tải email từ server
# Input: None
# Output: list_email []
#*******************************************************
def fetch_email():
    # đọc list_mailbox.json
    list_mail = read_json('mailbox/list_mails.json')
    
    #connect to POP3 server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((POP3_SERVER, POP3_PORT))
        
        data = s.recv(1024).decode()
        s.sendall(b'CAPA\r\n')
        data = s.recv(1024).decode()
        s.sendall(f'USER {USERNAME}\r\n'.encode())
        data = s.recv(1024).decode()
        s.sendall(f'PASS {PASSWORD}\r\n'.encode())
        data = s.recv(1024).decode()
        s.sendall(b'STAT\r\n')
        data = s.recv(1024).decode()
        s.sendall(b'LIST\r\n')
        data = s.recv(1024).decode()
        
        # get list email id from server
        list_email_server = []
        for line in data.split('\r\n')[1:-2]:
            list_email_server.append(int(line.split(' ')[0]))
        
        # list_ids from list_mailbox.json
        list_ids = get_list_ids(list_mail, 'All')
        #list_ids = []
        
        ids_to_fetch = []
        # cmp list_ids with list_email_server
        for email_id in list_email_server:
            if email_id not in list_ids:
                ids_to_fetch.append(email_id) 
        
        # update list_mailbox.json
        if ids_to_fetch == []:
            pass
        else:
            list_mail_in_msg = []
            list_mail_in_json = []
            for id in ids_to_fetch:
                email_data = load_email(s, id)
                st_email_data = parse_email_data(id, email_data)
                set_tag(st_email_data, filter)
                
                list_mail_in_msg += email_data
                list_mail_in_json.append(st_email_data)
                
                # write email to file
                for tag in st_email_data.tag:
                    write_email_to_file(id, email_data, tag)
                
            # write email to list_mailbox.json
            for email in list_mail_in_json:
                emails_dict = email_to_dict(email)
                add_data_json(emails_dict, 'mailbox/list_mails.json')
        
        s.sendall(b'QUIT\r\n')
        data = s.recv(1024).decode()
      

def input_list(input_string):
    email_addresses = [email.strip() for email in input_string.split(',')]
    return email_addresses

def check_id(id, list_ids):
    if not id.isdigit() or int(id) > len(list_ids) or int(id) < 1:
        return False
    return True

def auto_install_mail():
    while not stop_event.is_set():
        # Gọi hàm của bạn
        fetch_email()
        
        # Đợi 10 giây trước khi chạy lại hàm
        for i in range(50):
            if stop_event.is_set():
                break
            time.sleep(0.2)

def menu():
    while True:
        #os.system('cls')
        print('1. Send email')
        print('2. View mail')
        print('3. Exit')
        choice = input('Your choice: ')
        match choice:
            case '1': # send mail
                print('Case 1')
                
                # code to get input from user here
                # to_list is the list of email address
                input_string = input("To (Separate by comma): ")
                to_list = input_list(input_string)    
                input_string = input("CC (Separate by comma): ")
                cc_list = input_list(input_string)    
                input_string = input("BCC (Separate by comma): ")
                bcc_list = input_list(input_string)                
                subject = input('Subject: ')
                if subject == '':
                    subject = 'No subject'
                # content is multi-line
                print('Content: ')
                content_text = ''
                while True:
                    line = input()
                    if line == '':
                        break
                    content_text += line + '\n'
                choice = input('Do you want to attach file? (y/n)')
                if choice == 'y' or choice == 'Y':
                    attachments = []
                    print('You can enter multiple paths to attach multiple files')
                    input_path = input('Separate by comma (Ex: D:\MyLaptop, D:\MyPC): ')
                    attachments = input_list(input_path)
                else:
                    attachments = None       
                
                # code to send mail here
                send_email(subject, content_text, to_list, cc_list, bcc_list, attachments)
                print('Email sent successfully')
            case '2': # view mail
                data_mail = read_json('mailbox/list_mails.json')
                # Menu 2
                print('Choose folder to view mail')
                print('0. Inbox')
                print('1. Project')
                print('2. Important')
                print('3. Work')
                print('4. Spam')
                print('00. Go back')
                choice = input('Your choice: ')
                list_ids = []
                if choice == '1':
                    # code to get list mail from list_mailbox.json with tag = tag_folder_1 
                    list_ids = get_list_ids(data_mail, 'Project')
                elif choice == '2':
                    # code to get list mail from list_mailbox.json with tag = tag_folder_2
                    list_ids = get_list_ids(data_mail, 'Important')
                elif choice == '3':
                    # code to get list mail from list_mailbox.json with tag = tag_folder_3
                    list_ids = get_list_ids(data_mail, 'Work')
                elif choice == '4':
                    # code to get list mail from list_mailbox.json with tag = tag_folder_4
                    list_ids = get_list_ids(data_mail, 'Spam')
                elif choice == '0':
                    # code to get list mail from list_mailbox.json with tag = All
                    list_ids = get_list_ids(data_mail, 'Inbox')
                elif choice == '00':
                    continue
                else:
                    print('Invalid choice')
                    os.system('pause')
                    continue
                    
                # code to show list mail: <id> <sender> <subject> <time>
                show_list_mail(data_mail, list_ids)
            
                choice = input("Do you want to read mail? (y/n)" )
                if choice == 'y' or choice == 'Y':
                    id = input('Enter id of mail you want to read: ')
                    # check if id not in range of list_ids
                    if not check_id(id, list_ids):
                        print('Invalid id')
                        os.system('pause')
                        continue
                    # change type of id from str to int
                    id = list_ids[int(id)-1]
                    
                    # # code to read and print email data here
                    # data = read_data_mail(email_data)
                    # print(data)
                    
                    # call get_content() to show email content
                    content_text = get_content(id, data_mail)
                    print('Content: ')
                    print(content_text)
                    
                    # mark email as read
                    # code to mark email as read here
                    mark_as_read(id, data_mail)
                    write_json(data_mail, 'mailbox/list_mails.json')
                    
                    # if email has attachment, ask user if they want to save attachment
                    # code to check if email has attachment here
                    attachments = get_list_attachments(id, data_mail) 
                    if attachments != []:
                        # show attachment name
                        # code to show attachment name here
                        print('Attachment: ')
                        for attachment in attachments:
                            print(f'{attachments.index(attachment) + 1}. {attachment}')
                        
                        choice = input('Do you want to save attachment? (y/n)')
                        if choice == 'y' or choice == 'Y':
                            id_file = input('Enter the id of attachment: ')
                            if not check_id(id_file, attachments):
                                print('Invalid id')
                                os.system('pause')
                                continue
                            dst_path = input('Enter path to save(if not exist, it will be created automatically): ')
                            file_data = get_attachment_byte(id, int(id_file)-1, data_mail)
                            file_name = attachments[int(id_file)-1]
                            
                            save_attachment(file_data, file_name, dst_path)
                                   
            case '3':
                break
            case default:
                print('Invalid choice')
        os.system('pause')
        
if __name__ == '__main__':
    stop_event = threading.Event()
    init()
    fetch_email();
    thread = threading.Thread(target=auto_install_mail)
    # Bắt đầu luồng
    thread.start()         
    menu()   
    stop_event.set()
    thread.join()
            
    