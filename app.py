import os

from flask import redirect, make_response, session, abort, url_for, Flask, render_template, request, \
    send_from_directory, jsonify
from data.user import User
from data.interest import Interest
from data.message import Message
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

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat.db"
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
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


# главная страница
@app.route("/")
def index():
    db_sess = session.create_session()
    interest = db_sess.query(Interest)
    if current_user.is_authenticated:
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
@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        print("fgfgfgd")
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            information=form.information.data,
            connection=form.connection.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


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
        return redirect("/")
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
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


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
    return redirect('/')


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
            return redirect('/')
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


@app.route("/chat")
def chat():
    return render_template("chat.html")


@socketio.on("send_message")
def handle_message(data):
    """Обработка входящего сообщения и его сохранение в БД"""
    text = data.get("text", "")
    file_path = data.get("file_path", None)

    db_sess = session.create_session()
    message = Message(text=text, file_path=file_path)

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
    """Отправка нового сообщения в БД"""
    data = request.json
    author = data.get("author", "Аноним")
    content = data.get("content", "")
    file_url = data.get("file_url", None)
    message_type = data.get("type", "text")

    db_sess = session.create_session()

    # Создаём объект сообщения
    new_message = Message(
        author=author,
        content=content,
        file_url=file_url,
        message_type=message_type
    )

    # Добавляем в сессию и сохраняем в БД
    db_sess.add(new_message)
    db_sess.commit()

    return jsonify({"status": "ok", "message": {
        "id": new_message.id,
        "author": new_message.author,
        "content": new_message.content,
        "file_url": new_message.file_url,
        "message_type": new_message.message_type
    }})


@app.route("/messages", methods=["GET"])
def get_messages():
    """Получение всех сообщений из БД"""
    db_sess = session.create_session()

    # Получаем все сообщения, сортируя по timestamp (от новых к старым)
    messages = db_sess.execute(
        sa.select(Message).order_by(Message.timestamp.desc())
    ).scalars().all()

    return jsonify([{
        "id": msg.id,
        "content": msg.content,
        "message_type": msg.message_type,
        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
    } for msg in messages])


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


if __name__ == "__main__":
    main()
