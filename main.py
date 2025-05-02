import sqlalchemy
from flask import Flask, request, render_template, redirect
from globals import *
from flask_simple_captcha import CAPTCHA
from data import db_session
from data.users import User
from data.offers import Offer
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from datetime import datetime
import json
from consts import Constants

bd_password = Constants.BD_PASS

app = Flask(__name__)
app.config['SECRET_KEY'] = Constants.SECRET_KEY
app.jinja_env.globals['consts'] = Naming

db_session.global_init(f"h4cker3:{bd_password}")

login_manager = LoginManager()
login_manager.init_app(app)

YOUR_CONFIG = {
    'SECRET_CAPTCHA_KEY': Constants.SECRET_CAPTHCA_KEY,
    'CAPTCHA_LENGTH': 5,
    'CAPTCHA_DIGITS': False,
    'EXPIRE_SECONDS': 600,
}
SIMPLE_CAPTCHA = CAPTCHA(config=YOUR_CONFIG)
app = SIMPLE_CAPTCHA.init_app(app)

ROUND = 1


def get_fio_name(id, db_sess):
    usr = db_sess.query(User).filter(User.id == id).first()
    if not usr:
        return "Удаленный пользователь"
    return usr.fio


@app.errorhandler(500)
def error500(e):
    return f"База данных перезагружается. Перезапустите страницу и проблема решится сама :)", 500


@app.route("/")
@app.route("/index")
def index():
    db_sess = db_session.create_session()
    users_db = db_sess.query(User).filter(User.role == UserType.default).all()
    users = []
    for user in users_db:
        st = {'name': user.fio,
              'balance': user.balance,
              'id': user.id
              }
        users.append(st)
    users.sort(key=lambda x: x['balance'], reverse=True)
    if len(users) > 15:
        users = users[:15]
    if len(users) > 0:
        users[0]['name'] = "👑 " + users[0]['name'] + " 👑"
    db_sess.close()
    can = False
    if current_user.is_authenticated:
        can = current_user.role in UserType.level1
    global ROUND
    if ROUND != 0:
        return render_template("index.html",
                               text=f"Таблица лидеров закрыта до аукциона", users=users, can=can)
    else:
        return render_template("index.html", text="Скоро стартуем!", users=users, can=can)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    usr = db_sess.query(User).get(user_id)
    db_sess.close()
    return usr


@app.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        logout_user()
        return redirect("/")



@login_required
@app.route("/user", methods=['GET'])
def user_local_page():
    user = current_user
    role = "низкий (пользователь)"
    can = False
    if user.role in UserType.level1:
        role = "средний (модератор)"
        can = True
    if user.role in UserType.level2:
        role = "высокий (админ)"
        can = True
    trns = []
    db_sess = db_session.create_session()
    trns_db = db_sess.query(Transaction).filter(Transaction.income == current_user.id).all()
    for e in trns_db:
        trd = {"in": get_fio_name(e.income, db_sess) + f" ({e.income})",
               "out": get_fio_name(e.outcome, db_sess) + f" ({e.outcome})",
               "amount": e.count,
               "id": e.id,
               "reason": reason_return(e.type)}
        trns.append(trd)
    trns_db = db_sess.query(Transaction).filter(Transaction.outcome == current_user.id).all()
    for e in trns_db:
        trd = {"in": get_fio_name(e.income, db_sess) + f" ({e.income})",
               "out": get_fio_name(e.outcome, db_sess) + f" ({e.outcome})",
               "amount": e.count,
               "id": e.id,
               "reason": reason_return(e.type)}
        trns.append(trd)
    trns.sort(key=lambda x: x["id"], reverse=True)
    if len(trns) > 20:
        trns = trns[:20]
    res = {"name": user.fio,
           "id": user.id,
           "balance": user.balance,
           "role": role,
           "trns": trns
           }
    return render_template('user.html', res=res, can=can)

