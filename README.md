# Telegram-ARP-poisoner-Bot
A Python-based network tool for ARP Spoofing testing via Telegram


# 🛡️ Telegram ARP Spoofer

This bot allows you to perform ARP vulnerability tests within a local network directly from Telegram.

## 🚀 Features
- Dynamic network scanning.
- Automatic gateway detection.
- Two-way ARP spoofing attack in a separate thread.
- Automatic restore function upon shutdown.

## ⚠️ DISCLAIMER
This software was created for educational purposes only. The author assumes no responsibility for improper use of this tool. Unauthorized use on other networks is illegal.

## 🛠️ Installation
1. Install the dependencies: `pip install -r requirements.txt`
2. Configure the `.env` file with your `BOT_KEY` and `CHAT_ID`.
3. Run with administrator privileges: `python main.py`
