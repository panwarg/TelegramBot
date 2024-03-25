import os
import telebot
from dotenv import load_dotenv
import requests
import uuid

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')

bot = telebot.TeleBot(BOT_TOKEN)

def get_ton_transactions():
    url = "https://toncenter.com/api/v2/getTransactions"
    params = {"address": WALLET_ADDRESS, "limit": 99}
    response = requests.get(url, params)
    return response

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    comment = uuid.uuid1()
    response = "You need to send 0.01 TON for verification your wallet.\r\n\r\n"
    response += "Send to: " + WALLET_ADDRESS + "\r\n\r\n"
    response += "Comment: " + str(comment) + "\r\n\r\n"
    response += "Important! Don't forget to include comment in transaction!"

    bot.reply_to(message, response)


@bot.message_handler(func=lambda msg: True)
def echo_all(message):

    ton_txs = get_ton_transactions()

    response = "This comment is NOT available in transactions of this wallet: " + WALLET_ADDRESS

    if message.text in ton_txs.text:
        response = "This comment is AVAILABLE in transactions of this wallet: " + WALLET_ADDRESS

    bot.reply_to(message, response)

bot.infinity_polling()