@login_required
@app.route("/user/<int:id>", methods=['POST', 'GET'])
def user_page_edit(id: int):
    if not current_user.is_authenticated:
        return redirect("/")
    if request.method == 'GET':
        db_sess = db_session.create_session()
        if current_user.role not in UserType.level1:
            db_sess.close()
            return "<h1>Доступ запрещен!</h1>"
        can = current_user.role in UserType.level2
        ans = db_sess.query(User).filter(User.id == id).all()
        if len(ans) == 0:
            db_sess.close()
            return "Такого пользователя не существует!"
        user = ans[0]
        trns = []
        trns_db = db_sess.query(Transaction).filter(Transaction.income == id).all()
        for e in trns_db:
            trd = {"in": get_fio_name(e.income, db_sess) + f" ({e.income})",
                   "out": get_fio_name(e.outcome, db_sess) + f" ({e.outcome})",
                   "amount": e.count,
                   "id": e.id,
                   "reason": reason_return(e.type)}
            trns.append(trd)
        trns_db = db_sess.query(Transaction).filter(Transaction.outcome == id).all()
        for e in trns_db:
            trd = {"in": get_fio_name(e.income, db_sess) + f" ({e.income})",
                   "out": get_fio_name(e.outcome, db_sess) + f" ({e.outcome})",
                   "amount": e.count,
                   "id": e.id,
                   "reason": reason_return(e.type)}
            trns.append(trd)
        trns.sort(key=lambda x: x["id"], reverse=True)
        res = {"name": user.fio,
               "id": user.id,
               "role": user.role,
               "clss": user.clss,
               "balance": user.balance,
               "trns": trns}
        db_sess.close()
        return render_template("user_mod.html", res=res, can=can)
    elif request.method == 'POST':
        if current_user.role not in UserType.level2:
            return "<h1>Доступ запрещен!</h1>"
        db_sess = db_session.create_session()
        ans = db_sess.query(User).filter(User.id == id).all()
        if len(ans) == 0:
            return "Такого пользователя не существует!"
        user = ans[0]
        mode = int(request.form.get('mode').split()[0][1:-1])
        if mode == 1:
            user.role = UserType.moderator
        elif mode == 2:
            user.role = UserType.user
        elif mode == 3:
            db_sess.delete(user)
        db_sess.commit()
        db_sess.close()
        return redirect("/user")


@app.route("/login", methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_post():
    # login code goes here
    login = request.form.get('login').lower()
    password = request.form.get('password')

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.login == login).first()
    db_sess.close()
    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not user.password == password:
        return redirect("/login")  # if the user doesn't exist or password is wrong, reload the page
    login_user(user)
    # if the above check passes, then we know the user has the right credentials
    return redirect('/user')


@app.route("/register", methods=['GET'])
def register():
    new_captcha_dict = SIMPLE_CAPTCHA.create()
    return render_template('register.html', captcha=new_captcha_dict)


@app.route('/register', methods=['POST'])
def register_post():
    # login code goes here
    login = request.form.get('login').lower()
    fio = request.form.get('fio')
    clss = request.form.get('clss')
    password = request.form.get('password')
    c_hash = request.form.get('captcha-hash')
    c_text = request.form.get('captcha-text')
    if not SIMPLE_CAPTCHA.verify(c_text, c_hash):
        new_captcha_dict = SIMPLE_CAPTCHA.create()
        return render_template('register.html', message='Неверно решена Captcha!', captcha=new_captcha_dict)
    if not check_for_banned(fio):
        new_captcha_dict = SIMPLE_CAPTCHA.create()
        return render_template('register.html', message='Нельзя использовать такое ФИО :)', captcha=new_captcha_dict)
    if len(clss) > 3 or len(clss) < 2:
        new_captcha_dict = SIMPLE_CAPTCHA.create()
        return render_template('register.html', message='Несуществующий класс', captcha=new_captcha_dict)
    if len(fio) < 3 or len(fio) > 100:
        new_captcha_dict = SIMPLE_CAPTCHA.create()
        return render_template('register.html', message='Слишком короткое ФИО!', captcha=new_captcha_dict)
    if len(login) < 5 or len(login) > 30:
        new_captcha_dict = SIMPLE_CAPTCHA.create()
        return render_template('register.html', message='Слишком короткий логин!', captcha=new_captcha_dict)
    if len(password) < 5 or len(password) > 100:
        new_captcha_dict = SIMPLE_CAPTCHA.create()
        return render_template('register.html', message='Слишком короткий пароль!', captcha=new_captcha_dict)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.login == login).first()
    db_sess.close()
    if user:
        new_captcha_dict = SIMPLE_CAPTCHA.create()
        return render_template('register.html', message='Пользователь с таким логином уже есть!',
                               captcha=new_captcha_dict)
    db_sess = db_session.create_session()
    new_user = User()
    new_user.login = login
    new_user.password = password
    new_user.clss = clss
    new_user.fio = fio
    db_sess.add(new_user)
    db_sess.commit()
    login_user(new_user)
    db_sess.close()
    # if the above check passes, then we know the user has the right credentials
    return redirect('/user')


@app.route("/transfer", methods=['GET'])
def transfer():
    if not current_user.is_authenticated:
        return redirect("/")
    new_captcha_dict = SIMPLE_CAPTCHA.create()
    return render_template('transfer.html', captcha=new_captcha_dict)


