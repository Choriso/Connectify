import datetime
import os
from flask_security import roles_accepted
from flask import Flask, render_template, redirect, request, make_response, session, abort, url_for
from werkzeug.utils import secure_filename
from data import session
from data.appelation import Appelation
from data.event import Event
from data.user import User
from data.interest import Interest
from data.report import Report
from forms.interest import InterestForm
from forms.report import ReportForm
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
    # event = db_sess.query(Interest)
    if current_user.is_authenticated:
        interest = db_sess.query(Interest).filter(Interest.user_id != current_user.id)[::-1]
        # event = db_sess.query(Interest).filter(Interest.user_id != current_user.id)[::-1]
    return render_template("index.html", interest=interest, current_user=current_user)


@app.route("/main_page")
def main_page():
    return render_template("main_page.html")


@app.route('/geolocation')
def geolocation():
    return render_template('geolocation_ip.html')


# # for teachers page
# @app.route('/admins')
# # only Admin can access the page
# @roles_accepted('Admin')
# def admins():
#     db_sess = session.create_session()
#     teachers = []
#     # query for role Teacher that is role_id=2
#     role_teachers = db_sess.query(roles_users).filter_by(role_id=2)
#     # query for the users' details using user_id
#     for teacher in role_teachers:
#         user = User.query.filter_by(id=teacher.user_id).first()
#         teachers.append(user)
#     # return the teachers list
#     return render_template("teachers.html", teachers=teachers)

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


'''



                                                        ПОЛЬЗОВАТЕЛИ



'''
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


@app.route('/process_profile', methods=['POST'])
def process_profile():
    db_sess = session.create_session()
    user = db_sess.get(User, current_user.id)
    user.name = request.args.get('name')
    user.information = request.args.get('information')
    user.connection = request.args.get('connection')
    db_sess.commit()
    return redirect('/profile')


@app.route('/viewProfile', methods=['GET'])
def viewProfile():
    user_id = request.args.get('user_id')

    db_sess = session.create_session()
    interest = db_sess.query(Interest).filter(Interest.user_id == user_id)
    user = db_sess.query(User).get(user_id)

    return render_template('view_profile.html', interest=interest, user=user)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db_sess = session.create_session()
    user = db_sess.query(User).get(current_user.id)
    interest = db_sess.query(Interest).filter(Interest.user == current_user)
    return render_template('profile.html', title='Профиль', interest=interest, current_user=current_user)


'''




                                                ИНТЕРЕСЫ




'''


@app.route('/viewInteres', methods=['GET'])
def viewInteres():
    user_id = request.args.get('user_id')
    interest_id = request.args.get('interest_id')

    db_sess = session.create_session()
    interest = db_sess.query(Interest).filter(Interest.id == interest_id).first()
    user = db_sess.query(User).get(user_id)
    print(1)
    return render_template('view_interes.html', title="", interests=interest, user=user)


# добавление интереса
@app.route('/interest', methods=['GET', 'POST'])
@login_required
def add_interests():
    print(2)
    return render_template('interest.html', title='Добавление интереса')


@app.route('/process_interest', methods=['POST'])
def process_interest():
    print(3)
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
    print(4)
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
    print(5)
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


'''



                                                  СОБЫТИЯ




'''


# страница событий
@app.route("/index_event")
def index_event():
    db_sess = session.create_session()
    events = db_sess.query(Event)
    return render_template("index_event.html", events=events, current_user=current_user)


@app.route('/viewEvent', methods=['GET'])
def viewEvent():
    user_id = request.args.get('user_id')
    event_id = request.args.get('event_id')
    db_sess = session.create_session()
    events = db_sess.query(Interest).filter(Interest.id == event_id).first()
    user = db_sess.query(User).get(user_id)
    return render_template('view_event.html', title="", events=events, user=user)


# добавление cобытия
@app.route('/event', methods=['GET', 'POST'])
@login_required
def add_events():
    return render_template('event.html', title='Добавление события')


