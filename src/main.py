import requests
import os
from helper.functions import construct_local_url, extract_links, extract_image_urls
from flask import Flask, request
import telebot
import time

app = Flask(__name__)
bot = telebot.TeleBot(os.getenv('bot'), threaded=False)
url = os.getenv('url')
number_images = 10
modes = [[2, 0.2], [5, 0.5], [20, 2], [60, 5]]
mode = modes[2]
last_message_id = None

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

message_ids = []

@app.route('/', methods=['POST'])
def telegram():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return 'OK', 200


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Helloo there, I am The Rule 34 Bot. I will reply to your messages with images.\n\nUse /settings to modify my functionality.")

@bot.message_handler(commands=['settings'])
def handle_settings(message):
    markup = telebot.types.InlineKeyboardMarkup()

    number_images_options = ['2 images', '5 images', '10 images (default)', '20 images', '30 images', '40 images']
    number_images_buttons = []
    for option in number_images_options:
        number_images_buttons.append(telebot.types.InlineKeyboardButton(str(option), callback_data=f"num{option}"))
    markup.row(*number_images_buttons[0:3])
    markup.row(*number_images_buttons[3:6])
    
    mode_options = [
        ("Timeout = 2 seconds", 1),
        ("Timeout = 5 seconds", 2),
        ("Timeout = 20 seconds (Default)", 3),
        ("Timeout = 60 seconds", 4)
    ]
    mode_buttons = []
    for option in mode_options:
        mode_buttons.append(telebot.types.InlineKeyboardButton(option[0], callback_data=f"mode{option[1]}"))
    markup.row(*mode_buttons[0:2])
    markup.row(*mode_buttons[2:4])
    
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.message:
        if call.data.startswith("num"):
            global number_images
            number_images = int(call.data.replace("num", '').split()[0])
            bot.answer_callback_query(call.id, f"Number of images set to {number_images}")
            bot.send_message(call.message.chat.id, f"Number of images changed to {number_images}")

        elif call.data.startswith("mode"):
            mode_info = int(call.data.replace('mode', ''))
            global mode
            mode = modes[mode_info - 1]
            bot.answer_callback_query(call.id, f"Mode changed to {mode_info}")
            bot.send_message(call.message.chat.id, f"Mode changed to {mode_info}")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)


@bot.message_handler(func=lambda message: True)
def images(message):
    global last_message_id

    if last_message_id == message.message_id:
        return

    last_message_id = message.message_id

    input_text = message.text.replace(' ', '_')

    local_url, input_text, last_pageid = construct_local_url(input_text, number_images)

    response = requests.get(local_url, headers=headers)

    if response.status_code == 200:
        links = extract_links(number_images, response)

        if links :
            images = extract_image_urls(links)
            send_images(message.chat.id, images, message_ids)
            bot.reply_to(message, f"/more{last_pageid+1}_{input_text}")
        else:
            bot.reply_to(message, "No results")
    else:
        bot.reply_to(message, "No results")

    schedule_message_deletion(message, message_ids, mode)
    return



def send_images(chat_id, images, message_ids):
    for img_url in images:
        sent_message = bot.send_photo(chat_id, img_url)
        time.sleep(0.3)
        message_ids.append(sent_message.message_id)


def schedule_message_deletion(message, message_ids, mode):
    time.sleep(mode[0])
    for message_id in message_ids:
        time.sleep(mode[1])
        bot.delete_message(message.chat.id, message_id)
    message_ids.clear()