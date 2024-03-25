import os

import telebot

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    comment = "2e7b37be-5ee4-4285-aee5-94bd0a2e8f9d"
    response = "You need to send 0.01 TON for verification your wallet.\r\n\r\n"
    response += "Send to: " + WALLET_ADDRESS + "\r\n\r\n"
    response += "Comment: " + comment + "\r\n\r\n"
    response += "Important! Don't forget to include comment in transaction!"

    bot.reply_to(message, response)


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, message.text)

bot.infinity_polling()