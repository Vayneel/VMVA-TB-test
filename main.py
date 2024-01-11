"""
VMVA-TB main module
"""

import telebot  # work with Telegram API
import openai  # work with OpenAI API
import json  # use outside files like users and passwords
from random import choice  # used in password generation
import asyncio  # used in some funcs to make them async

TELEGRAM_BOT_TOKEN = "YOUR TOKEN HERE"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
openai.api_key = "OPENAI API KEY HERE"
# openai_client = openai.OpenAI()


# todo block any command if already called one and haven't finished with it yet


pass_name_enter = False
pass_name = ''
question_enter = False
question = ''


def user_check(message):
    with open("data/users.json") as file:
        users = json.load(file)
    if str(message.from_user.id) in list(users.keys()):
        return users
    else:
        users[str(message.from_user.id)] = message.from_user.first_name
        with open("data/users.json", "w") as file:
            json.dump(users, file)
        return users


def generate_password():
    generated_password = ''
    while len(generated_password) < 16:
        generated_password += choice("0123456789aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ0123456789")
    return generated_password


def gpt_answer(gpt_question, mcid):
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "You are a loyal female assistant, Albedo," +
                        " skilled in answering any questions of user."},
            {"role": "user", "content": gpt_question}
        ]
    )
    bot.send_message(mcid, completion.choices[0].message.content)


async def hide_pass(cid, mid):
    await asyncio.sleep(5)
    bot.edit_message_text(f"I hid the password", cid, mid)


@bot.message_handler(commands=['start'])
def start(message):
    users = user_check(message)
    bot.send_message(message.chat.id, f"Welcome, {users[str(message.from_user.id)]}")


@bot.message_handler(commands=['getpass'])
def getpass(message):
    users = user_check(message)
    global pass_name_enter
    pass_name_enter = True
    bot.send_message(message.chat.id, f'{users[str(message.from_user.id)]}, enter keyword, please')


@bot.message_handler(commands=['ask'])
def ask(message):
    users = user_check(message)
    global question_enter
    question_enter = True
    bot.send_message(message.chat.id, f'{users[str(message.from_user.id)]}, ask any questions')


@bot.message_handler(content_types=['text'])
def text(message):
    users = user_check(message)
    global pass_name_enter
    global question_enter

    if pass_name_enter:
        global pass_name
        pass_name_enter = False
        pass_name = message.text.lower()
        try:
            with open(f"data/{str(message.from_user.id)}_passwords.json") as file:
                passwords = json.load(file)
        except FileNotFoundError:
            with open(f"data/{str(message.from_user.id)}_passwords.json", 'w') as file:
                passwords = {}
                json.dump(passwords, file)
        try:
            cid = message.chat.id
            mid = bot.send_message(cid, "I've found password, " +
                                   f"{users[str(message.from_user.id)]}\n{passwords[pass_name]}").message_id
            asyncio.run(hide_pass(cid, mid))
        except KeyError:
            markup = telebot.types.InlineKeyboardMarkup()
            no_btn = telebot.types.InlineKeyboardButton("Never mind", callback_data="add_password_no")
            try_btn = telebot.types.InlineKeyboardButton("I'll try again", callback_data="add_password_try")
            yes_btn = telebot.types.InlineKeyboardButton("Of course, you should", callback_data="add_password_yes")
            markup.row(try_btn, no_btn)
            markup.add(yes_btn)
            bot.send_message(message.chat.id, f"I'm sorry, {users[str(message.from_user.id)]}, but I can't" +
                             " find such keyword. Should I append our password list?", reply_markup=markup)
    elif question_enter:
        global question
        question_enter = False
        question = message.text
        gpt_answer(question, message.chat.id)
    else:
        if message.text[-1] == '?':
            gpt_answer(message.text, message.chat.id)  # todo I need /ask?


@bot.callback_query_handler(func=lambda callback: True)  # todo too hard to read
def callback_handle(callback):
    users = user_check(callback)
    if callback.data == "add_password_no":
        bot.edit_message_text(f"I'm sorry, {users[str(callback.from_user.id)]}, but I can't find such keyword",
                              callback.message.chat.id, callback.message.message_id)
    elif callback.data == "add_password_yes":
        global pass_name
        bot.edit_message_text(f"I'm sorry, {users[str(callback.from_user.id)]}, but I can't find such keyword",
                              callback.message.chat.id, callback.message.message_id)
        with open(f'data/{str(callback.from_user.id)}_passwords.json') as file:
            passwords = json.load(file)
        new_pass = generate_password()
        passwords[pass_name] = new_pass
        with open(f'data/{str(callback.from_user.id)}_passwords.json', 'w') as file:
            json.dump(passwords, file)
        cid = callback.message.chat.id
        bot.send_message(cid, f"Successfully added new password, {users[str(callback.from_user.id)]}\n")
        mid = bot.send_message(cid, f"Keyword: {pass_name}\nPassword: {new_pass}").message_id
        asyncio.run(hide_pass(cid, mid))
    elif callback.data == "add_password_try":
        global pass_name_enter
        pass_name_enter = True
        bot.edit_message_text(f"I'm sorry, {users[str(callback.from_user.id)]}, but I can't find such keyword, " +
                              "but if you wish to try again..",
                              callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, "Enter keyword again, please")


bot.infinity_polling()
