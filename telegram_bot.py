import telebot
from telebot import types
import data

bot = telebot.TeleBot('6954772097:AAGBsH6mchQd6OjKk_5YUWhpV9wIvrkRH9A')

USER_STATE = {}

def get_user_state(user_id):
    return USER_STATE.get(user_id, 'NORMAL')

def update_user_state(user_id, state):
    USER_STATE[user_id] = state

@bot.message_handler(commands =["start"])
def start(message):
    mess = f"Привет, <b>{message.from_user.first_name} <u>{message.from_user.last_name}</u></b>"
    bot.send_message(message.chat.id, mess, parse_mode="html")
    show_keyboard(message)

def show_keyboard(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_start = types.KeyboardButton(text="Старт")
    button_help = types.KeyboardButton(text="Помощь")
    keyboard.add(button_start, button_help)
    bot.send_message(message.chat.id, "Выбери действия под клавиатурой, если бот плохо работает)", reply_markup=keyboard)
    show_inline_keyboard(message)

def show_inline_keyboard(message):
    keyboard = types.InlineKeyboardMarkup()
    button_sem1 = types.InlineKeyboardButton(text="1", callback_data="sem1")
    button_sem2 = types.InlineKeyboardButton(text="2", callback_data="sem2")
    button_sem3 = types.InlineKeyboardButton(text="3", callback_data="sem3")
    keyboard.add(button_sem1, button_sem2, button_sem3)
    bot.send_message(message.chat.id, "Выбери семестр обучения", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data in data.labs.keys():  # Пользователь выбрал семестр
        show_labs(call.message, call.data)
    elif ":" in call.data:  # Пользователь выбрал опцию
        lab_number, option = call.data.split(":")
        for semester in data.labs.values():
            for lab in semester:
                if str(lab.number) == lab_number:
                    state = lab.run(option, call.message, bot)
                    if state:
                        update_user_state(call.message.chat.id, state)
    else:  # Пользователь выбрал лабораторную работу
        for semester in data.labs.values():
            for lab in semester:
                if str(lab.number) == call.data:
                    show_lab_options(call.message, lab)

def show_labs(message, semester):
    keyboard = types.InlineKeyboardMarkup()
    for lab in data.labs[semester]:
        button_lab = types.InlineKeyboardButton(text=str(lab.number), callback_data=str(lab.number))
        keyboard.add(button_lab)
    bot.send_message(message.chat.id, f"Выбери лабораторную работу для {semester}", reply_markup=keyboard)

def show_lab_options(message, lab):
    keyboard = types.InlineKeyboardMarkup()
    for option in data.options:
        button_option = types.InlineKeyboardButton(text=option, callback_data=f"{lab.number}:{option}")
        keyboard.add(button_option)
    bot.send_message(message.chat.id, f"Вы выбрали {lab.name}. Теперь выберите действие:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    if get_user_state(message.chat.id) == 'INPUT_FOR_OPT3':
        state = data.labs['sem2'][0].module.handle_input_for_opt3(message, bot)  # Замените 'sem1' и 0 на соответствующий семестр и номер лабораторной работы
        if state:
            update_user_state(message.chat.id, state)
    elif get_user_state(message.chat.id) == 'INPUT_FOR_OPT4':
        state = data.labs['sem2'][0].module.handle_input_for_opt4(message, bot)  # Замените 'sem1' и 0 на соответствующий семестр и номер лабораторной работы
        if state:
            update_user_state(message.chat.id, state)
    else:
        handle_normal_message(message)

def handle_normal_message(message):
    user_message = message.text
    if user_message == "Старт":
        start(message)
    elif user_message == "Помощь":
        help(message)
    else:
        response = f"Вы написали: <b>{user_message}</b>"
        bot.send_message(message.chat.id, response, parse_mode="html")

@bot.message_handler(commands =["help"])
def help(message):
    mess = f"Здесь вы можете получить помощь по использованию бота"
    bot.send_message(message.chat.id, mess, parse_mode="html")

bot.polling(none_stop=True)