@app.route('/transfer', methods=['POST'])
def transfer_post():
    if not current_user.is_authenticated:
        return redirect("/")
    id_income = request.form.get('id_income')
    amount = request.form.get('amount')
    c_hash = request.form.get('captcha-hash')
    c_text = request.form.get('captcha-text')
    if not SIMPLE_CAPTCHA.verify(c_text, c_hash):
        new_captcha_dict = SIMPLE_CAPTCHA.create()
        return render_template('transfer.html', message='Неверно решена Captcha!', captcha=new_captcha_dict)
    if not amount.isnumeric() or int(amount) <= 0:
        new_captcha_dict = SIMPLE_CAPTCHA.create()
        return render_template('transfer.html', message='Неправильная сумма перевода', captcha=new_captcha_dict)
    amount = int(amount)
    if amount > current_user.balance:
        new_captcha_dict = SIMPLE_CAPTCHA.create()
        return render_template('transfer.html', message='Недостаточно средств', captcha=new_captcha_dict)
    if id_income == current_user.id:
        new_captcha_dict = SIMPLE_CAPTCHA.create()
        return render_template('transfer.html', message='Нельзя перевести себе!', captcha=new_captcha_dict)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id_income).first()
    if not user:
        db_sess.close()
        new_captcha_dict = SIMPLE_CAPTCHA.create()
        return render_template('transfer.html', message='Не существует пользователя с таким ID', captcha=new_captcha_dict)
    user.balance += amount
    cr_user = db_sess.query(User).filter(User.id == current_user.id).first()
    if not cr_user:
        db_sess.close()
        return redirect('/')
    cr_user.balance -= amount
    login_user(cr_user)
    tr = Transaction()
    tr.income = cr_user.id
    tr.outcome = user.id
    tr.count = amount
    tr.type = TransactionType.goto
    db_sess.add(tr)
    db_sess.commit()
    db_sess.close()
    return redirect('/transfer')


@app.route("/mod", methods=['GET'])
def moderator():
    if not current_user.is_authenticated:
        return redirect("/")
    db_sess = db_session.create_session()
    cr_user = db_sess.query(User).filter(User.id == current_user.id).first()
    if not cr_user:
        db_sess.close()
        return redirect('/')
    if cr_user.role not in UserType.level1:
        db_sess.close()
        return redirect('/')
    login_user(cr_user)
    db_sess.close()
    return render_template('moderator_panel.html')


@app.route('/mod', methods=['POST'])
def moderator_post():
    if not current_user.is_authenticated:
        return redirect("/")
    db_sess = db_session.create_session()
    cr_user = db_sess.query(User).filter(User.id == current_user.id).first()
    if not cr_user:
        db_sess.close()
        return redirect('/')
    if cr_user.role not in UserType.level1:
        db_sess.close()
        return redirect('/')
    login_user(cr_user)
    db_sess.close()
    id_user = int(request.form.get('id'))
    amount = int(request.form.get('amount'))
    if id_user < 0:
        return render_template('moderator_panel.html', message='Отрицательное ID!', alert=True)
    if amount == 0:
        return render_template('moderator_panel.html', message='Нулевая сумма перевода!', alert=True)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id_user).first()
    if not user:
        db_sess.close()
        return render_template('moderator_panel.html', message='Не существует пользователя с таким ID', alert=True)
    user.balance += amount
    tr = Transaction()
    tr.income = cr_user.id
    tr.outcome = user.id
    tr.count = amount
    tr.type = TransactionType.check
    db_sess.add(tr)
    db_sess.commit()
    db_sess.close()
    return render_template('moderator_panel.html', message='Успешно выполнено!')


@app.route("/qwerty", methods=['GET'])
def qwerty():
    if not current_user.is_authenticated:
        return redirect("/")
    db_sess = db_session.create_session()
    cr_user = db_sess.query(User).filter(User.id == current_user.id).first()
    if not cr_user:
        db_sess.close()
        return redirect('/')
    if cr_user.role not in UserType.level2:
        db_sess.close()
        return redirect('/')
    login_user(cr_user)
    db_sess.close()
    return render_template('qwerty.html')


@app.route('/qwerty', methods=['POST'])
def qwerty_post():
    if not current_user.is_authenticated:
        return redirect("/")
    db_sess = db_session.create_session()
    cr_user = db_sess.query(User).filter(User.id == current_user.id).first()
    if not cr_user:
        db_sess.close()
        return redirect('/')
    if cr_user.role not in UserType.level2:
        db_sess.close()
        return redirect('/')
    login_user(cr_user)
    db_sess.close()
    quest = request.form.get('quest')
    answered = request.form.get("answered")
    db_sess = db_session.create_session()
    answer = db_sess.execute(sqlalchemy.text(quest))
    db_sess.commit()
    db_sess.close()
    if answered:
        rows = answer.fetchall()
        res = {}
        res['body'] = []
        res['head'] = answer.keys()
        for ts in rows:
            res['body'].append(ts)
        return render_template('qwerty.html', res=res)
    return render_template('qwerty.html')


def main():
    app.run()


if __name__ == '__main__':
    main()
