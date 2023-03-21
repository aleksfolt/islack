from flask import Flask, render_template, request, redirect, url_for
from pywebio.platform.flask import webio_view
from pywebio import start_server, input, output, Session


app = Flask(__name__)

# Имитация базы данных с пользователями и каналами
USERS = {
    'user1': {'password': 'pass1', 'channels': ['general']},
    'user2': {'password': 'pass2', 'channels': ['general', 'random']},
    'user3': {'password': 'pass3', 'channels': ['random']}
}

CHANNELS = {
    'general': {
        'description': 'Общий канал',
        'messages': [
            {'user': 'user1', 'message': 'Привет!'},
            {'user': 'user2', 'message': 'Как дела?'}
        ]
    },
    'random': {
        'description': 'Канал для случайных разговоров',
        'messages': [
            {'user': 'user2', 'message': 'Сегодня хорошая погода :)'},
            {'user': 'user3', 'message': 'Я нашел новый рецепт пиццы!'}
        ]
    }
}

# Функция проверки аутентификации
def check_auth(username, password):
    if username in USERS and USERS[username]['password'] == password:
        return True
    else:
        return False

# Функция для получения списка каналов пользователя
def get_user_channels(username):
    if username in USERS:
        return USERS[username]['channels']
    else:
        return []

# Функция для создания нового канала
def create_channel():
    channel_name = input("Введите название канала:")
    channel_description = input("Введите описание канала:")
    CHANNELS[channel_name] = {'description': channel_description, 'messages': []}
    output.put_text(f"Канал {channel_name} успешно создан!")

# Функция для отправки сообщения в канал
def send_message(channel_name, username):
    message = input("Введите сообщение:")
    CHANNELS[channel_name]['messages'].append({'user': username, 'message': message})
    output.put_text("Сообщение отправлено!")

# Основная страница (список каналов)
@app.route('/')
def index():
    session = Session.get()
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    username = session.get('username')
    channels = get_user_channels(username)
    return render_template('index.html', username=username, channels=channels)

# Страница входа в систему
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_auth(username, password):
            session = Session.get()
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            output.put_text("Неверное имя пользователя или пароль!")
    return render_template('login.html')

# Страница выхода из системы
@app.route('/logout')
def logout():
    session = Session.get()
    session['logged_in'] = False
    session['username'] = None
    return redirect(url_for('login'))

# Страница выбранного канала
@app.route('/channel/<channel_name>', methods=['GET', 'POST'])
def channel(channel_name):
    session = Session.get()
    username = session.get('username')

    # Если пользователь не авторизован, перенаправляем на страницу входа
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Если канал не существует, выводим ошибку
    if channel_name not in CHANNELS:
        output.put_text(f"Канал '{channel_name}' не существует!")
        return redirect(url_for('index'))

    # Если пользователь не имеет доступа к каналу, выводим ошибку
    if channel_name not in get_user_channels(username):
        output.put_text(f"У вас нет доступа к каналу '{channel_name}'!")
        return redirect(url_for('index'))

    # Если запрос метода POST, отправляем сообщение в канал
    if request.method == 'POST':
        send_message(channel_name, username)

    # Выводим сообщения канала
    messages = CHANNELS[channel_name]['messages']
    return render_template('channel.html', channel_name=channel_name, messages=messages)

# Страница создания нового канала
@app.route('/create_channel', methods=['GET', 'POST'])
def create_channel_page():
    session = Session.get()
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Если запрос метода POST, создаем новый канал
    if request.method == 'POST':
        create_channel()

    return render_template('create_channel.html')

# Функция запуска сервера
def main():
    # Запускаем сервер PyWebIO на Flask
    app.add_url_rule('/pywebio/<path:path>', 'webio_view', webio_view(index), methods=['GET', 'POST', 'OPTIONS'])
    start_server(app)


if __name__ == '__main__':
    main()
