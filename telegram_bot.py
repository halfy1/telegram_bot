import json
import telebot
from telebot import types
import openpyxl
import matplotlib.pyplot as plt

def load_labs(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            data = json.load(file)
            print(f"Loaded {len(data['labs'])} labs from {file_name}")
            return data['labs']
    except FileNotFoundError:
        print(f"File {file_name} not found.")
        return []

def load_admins():
    with open('admins.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        return set(data.get('admins', []))

def save_lab_data(lab_data):
    try:
        with open('labs.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            labs_data = data['labs']
    except FileNotFoundError:
        labs_data = []

    labs_data.append(lab_data)

    with open('labs.json', 'w', encoding='utf-8') as file:
        json.dump({'labs': labs_data}, file, indent=4, ensure_ascii=False)

TOKEN='6954772097:AAGBsH6mchQd6OjKk_5YUWhpV9wIvrkRH9A'
bot = telebot.TeleBot(TOKEN)
ADMINS = load_admins()

@bot.message_handler(commands=['status'])
def check_status(message):
    user_id = message.from_user.id

    if user_id in ADMINS:
        bot.send_message(message.chat.id, 'Вы являетесь администратором.')
    else:
        bot.send_message(message.chat.id, 'У вас нет прав администратора')

def show_keyboard(message):
    custom_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3, one_time_keyboard=True)
    return bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=custom_keyboard)

bot.set_my_commands([
    telebot.types.BotCommand('start', 'Начать работу'),
    telebot.types.BotCommand('help', 'Получить помощь'),
    telebot.types.BotCommand('status', 'Проверить свой статус'),
    telebot.types.BotCommand('add_lab', 'Добавить лабораторную работу')
])

labs_data = load_labs('labs.json')
labs = {}

for lab in labs_data:
    semester = lab['semester']
    title = lab['title']

    if semester not in labs:
        labs[semester] = []

    labs[semester].append(title)

@bot.message_handler(commands=['start'])
def start(message):
    labs_data = load_labs('labs.json')
    markup = types.InlineKeyboardMarkup(row_width=2)
    available_semesters = [semester for semester, labs_list in labs.items() if labs_list]

    for semester in available_semesters:
        btn = types.InlineKeyboardButton(f'{semester}', callback_data=f'semester_{semester}')
        markup.add(btn)

    bot.send_message(message.chat.id, 'Выберите семестр:', reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = "Этот бот поможет вам найти нужную лабораторную работу.\n\n" \
                "Используйте кнопку 'Старт' слева, чтобы начать работу.\n"
    bot.send_message(message.chat.id, help_text)

@bot.callback_query_handler(func=lambda call: call.data.startswith('semester_'))
def handle_semester(call):
    labs_data = load_labs('labs.json')
    chosen_semester = int(call.data.split('_')[1])
    labs_in_semester = [lab for lab in labs_data if lab['semester'] == chosen_semester]

    markup = types.InlineKeyboardMarkup(row_width=1)
    for lab in labs_in_semester:
        btn = types.InlineKeyboardButton(text=lab['title'], callback_data=f'lab_{lab["number"]}')  # Изменение здесь
        markup.add(btn)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Выберите лабораторную работу:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lab_'))
def handle_lab(call):
    labs_data = load_labs('labs.json')
    chosen_lab = call.data.split('_')[1]
    lab_data = next((lab for lab in labs_data if lab['number'] == chosen_lab), None)

    if not lab_data:
        bot.answer_callback_query(callback_query_id=call.id, text='Лабораторная работа не найдена.')
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_output = types.InlineKeyboardButton(text='Вывод', callback_data=f'output_{chosen_lab}')
    markup.add(btn_output)
    btn_graph = types.InlineKeyboardButton(text='Графики', callback_data=f'graphs_{chosen_lab}')
    markup.add(btn_graph)
    btn_excel = types.InlineKeyboardButton(text='Расчёт', callback_data=f'excel_{chosen_lab}')
    markup.add(btn_excel)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f'Лабораторная работа: {lab_data["title"]}', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('output_') or call.data.startswith('graphs_') or call.data.startswith('excel_'))
def handle_callback(call):
    query, number = call.data.split('_', 1)
    lab = next((lab for lab in labs_data if lab['number'] == number), None)

    if not lab:
        bot.answer_callback_query(callback_query_id=call.id, text='Лабораторная работа не найдена.')
        return

    query_map = {
        'output': 'Вывод отсутствует.',
        'graphs': 'Графики не добавлены.',
        'excel': 'Excel файл не добавлен.'
    }

    if lab.get(query) is None:
        bot.answer_callback_query(callback_query_id=call.id, text=query_map[query])
    else:
        if query == 'output':
            bot.send_message(call.message.chat.id, lab[query])
        if query == "graphs":
            markup = types.InlineKeyboardMarkup(row_width=1)
            for i, graph in enumerate(lab['graphs'], start=1):
                btn = types.InlineKeyboardButton(text=graph['title'], callback_data=f'graph_{i}')
                markup.add(btn)
            bot.send_message(call.message.chat.id, 'Выберите график:', reply_markup=markup)

        if query == 'excel':
            bot.send_message(call.message.chat.id, lab['excel_description'] + '\n\nВведите данные через пробел и по строчкам:')
            bot.register_next_step_handler(call.message, insert_user_data, lab)

@bot.callback_query_handler(func=lambda call: call.data.startswith('graphs_'))
def handle_graphs(call):
    chosen_lab = call.data.split('_')[1]
    lab_data = next((lab for lab in labs_data if lab['number'] == chosen_lab), None)

    if not lab_data or 'graphs' not in lab_data:
        bot.answer_callback_query(callback_query_id=call.id, text='Графики не добавлены.')
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for graph in lab_data['graphs']:
        btn = types.InlineKeyboardButton(text=graph['title'], callback_data=f'graph_{graph["title"]}')
        markup.add(btn)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Выберите график:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('graph_'))