@app.route('/process_event', methods=['POST'])
def process_event():
    title = request.form['title']
    description = request.form['description']
    date_begin = request.form['date_begin']
    date_end = request.form['date_end']
    place = request.form['place']
    print(title, description, date_begin, date_end, place)
    db_sess = session.create_session()
    event = Event()
    event.title = title
    event.description = description
    event.date_begin = date_begin
    event.date_end = date_end
    event.place = place
    current_user.events.append(event)
    db_sess.merge(current_user)
    db_sess.commit()
    return redirect('/index_event')


# # редактирование интереса
# @app.route('/interest/<int:id>', methods=['GET', 'POST'])
# @login_required
# def edit_interests(id):
#     form = InterestForm()
#     if request.method == "GET":
#         db_sess = session.create_session()
#         interest = db_sess.query(Interest).filter(Interest.id == id, Interest.user == current_user).first()
#         if interest:
#             form.title.data = interest.title
#             form.description.data = interest.description
#             form.tags.data = interest.tags
#         else:
#             abort(404)
#     if form.validate_on_submit():
#         db_sess = session.create_session()
#         interest = db_sess.query(Interest).filter(Interest.id == id, Interest.user == current_user).first()
#         if interest:
#             interest.title = form.title.data
#             interest.description = form.description.data
#             interest.tags = form.tags.data
#             db_sess.commit()
#             return redirect('/')
#         else:
#             abort(404)
#     return render_template('interest.html',
#                            title='Редактирование интереса',
#                            form=form
#                            )


@app.route('/event_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def events_delete(id):
    db_sess = session.create_session()
    event = db_sess.query(Event).filter(Event.id == id,
                                              Event.user == current_user
                                              ).first()
    if event:
        db_sess.delete(event)
        db_sess.commit()
    else:
        abort(404)
    previous_page = request.referrer
    if previous_page:
        return redirect(previous_page)
    else:
        return redirect(url_for('index_event'))


"""



                                                            ЖАЛОБЫ



"""

@app.route('/viewReportInteres', methods=['GET'])
def viewReportInteres():
    interest_id = request.args.get('interest_id')

    db_sess = session.create_session()
    interest = db_sess.query(Interest).filter(Interest.id == interest_id).first()
    print(1)
    return render_template('view_report_interest.html', title="", interests=interest)



# главная страница
@app.route("/admin")
def admin():
    db_sess = session.create_session()
    report = db_sess.query(Report)
    appelation = db_sess.query(Appelation)
    return render_template("admin.html", appelations=appelation, reports=report)


@app.route('/viewReport', methods=['GET'])
def viewreports():
    interest_id = request.args.get('interest_id')
    report_id = request.args.get('report_id')

    db_sess = session.create_session()
    report = db_sess.query(Report).filter(Report.id == report_id).first()
    interest = db_sess.query(Interest).get(interest_id)

    return render_template('view_reports.html', title="", reports=report, interest=interest)


# добавление жалобы
@app.route('/report', methods=['GET', 'POST'])
@login_required
def add_reports():
    print(1)
    global current_interest
    interest_id = request.args.get('interest_id')
    db_sess = session.create_session()
    current_interest = db_sess.query(Interest).get(interest_id)
    return render_template('report.html', title='Добавление жалобы')


@app.route('/process_report', methods=['POST'])
def process_report():
    print(2)
    title = request.form['title']
    description = request.form['description']
    print(title, description)
    db_sess = session.create_session()
    report = Report()
    report.title = title
    report.description = description
    current_interest.reports.append(report)
    db_sess.merge(current_interest)
    db_sess.commit()
    return redirect('/')


@app.route('/report_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def reports_delete(id):
    db_sess = session.create_session()
    report = db_sess.query(Report).filter(Report.id == id,
                                              Report.user == current_user
                                              ).first()
    if report:
        db_sess.delete(report)
        db_sess.commit()
    else:
        abort(404)
    previous_page = request.referrer
    if previous_page:
        return redirect(previous_page)
    else:
        return redirect(url_for('index'))

#
# '''
#
#
#
#                                                        АППЕЛЯЦИИ
#
#
#
# '''
#
#
# # добавление аппеляции
# @app.route('/appelation', methods=['GET', 'POST'])
# @login_required
# def add_interests():
#     return render_template('interest.html', title='Добавление интереса')
#
"""




                                                        CТАТИСТИКА
                                                        
                                                        
                                                        
                                                        
"""
if __name__ == '__main__':
    main()