import os

from flask import redirect, make_response, session, abort, url_for, Flask, render_template, request, \
    send_from_directory, jsonify
from data.user import User
from data.interest import Interest
from data.message import Message
from data.chat import Chat
from forms.interest import InterestForm
from forms.user import RegisterForm, LoginForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from get_similar import line_vector, cosdis
from flask_socketio import SocketIO, emit
import sqlalchemy as sa
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import sqlite3
from PIL import Image, ImageFile
from FindLinks import contains_contact_info
from data import session
import re

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat.db"
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.login_view = ''
login_manager.init_app(app)

socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)  # Разрешаем CORS для фронта


# загрузка пользователя
@login_manager.user_loader
def load_user(user_id):
    db_sess = session.create_session()
    return db_sess.query(User).get(user_id)


# запуск приложения
def main():
    session.global_init("db/blogs.db")
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)


@app.route("/", methods=['GET', 'POST'])
def start():
    return render_template("startScreen.html", current_user=current_user)


@app.route("/intereses")
def index():
    db_sess = session.create_session()
    interest = db_sess.query(Interest).filter(Interest.user_id != current_user.id)[::-1]
    return render_template("index.html", interest=interest, current_user=current_user)


@app.route('/geolocation')
def geolocation():
    return render_template('geolocation_ip.html')


@app.route('/viewProfile', methods=['GET'])
def viewProfile():
    user_id = request.args.get('user_id')

    db_sess = session.create_session()
    interest = db_sess.query(Interest).filter(Interest.user_id == user_id)
    user = db_sess.query(User).get(user_id)

    return render_template('view_profile.html', interest=interest, user=user)


@app.route('/viewInteres', methods=['GET'])
def viewInteres():
    user_id = request.args.get('user_id')
    interest_id = request.args.get('interest_id')

    db_sess = session.create_session()
    interest = db_sess.query(Interest).filter(Interest.id == interest_id).first()
    user = db_sess.query(User).get(user_id)

    return render_template('view_interes.html', title="", interests=interest, user=user)


@app.route('/upload_render')
def upload_render():
    return render_template('upload_file.html')


@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if 'photo' in request.files:
        db_sess = session.create_session()
        photo = request.files['photo']
        print(photo.filename)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
        photo.save(photo_path)
        user = db_sess.get(User, current_user.id)
        user.image_path = photo_path
        db_sess.commit()
        return redirect("/profile")
    return 'Файл не найден или не загружен'


# регистрация пользователя
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    print("Получен POST-запрос на /register")
    print("Request data:", request.json)
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('fullName')
    accept_policy = data.get('acceptPolicy', 0)
    allow_location = data.get('allowLocation', 0)

    db_sess = session.create_session()

    # Проверка на существующего пользователя
    if db_sess.query(User).filter(User.email == email).first():
        return jsonify({"success": False, "message": "Такой пользователь уже зарегистрирован."})

    if not accept_policy:
        return jsonify({"success": False, "message": "Вы должны принять политику конфиденциальности."})

    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, email):
        return jsonify({"success": False, "message": "Некорректный формат email."})

    # Создание нового пользователя
    user = User(
        name=full_name,
        email=email,
        allow_location=bool(allow_location),
    )
    user.set_password(password)  # Хеширование пароля

    db_sess.add(user)
    db_sess.commit()

    login_user(user)
    return jsonify({"success": True})


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db_sess = session.create_session()
    user = db_sess.query(User).get(current_user.id)
    interest = db_sess.query(Interest).filter(Interest.user == current_user)
    return render_template('profile.html', title='Профиль', interest=interest, current_user=current_user)


@app.route('/search', methods=['GET'])
def search():
    SIMILAR_RATIO = 0.5
    query = request.args.get('q')
    if query == "все":
        return redirect("/intereses")
    db_sess = session.create_session()
    if query:
        vector_query = line_vector(query)
        all_interests = db_sess.query(Interest)
        interest_searched = {}
        for i in all_interests:
            tittle_cos = cosdis(vector_query, line_vector(i.title))
            disc_cos = cosdis(vector_query, line_vector(i.description))
            if tittle_cos > SIMILAR_RATIO:
                interest_searched[i] = tittle_cos
            elif disc_cos > SIMILAR_RATIO:
                interest_searched[i] = disc_cos
        sorted_interests = [i[0] for i in sorted(interest_searched.items(), key=lambda item: item[1])][::-1]
        return render_template("chat.html", interest=sorted_interests)