def handle_graph(call):
    chosen_graph = call.data.split('_')[1]
    graph_data = next((graph for graph in labs_data['graphs'] if graph['title'] == chosen_graph), None)

    if not graph_data:
        bot.answer_callback_query(callback_query_id=call.id, text='График не найден.')
        return

    bot.send_message(call.message.chat.id, graph_data['title'] + '\n\nВведите данные через пробел и по строчкам:')
    bot.register_next_step_handler(call.message, draw_graph, graph_data)

def insert_user_data(message, lab):
    user_data = [row.split(' ') for row in message.text.split('\n')]
    excel = openpyxl.load_workbook(lab['excel'])

    for cell_ranges, data_row in zip(lab['excel_cells'], user_data):
        for cell_range in cell_ranges.split():
            cells = excel.active[cell_range]
            for cell, data in zip(cells[0], data_row):
                cell.value = data

    excel.save('updated_' + lab['excel'])
    with open('updated_' + lab['excel'], 'rb') as file:
        bot.send_document(message.chat.id, file)

def draw_graph(message, graph):
    user_data = message.text.split()
    x_data = [float(point.split(',')[0]) for point in user_data]
    y_data = [float(point.split(',')[1]) for point in user_data]

    plt.figure(figsize=(10, 6))
    plt.title(graph['title'])
    plt.xlabel(graph['xlabel'])
    plt.ylabel(graph['ylabel'])

    if graph['type'] == 'По точкам':
        plt.plot(x_data, y_data, 'o')
    elif graph['type'] == 'Аппроксимация':
        z = np.polyfit(x_data, y_data, 1)
        p = np.poly1d(z)
        plt.plot(x_data, p(x_data), 'r--')

    plt.grid(True)
    plt.savefig('graph.png')
    plt.close()

    with open('graph.png', 'rb') as file:
        bot.send_photo(message.chat.id, file)

@bot.message_handler(commands=['add_admin'])
def add_admin(message):
    if message.from_user.id in admins:
        user_id = message.text.split()[1]

        if user_id.isdigit():
            user_id = int(user_id)
            admins.append(user_id)

            with open('admins.json', 'w', encoding='utf-8') as file:
                json.dump({'admins': admins}, file, ensure_ascii=False, indent=4)

            bot.send_message(message.chat.id, f'Пользователь с ID {user_id} успешно добавлен в список администраторов.')
        else:
            bot.send_message(message.chat.id, 'Неверный формат ID.')
    else:
        bot.send_message(message.chat.id, 'У вас недостаточно прав для выполнения этой команды.')

@bot.message_handler(commands=['add_lab'])
def add_lab(message):
    if message.from_user.id not in ADMINS:
        bot.send_message(message.chat.id, 'У вас недостаточно прав для выполнения этой команды.')
        return

    bot.send_message(message.chat.id, 'Введите номер семестра:')
    bot.register_next_step_handler(message, get_semester)

def get_semester(message):
    semester = int(message.text)
    bot.send_message(message.chat.id, 'Введите номер лабораторной работы:')
    bot.register_next_step_handler(message, get_lab_number, semester)

def get_lab_number(message, semester):
    lab_number = message.text
    bot.send_message(message.chat.id, 'Введите название лабораторной работы:')
    bot.register_next_step_handler(message, get_lab_name, semester, lab_number)

def get_lab_name(message, semester, lab_number):
    lab_name = message.text
    bot.send_message(message.chat.id, 'Введите вывод лабораторной работы (или введите "Пропустить", если вывода нет):')
    bot.register_next_step_handler(message, get_lab_output, semester, lab_number, lab_name)

def get_lab_output(message, semester, lab_number, lab_name):
    lab_output = message.text if message.text != 'Пропустить' else None
    bot.send_message(message.chat.id, 'Введите количество графиков (или введите "Пропустить", если графиков нет):')
    bot.register_next_step_handler(message, get_graph_count, semester, lab_number, lab_name, lab_output)

def get_graph_count(message, semester, lab_number, lab_name, lab_output):
    if message.text == 'Пропустить':
        graph_count = 0
        graphs = []
    else:
        graph_count = int(message.text)
        graphs = []
    if graph_count > 0:
        bot.send_message(message.chat.id, f'Введите название для графика 1:')
        bot.register_next_step_handler(message, get_graph_title, semester, lab_number, lab_name, lab_output, graphs, 1, graph_count)
    else:
        bot.send_message(message.chat.id, 'Пришлите файл Excel (.xlsx) (или введите "Пропустить", если файла нет):')
        bot.register_next_step_handler(message, get_excel_file, semester, lab_number, lab_name, lab_output, graphs)

