from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from flask_ngrok import run_with_ngrok

from data import db_session
from data.posts import Post
from data.users import User
from forms.post_forms import AddNewPostForm
from forms.user_forms import RegisterForm, LoginForm

import os

app = Flask(__name__)
run_with_ngrok(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/user_data.db")
    app.run()


@app.route('/')
@app.route('/posts')
def index():
    # главная страница
    try:
        db_sess = db_session.create_session()

        subscriptions_list = get_subscriptions_list()
        # список id пользователей на которых подписан текущий пользователь

        posts = db_sess.query(Post).filter(Post.creator.in_(subscriptions_list)) # .order_by(-1 * Post.id)
        posts_for_template = []
        for post in posts:
            posts_for_template.append((post, os.path.exists(f'db/users_content_data/file_{post.id}.jpg')))
            print(f'file_{post.id}.jpg')
        print(posts_for_template)
        # список нужных постов (те, у кого создатель - тот на кого подписан пользователь)

        return render_template("index.html", title='записи', posts=posts_for_template)

    except AttributeError:
        # если пользователь не зарегистрировани, то показываются все новости всех пользователей
        db_sess = db_session.create_session()

        posts = db_sess.query(Post).all() # .order_by(-1 * Post.id)
        posts_for_template = []
        for post in posts:
            posts_for_template.append((post, os.path.exists(f'db/users_content_data/file_{post.id}.jpg')))
            print(f'file_{post.id}.jpg')
        print(posts_for_template)
        # список всех постов
        return render_template("index.html", title='записи', posts=posts_for_template)


@app.route('/')
@app.route('/posts/<int:creator>')
def users_posts(creator):
    # главная страница с записами только определённого пользователя
    db_sess = db_session.create_session()

    posts = db_sess.query(Post).filter(Post.creator == creator)
    # список нужных постов (те, у кого создатель - переденный параметр)
    return render_template("index.html", title='записи', posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    # регистрация нового пользователя
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")

        user = User(name=form.name.data,
                    surname=form.surname.data,
                    email=form.email.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # авторизация пользователя
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    # добавление нового поста
    form = AddNewPostForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        # запсь в Post текста записи и создателя
        post = Post(text=form.text.data,
                    creator=current_user.id)

        if form.file.data:
            # если есть файл
            file = form.file.data

            # нахожу последний id
            if db_sess.query(Post).all():
                last_id = db_sess.query(Post).all()[-1].id
            else:
                last_id = 0
            # сохраниение фаила с именем "file_id записи к которой он отностися.jpg"
            file.save(f'db/users_content_data/file_{last_id + 1}.jpg')

        db_sess.add(post)
        db_sess.commit()
        return redirect('/')
    return render_template('add_post.html', title='Добавление новой записи', form=form)


@app.route('/post_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def post_delete(id):
    db_sess = db_session.create_session()
    post = db_sess.query(Post).filter(Post.id == id,
                                      ((Post.creator == current_user) | (current_user.id == 1))).first()
    if post:
        db_sess.delete(post)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/subscriptions')
@login_required
def subscriptions_list():
    # страница со списком подписок пользователя
    db_sess = db_session.create_session()

    subscriptions_list = get_subscriptions_list()
    # список id пользователей на которых подписан текущий пользователь

    users = db_sess.query(User).filter(User.id.in_(subscriptions_list))
    # список нужных постов (те, у кого создатель - тот на кого подписан пользователь)
    return render_template("subscriptions_list.html", title='подписки', users=users)


@app.route('/all_users')
@login_required
def all_users_list():
    # страница со списком других пользоветелей (посик новых подписок в сети)
    db_sess = db_session.create_session()

    subscriptions_list = get_subscriptions_list()
    # список id пользователей на которых подписан текущий пользователь

    users = db_sess.query(User).filter(User.id.notin_(subscriptions_list))
    # список нужных постов (те, у кого создатель - тот на кого не подписан пользователь)
    return render_template("subscriptions_list.html", title='подписки', users=users)


@app.route('/subscribe/<int:id>')
@login_required
def subscribe(id):
    db_sess = db_session.create_session()

    user = db_sess.query(User).get(current_user.id)
    # текущий пользователь
    subscriptions_list = get_subscriptions_list()
    # список id пользователей на которых подписан текущий пользователь
    subscriptions_list.append(id)
    # удаление id  в список
    user.subscribtions = ', '.join(sorted(subscriptions_list))
    db_sess.commit()
    # запись изменнений в user и базу данных

    # return redirect(/all_users)


@app.route('/unsubscribe/<int:id>')
@login_required
def unsubscribe(id):
    db_sess = db_session.create_session()

    user = db_sess.query(User).get(current_user.id)
    # текущий пользователь
    subscriptions_list = get_subscriptions_list()
    # список id пользователей на которых подписан текущий пользователь

    subscriptions_list.remove(id)
    # удаление id из списка
    user.subscribtions = ', '.join(subscriptions_list)
    db_sess.commit()
    # запись изменнений в user и базу данных

    # return redirect(/subscriptions)


@app.route('/confirm_logout')
@login_required
def confirm_logout():
    return render_template('confirm_logout.html', title='Подтверждение выхода')


@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


def get_subscriptions_list():
    # получение списка подписок текущего пользователя
    db_sess = db_session.create_session()

    user = db_sess.query(User).get(current_user.id)
    # print(user.name, user.surname, user.id)
    # текущий пользователь
    if user.subscriptions:
        # если есть подписки:
        subscriptions = list(map(int, user.subscriptions.split(',')))
    else:
        subscriptions = []
    # список id пользователей на которых подписан текущий пользователь

    return subscriptions


if __name__ == '__main__':
    main()
