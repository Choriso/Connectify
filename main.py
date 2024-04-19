from flask import Flask, render_template, redirect, request, make_response, session, abort
from data import session
from data.user import User
from data.interest import Interest
from forms.interest import InterestForm
from forms.user import RegisterForm, LoginForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
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
    # current_filter = input()
    db_sess = session.create_session()
    if current_user.is_authenticated:
        interests = db_sess.query(Interest)
        # if current_filter:
        #     interests = db_sess.query(Interest).filter(current_filter in Interest.tags)
    return render_template("index.html")


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db_sess = session.create_session()
    user = db_sess.query(User).get(current_user.id)
    interest = db_sess.query(Interest).filter(Interest.user == current_user)
    return render_template('profile.html', title='Профиль', interest=interest)


@app.route('/profile/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_profile(id):
    form = RegisterForm()
    if request.method == "GET":
        db_sess = session.create_session()
        user = db_sess.query(User).filter(User.id == id).first()
        if user:
            user.email.data = user.email
            form.password.data = user.password
            form.name.data = user.name
            form.information.data = user.information
            form.connection.data = user.connection
            form.image.data = user.image
            form.is_allow_gps = user.is_allow_gps
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = session.create_session()
        user = db_sess.query(Interest).filter(User.id == id).first()
        if user:
            user.email = user.email.data
            user.password = form.password.data
            user.name = form.name.data
            user.information = form.information.data
            user.connection = form.connection.data
            user.image = form.image.data
            user.is_allow_gps = form.is_allow_gps
            db_sess.commit()
            return redirect('/profile')
        else:
            abort(404)
    return render_template('register.html',
                           title='Редактирование интереса',
                           form=form
                           )


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
            is_allow_gps=form.is_allow_gps.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


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
@app.route('/interest',  methods=['GET', 'POST'])
@login_required
def add_interest():
    form = InterestForm()
    if form.validate_on_submit():
        db_sess = session.create_session()
        interest = Interest()
        interest.title = form.title.data
        interest.description = form.description.data
        current_user.interest.append(interest)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/index')
    return render_template('interest.html', title='Добавление интереса',
                           form=form)


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
    return redirect('/')


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


if __name__ == '__main__':
    main()
