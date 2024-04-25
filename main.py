import os

from flask import Flask, render_template, redirect, request, make_response, session, abort, url_for
from werkzeug.utils import secure_filename

from data import session
from data.user import User
from data.interest import Interest
from forms.interest import InterestForm
from forms.user import RegisterForm, LoginForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from get_similar import line_vector, cosdis

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


# загрузка пользователя
@login_manager.user_loader
def load_user(user_id):
    db_sess = session.create_session()
    return db_sess.query(User).get(user_id)


# запуск приложения
def main():
    session.global_init("db/blogs.db")
    app.run()


# главная страница
@app.route("/")
def index():
    db_sess = session.create_session()
    interest = db_sess.query(Interest)
    if current_user.is_authenticated:
        interest = db_sess.query(Interest)
    return render_template("index.html", interest=interest, current_user=current_user)


@app.route('/geolocation')
def geolocation():
    return render_template('geolocation_ip.html')


@app.route('/viewInteres', methods=['GET'])
def viewInteres():
    db_sess = session.create_session()
    interest = db_sess.query(Interest).filter(Interest.id == id).first()
    user = db_sess.query(User).get(interest.user_id).first()
    return render_template('view_interes.html', title="", interests=interest, user=user)

@app.route('/upload_render')
def upload_render():
    return render_template('upload_file.html')

@app.route('/upload', methods=['POST'])
def upload_file():
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
            image=form.image.data,
        )
        if form.validate_on_submit():
            f = form.image.data
            filename = secure_filename(user.image)
            f.save(os.path.join(app.instance_path, 'photos', filename))
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
        return render_template("index.html", interest=sorted_interests)


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
def edit_interests(id):
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
def interests_delete(id):
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


if __name__ == '__main__':
    main()