# вход в учётную запись
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    db_sess = session.create_session()
    user = db_sess.query(User).filter(User.email == email).first()

    if not user or not user.check_password(password):
        return jsonify({"success": False, "message": "Неверный email или пароль."})

    login_user(user)
    return jsonify({"success": True, "message": "Вход выполнен успешно."})


# выход с учётной записи
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# добавление интереса
@app.route('/interest', methods=['GET', 'POST'])
@login_required
def add_news():
    return render_template('interest.html', title='Добавление интереса')


@app.route('/process_profile', methods=['POST'])
def process_profile():
    db_sess = session.create_session()
    user = db_sess.get(User, current_user.id)
    user.name = request.args.get('name')
    user.information = request.args.get('information')
    user.connection = request.args.get('connection')
    db_sess.commit()
    return redirect('/profile')


@app.route('/process_interest', methods=['POST'])
def process_interest():
    title = request.form['title']
    description = request.form['description']
    print(title, description)
    db_sess = session.create_session()
    interest = Interest()
    interest.title = title
    interest.description = description
    current_user.interests.append(interest)
    db_sess.merge(current_user)
    db_sess.commit()
    return redirect('/intereses')


# редактирование интереса
@app.route('/interest/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = InterestForm()
    if request.method == "GET":
        db_sess = session.create_session()
        interest = db_sess.query(Interest).filter(Interest.id == id, Interest.user == current_user).first()
        if interest:
            form.title.data = interest.title
            form.description.data = interest.description
            form.tags.data = interest.tags
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = session.create_session()
        interest = db_sess.query(Interest).filter(Interest.id == id, Interest.user == current_user).first()
        if interest:
            interest.title = form.title.data
            interest.description = form.description.data
            interest.tags = form.tags.data
            db_sess.commit()
            return redirect('/intereses')
        else:
            abort(404)
    return render_template('interest.html',
                           title='Редактирование интереса',
                           form=form
                           )


@app.route('/interest_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = session.create_session()
    interest = db_sess.query(Interest).filter(Interest.id == id,
                                              Interest.user == current_user
                                              ).first()
    if interest:
        db_sess.delete(interest)
        db_sess.commit()
    else:
        abort(404)
    previous_page = request.referrer
    if previous_page:
        return redirect(previous_page)
    else:
        return redirect(url_for('index'))


@app.route("/cookie_test")
def cookie_test():
    visits_count = int(request.cookies.get("visits_count", 0))
    if visits_count:
        res = make_response(
            f"Вы пришли на эту страницу {visits_count + 1} раз")
        res.set_cookie("visits_count", str(visits_count + 1),
                       max_age=60 * 60 * 24 * 365 * 2)
    else:
        res = make_response(
            "Вы пришли на эту страницу в первый раз за последние 2 года")
        res.set_cookie("visits_count", '1',
                       max_age=60 * 60 * 24 * 365 * 2)
    return res


@app.route("/session_test")
def session_test():
    visits_count = session.get('visits_count', 0)
    session['visits_count'] = visits_count + 1
    return make_response(
        f"Вы пришли на эту страницу {visits_count + 1} раз")


@app.route("/chat", methods=["GET"])
@login_required
def all_chats():
    db_sess = session.create_session()

    # Получаем все чаты для текущего пользователя
    chats = get_user_chats(current_user.id)  # Функция для получения всех чатов текущего пользователя

    # Для каждого чата, получаем последние сообщения
    chat_data = []
    for chat in chats:
        last_message = get_last_message(chat.id)  # Функция для получения последнего сообщения в чате
        chat_data.append({
            'chat_id': chat.id,
            'chat_name': get_chat_name(chat, current_user.id),  # Имя второго пользователя в чате
            'last_message': last_message.text if last_message else None,
            'timestamp': last_message.timestamp if last_message else None
        })

    # Если есть хотя бы один чат, выберем первый, чтобы сразу отобразить его
    default_chat_id = chat_data[0]['chat_id'] if chat_data else None

    return render_template("all_chats.html", chat_data=chat_data, default_chat_id=default_chat_id)


def get_chat_name(chat_id, current_user_id):
    db_sess = session.create_session()

    # Получаем пользователей, участвующих в чате
    chat = db_sess.query(Chat).filter(Chat.id == chat_id).first()

    if not chat:
        return None

    # Получаем пользователей, связанные с этим чатом
    user1 = db_sess.query(User).filter(User.id == chat.user1_id).first()
    user2 = db_sess.query(User).filter(User.id == chat.user2_id).first()

    # Проверяем, чей чат и на основе этого возвращаем имя
    if current_user_id == user1.id:
        return user2.name
    else:
        return user1.name


def get_last_message(chat_id):
    db_sess = session.create_session()

    # Получаем последнее сообщение в чате
    last_message = db_sess.query(Message).filter(Message.chat_id == chat_id) \
        .order_by(Message.timestamp.desc()).first()

    return last_message


def get_user_chats(user_id):
    db_sess = session.create_session()

    # Получаем все чаты, в которых участвует данный пользователь (user_id)
    participant_chats = db_sess.query(Chat).filter(
        (Chat.user1_id == user_id) | (Chat.user2_id == user_id)
    ).all()

    # Список для хранения информации о чатах
    chats = []

    # Проходим по каждому чату
    for chat in participant_chats:
        # Получаем ID другого участника чата
        other_user_id = chat.user2_id if chat.user1_id == user_id else chat.user1_id

        # Получаем данные другого участника
        other_user = db_sess.query(User).filter(User.id == other_user_id).first()

        # Получаем последнее сообщение в чате
        last_message = db_sess.query(Message).filter(Message.chat_id == chat.id).order_by(
            Message.timestamp.desc()).first()

        # Собираем данные о чате
        chats.append({
            'chat_id': chat.id,
            'chat_name': other_user.name,  # Имя второго участника чата
            'last_message': last_message.content if last_message else None,  # Последнее сообщение
            'timestamp': last_message.timestamp if last_message else None,  # Время последнего сообщения
            'message_type': last_message.message_type if last_message else None  # Тип последнего сообщения
        })

    return chats


@app.route("/chat/messages/<int:chat_id>", methods=["GET"])
@login_required
def chat_messages(chat_id):
    db_sess = session.create_session()
    messages = db_sess.query(Message).filter(Message.chat_id == chat_id).all()

    messages_data = [{
        'text': message.text,
        'type': 'sent' if message.sender_id == current_user.id else 'received'
    } for message in messages]

    # Получаем имя второго участника чата для отображения в заголовке
    chat_name = get_chat_name(chat_id, current_user.id)

    return jsonify({'messages': messages_data, 'chat_name': chat_name})


@app.route("/messages", methods=["GET"])
def get_messages():
    """Получение всех сообщений из БД"""
    db_sess = session.create_session()

    # Получаем все сообщения, сортируя по timestamp (от новых к старым)
    messages = db_sess.execute(
        sa.select(Message).order_by(Message.timestamp.asc())
    ).scalars().all()

    return jsonify([{
        "id": msg.id,
        "content": msg.content,
        "message_type": msg.message_type,
        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
    } for msg in messages])


@socketio.on("send_message")
def handle_message(data):
    """Обработка входящего сообщения и его сохранение в БД"""
    text = data.get("text", "")
    file_path = data.get("file_path", None)

    db_sess = session.create_session()
    message = Message(
        text=text,
        file_path=file_path,
        author_id=current_user.id  # Сохраняем ID пользователя
    )

    db_sess.add(message)
    db_sess.commit()

    emit("addMessageToChat", {
        "author": "0000",
        "id": message.id,
        "text": text
    }, broadcast=True)

    db_sess.close()


# Отправка сообщения
@app.route("/messages", methods=["POST"])
def send_message():
    data = request.json
    author_id = current_user.id
    recipient_id = data.get("recipient_id")  # ID получателя
    content = data.get("content", "")
    message_type = data.get("type", "text")

    chat_id = get_or_create_chat(author_id, recipient_id)

    db_sess = session.create_session()
    new_message = Message(
        chat_id=chat_id,
        author_id=author_id,
        content=content,
        message_type=message_type
    )
    db_sess.add(new_message)
    db_sess.commit()

    return jsonify({"status": "ok", "message": {
        "id": new_message.id,
        "chat_id": chat_id,
        "author_id": new_message.author_id,
        "content": new_message.content,
        "message_type": new_message.message_type
    }})


# Изменение сообщения
@app.route("/messages/<int:message_id>", methods=["PUT"])
def edit_message(message_id):
    """Обновление содержимого сообщения в БД"""
    data = request.json
    new_content = data.get("content")

    if not new_content:
        return jsonify({"status": "error", "message": "Content cannot be empty"}), 400

    # Открываем сессию
    db_sess = session.create_session()

    # Проверяем, существует ли сообщение
    message = db_sess.execute(
        sa.select(Message).where(Message.id == message_id)
    ).scalar()

    if not message:
        return jsonify({"status": "error", "message": "Message not found"}), 404

    # Обновляем содержимое сообщения
    message.content = new_content
    db_sess.commit()

    return jsonify({"status": "ok", "message": {"id": message_id, "content": new_content}})


# Удаление сообщения
@app.route("/messages/<int:message_id>", methods=["DELETE"])
def delete_message(message_id):
    # Открываем сессию
    db_sess = session.create_session()

    # Ищем сообщение в БД
    message = db_sess.execute(
        sa.select(Message).where(Message.id == message_id)
    ).scalar()
    if not message:
        return jsonify({"status": "error", "message": "Message not found"}), 404
    if message.author != current_user.id:
        return jsonify({"status": "error", "message": "Вы можете удалять только свои сообщения"}), 403
    # Если это файл или изображение — удаляем его из папки загрузок
    if message.message_type in ["file", "image"]:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], os.path.basename(message.content))
        if os.path.exists(file_path):
            os.remove(file_path)  # Удаляем файл

    # Удаляем сообщение из БД
    db_sess.delete(message)
    db_sess.commit()

    return jsonify({"status": "ok"})


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = file.filename
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if filename.lower().endswith(("png", "jpg", "jpeg", "webp")):
        ImageFile.LOAD_TRUNCATED_IMAGES = True  # Разрешаем загружать "битые" файлы
        img = Image.open(file.stream)
        img = img.convert("RGB")  # Конвертируем в RGB (если PNG, уберем альфа-канал)
        img.save(file_path, "JPEG", quality=70, icc_profile=None)  # Сохраняем с качеством 70% (можно менять)
    else:
        file.save(file_path)  # Просто сохраняем файл, если это не картинка

    # Отдаем URL файла для отображения
    file_url = f"http://127.0.0.1:5000/static/uploads/{filename}"
    return jsonify({"status": "ok", "file_url": file_url})


@app.route("/uploads/<filename>")
def get_uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


def get_or_create_chat(user1_id, user2_id):
    db_sess = session.create_session()
    chat = db_sess.execute(
        sa.select(Chat).where(
            ((Chat.user1_id == user1_id) & (Chat.user2_id == user2_id)) |
            ((Chat.user1_id == user2_id) & (Chat.user2_id == user1_id))
        )
    ).scalar()

    if not chat:
        chat = Chat(user1_id=user1_id, user2_id=user2_id)
        db_sess.add(chat)
        db_sess.commit()

    return chat.id


@app.route("/messages/<int:chat_id>", methods=["GET"])
def get_chat_messages(chat_id):
    db_sess = session.create_session()
    messages = db_sess.execute(
        sa.select(Message).where(Message.chat_id == chat_id).order_by(Message.timestamp.asc())
    ).scalars().all()

    return jsonify([{
        "id": msg.id,
        "author_id": msg.author_id,
        "content": msg.content,
        "message_type": msg.message_type,
        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
    } for msg in messages])


if __name__ == "__main__":
    main()
