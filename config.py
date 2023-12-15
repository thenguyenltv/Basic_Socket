import os
import json

# Dữ liệu cần ghi vào tệp JSON
config_data = {
    "SMTP_SERVER": "127.0.0.1",
    "SMTP_PORT": 2225,
    "POP3_SERVER": "127.0.0.1",
    "POP3_PORT": 3335,
    "SENDER_EMAIL": "thenguyenltv@gmail.com",
    "USERNAME": "triduc@gmail.com",
    "PASSWORD": "1234",
    "filters": [
        {"criteria": "from", "keywords": ["thenguyenltv@gmail.com"], "folder": "Project"},
        {"criteria": "subject", "keywords": ["urgent", "ASAP"], "folder": "Important"},
        {"criteria": "content", "keywords": ["report", "meeting"], "folder": "Work"},
        {"criteria": "spam", "keywords": ["virus", "hack", "crack"], "folder": "Spam"}
    ]
}

# Tên của tệp JSON
file_name = "config.json"

# Ghi dữ liệu vào tệp JSON
with open(file_name, "w") as json_file:
    json.dump(config_data, json_file, indent=2)

