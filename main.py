import requests
from bs4 import BeautifulSoup
import os
from flask import Flask, request
import telebot
import time

app = Flask(__name__)
bot = telebot.TeleBot(os.getenv('bot'), threaded=False)
url = os.getenv('url')
number_images = 15
modes = [[5, 0.5] , [20, 2 ] , [60 , 5 ]]
mode = modes[0]
last_message_id = None

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

message_ids = []  # List to store message IDs

@app.route('/', methods=['POST'])
def telegram():
    # Process incoming updates from Telegram
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return 'OK', 200

    
@bot.message_handler(commands=['settings'])
def handle_settings(message):
    markup = telebot.types.InlineKeyboardMarkup()
    
    # Add button to change number_images
    number_images_options = [5, 10, 15, 20, 25, 30]
    number_images_buttons = []
    for option in number_images_options:
        number_images_buttons.append(telebot.types.InlineKeyboardButton(str(option), callback_data=f"num_{option}"))
    markup.row(*number_images_buttons)
    
    # Add button to change mode
    mode_options = [("Mode 1", 5, 0.5), ("Mode 2", 20, 2), ("Mode 3", 60, 5)]
    mode_buttons = []
    for option in mode_options:
        mode_buttons.append(telebot.types.InlineKeyboardButton(option[0], callback_data=f"mode{option[0]}"))
    markup.row(*mode_buttons)
    
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.message:
        # Callback for changing number_images
        if call.data.startswith("num"):
            global number_images
            number_images = int(call.data.split("_")[1])
            bot.answer_callback_query(call.id, f"Number of images set to {number_images}")
            bot.send_message(call.message.chat.id, f"Number of images changed to {number_images}")
        
        # Callback for changing mode
        elif call.data.startswith("mode"):
            mode_info = int(call.data.replace('modeMode ',''))
            global mode
            mode = modes[mode_info - 1]
            bot.answer_callback_query(call.id, f"Mode changed to {mode+1}")
            bot.send_message(call.message.chat.id, f"Mode changed to {mode+1}")
        
        # Edit the original message to remove the inline keyboard
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

    
@bot.message_handler(func=lambda message: True)
def images(message):
    global last_message_id

    # Check if this is the same message as the previous one
    if last_message_id == message.message_id:
        return

    # Store the current message ID as the most recent one
    last_message_id = message.message_id
    
    input_text = message.text.replace(' ', '_')
    
    if input_text.startswith('/more'):
        input_text = input_text.replace('/more','')
        num = int(input_text[0]) * number_images
        input_text = input_text[2:]
        local_url = url + f'index.php?page=post&s=list&tags={input_text}&pid={num}'
    else:
        local_url = url + f'index.php?page=post&s=list&tags={input_text}&pid=0'
        
    response = requests.get(local_url, headers=headers)

    if response.status_code == 200:
        links = get_links(number_images, response)

        if links != "":
            images = get_image_urls(links)
            send_images(message.chat.id, images, message_ids)
        else:
            bot.reply_to(message, "No results")
    else:
        bot.reply_to(message, "Failed to fetch website")

    schedule_message_deletion(message, message_ids , mode)
    return



def get_links(counter, response):
    soup = BeautifulSoup(response.text, 'html.parser')
    links = ""

    a_tags = soup.find_all('a')

    for a in a_tags:
        href = a.get('href')
        if 's=view' in href:
            absolute_url = requests.compat.urljoin(url, href)
            links += absolute_url
            links += '\n'
            counter -= 1
        if counter == 0:
            break
    return links

def get_image_urls(links):
    images = []
    for i in links.splitlines():
        img_response = requests.get(i, headers=headers)
        if img_response.status_code == 200:
            img_soup = BeautifulSoup(img_response.text, 'html.parser')
            img_tags = img_soup.find_all('img', id='image')
            for img in img_tags:
                img_src = img['src'].split('?', 1)[0]
                images.append(img_src)
    return images


def send_images(chat_id, images, message_ids):
    for img_url in images:
        sent_message = bot.send_photo(chat_id, img_url)
        message_ids.append(sent_message.message_id)

        
def schedule_message_deletion(message, message_ids, mode):
    time.sleep(mode[0])
    for message_id in message_ids:
        time.sleep(mode[1])
        bot.delete_message(message.chat.id, message_id)
    message_ids.clear()
