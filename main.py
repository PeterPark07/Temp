import requests
from bs4 import BeautifulSoup
import os
from flask import Flask, request
import telebot

app = Flask(__name__)
bot = telebot.TeleBot(os.getenv('bot'), threaded=False)
url = os.getenv('url')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

@app.route('/', methods=['POST'])
def telegram():
    # Process incoming updates from Telegram
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return 'OK', 200

    
    
@bot.message_handler(func=lambda message: True)
def images(message):
    input_text = message.text.split(' ')[0]
    global url
    local_url = url + f'index.php?page=post&s=list&tags={input_text}'
    bot.reply_to(message, local_url)
    response = requests.get(local_url, headers=headers)

    # Step 4: Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Step 5: Create a BeautifulSoup object to parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Step 6: Find all the <img> tags in the HTML
        img_tags = soup.find_all('img')
        links = ""
        counter = 0  # Counter variable for limiting the number of links

        # Step 7: Extract the src attribute from each img tag and display them
        for img in img_tags:
            src = img.get('src')
            absolute_url = requests.compat.urljoin(local_url, src)
            links += absolute_url
            links += '\n'
            counter += 1  # Increment the counter

            if counter == 10:  # Break the loop when counter reaches 10
                break

        bot.reply_to(message, links)
    else:
        bot.reply_to(message, "Failed to fetch website")