def get_graph_title(message, semester, lab_number, lab_name, lab_output, graphs, current_graph, total_graphs):
    graph_title = message.text
    bot.send_message(message.chat.id, 'Введите подпись для оси X:')
    bot.register_next_step_handler(message, get_graph_xlabel, semester, lab_number, lab_name, lab_output, graphs, graph_title, current_graph, total_graphs)
def get_graph_xlabel(message, semester, lab_number, lab_name, lab_output, graphs, graph_title, current_graph, total_graphs):
    graph_xlabel = message.text
    bot.send_message(message.chat.id, 'Введите подпись для оси Y:')
    bot.register_next_step_handler(message, get_graph_ylabel, semester, lab_number, lab_name, lab_output, graphs, graph_title, graph_xlabel, current_graph, total_graphs)
def get_graph_ylabel(message, semester, lab_number, lab_name, lab_output, graphs, graph_title, graph_xlabel, current_graph, total_graphs):
    graph_ylabel = message.text
    markup = types.InlineKeyboardMarkup(row_width=2)
    graphs.append({
        'title': graph_title,
        'xlabel': graph_xlabel,
        'ylabel': graph_ylabel
    })
    graph_index = len(graphs) - 1  # Индекс только что добавленного графика
    btn_dot = types.InlineKeyboardButton('По точкам', callback_data=f'dot_{graph_index}_{current_graph}_{total_graphs}')
    btn_approx = types.InlineKeyboardButton('Аппроксимация', callback_data=f'approx_{graph_index}_{current_graph}_{total_graphs}')
    markup.add(btn_dot, btn_approx)
    bot.send_message(message.chat.id, 'Выберите тип графика:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dot') or call.data.startswith('approx'))
def get_graph_type(call):
    data = call.data.split('_')
    graph_type = 'По точкам' if data[0] == 'dot' else 'Аппроксимация'
    graph_index = int(data[1])
    current_graph = int(data[2])
    total_graphs = int(data[3])
    graphs[graph_index]['type'] = graph_type
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(call.message.chat.id, 'График успешно добавлен!', reply_markup=markup)
    if current_graph < total_graphs:
        bot.send_message(call.message.chat.id, f'Введите название для графика {current_graph + 1}:')
        bot.register_next_step_handler(call.message, get_graph_title, semester, lab_number, lab_name, lab_output, graphs, current_graph + 1, total_graphs)
    else:
        bot.send_message(call.message.chat.id, 'Пришлите файл Excel (.xlsx) (или введите "Пропустить", если файла нет):')
        bot.register_next_step_handler(call.message, get_excel_file, semester, lab_number, lab_name, lab_output, graphs)

def get_excel_file(message, semester, lab_number, lab_name, lab_output, graphs):
    if message.text == 'Пропустить':
        excel = None
        excel_description = None
        excel_cells = None
    else:
        try:
            if message.document.mime_type != 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                raise ValueError('Неверный формат файла. Ожидается файл .xlsx')
            excel_id = message.document.file_id
            excel_info = bot.get_file(excel_id)
            downloaded_file = bot.download_file(excel_info.file_path)
            with open(f"{message.document.file_name}", 'wb') as new_file:
                new_file.write(downloaded_file)
            excel_description = message.document.file_name
        except (AttributeError, ValueError):
            bot.send_message(message.chat.id, 'Вы должны прислать файл в формате .xlsx')
            return get_excel_file(message, semester, lab_number, lab_name, lab_output, graphs)
    bot.send_message(message.chat.id, 'Введите пояснительный текст для файла Excel:')
    bot.register_next_step_handler(message, get_excel_description, semester, lab_number, lab_name, lab_output, graphs, excel_description)

def get_excel_description(message, semester, lab_number, lab_name, lab_output, graphs, excel):
    if excel is None or message.text == 'Пропустить':
        excel_description = None
    else:
        excel_description = message.text
    bot.send_message(message.chat.id, 'Введите ячейки в которые надо вставлять значения от пользователя (в формате "A1, B2, C3"):')
    bot.register_next_step_handler(message, get_excel_cells, semester, lab_number, lab_name, lab_output, graphs, excel, excel_description)

def get_excel_cells(message, semester, lab_number, lab_name, lab_output, graphs, excel, excel_description):
    if excel is None or message.text == 'Пропустить':
        excel_cells = None
        excel_description = None
    else:
        excel_cells = message.text.split(', ')

    lab_data = {
        'semester': semester,
        'number': lab_number,
        'title': lab_name,
        'output': lab_output,
        'excel': excel,
        'excel_description': excel_description,
        'excel_cells': excel_cells,
        'graphs': graphs
    }

    save_lab_data(lab_data)
    bot.send_message(message.chat.id, 'Лабораторная работа успешно добавлена!')

if __name__ == '__main__':
    bot.polling(none_stop=True)
