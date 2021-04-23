import logging
import os

from flask import Flask, render_template, redirect, abort, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from data import db_session
from data.posts import Post
from data.users import User
from forms.post_forms import AddNewPostForm
from forms.user_forms import RegisterForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '9CB2FA9ED59693626BC2'

login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/user_data.db")
    logging.basicConfig(
        filename='logs.log',
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        level=logging.INFO)

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


@app.route('/')
@app.route('/posts')
def index():
    # главная страница
    db_sess = db_session.create_session()
    users = db_sess.query(User)
    try:
        subscriptions_list = get_subscriptions_list()
        # список id пользователей на которых подписан текущий пользователь

        posts = db_sess.query(Post).order_by(-1 * Post.id).filter(
            (Post.creator.in_(subscriptions_list)) | (Post.creator == current_user.id))
        posts_for_template = []
        for post in posts:
            posts_for_template.append((post, os.path.exists(f'static/img/file_{post.id}.jpg'),
                                       f'file_{post.id}.jpg', current_user.id in (post.creator, 1, 2)))
        # print(posts_for_template)
        logging.debug(f'post request:{str(posts_for_template)}')
        if users.get(current_user.id).posts_liked:
            liked = list(map(int, users.get(current_user.id).posts_liked.split(", ")))
        else:
            liked = []
        # список нужных постов (те, у кого создатель - тот на кого подписан пользователь)
        return render_template("index.html", title='записи', posts=posts_for_template, usr=users, liked=liked,
                               other=False)

    except AttributeError:
        # если пользователь не зарегистрировани, то показываются все новости всех пользователей
        posts = db_sess.query(Post).order_by(-1 * Post.id).all()
        # список всех постов

        hello_text = open('README.txt', encoding='utf-8').read()
        posts_for_template = [
            (Post(text=hello_text, creator=2, likes=0, id=0, modified_date=''), True, 'file_0.jpg', False)]
        for post in posts:
            posts_for_template.append((post, os.path.exists(f'static/img/file_{post.id}.jpg'),
                                       f'file_{post.id}.jpg', False))
        # print(posts_for_template)
        liked = []
        return render_template("index.html", title='записи', posts=posts_for_template, usr=users, liked=liked,
                               other=False)


@app.route('/')
@app.route('/posts/<int:creator>')
@login_required
def users_posts(creator):
    # главная страница с записами только определённого пользователя
    db_sess = db_session.create_session()
    users = db_sess.query(User)

    posts = db_sess.query(Post).filter(Post.creator == creator)
    posts_for_template = []
    for post in posts:
        posts_for_template.append((post, os.path.exists(f'static/img/file_{post.id}.jpg'),
                                   f'file_{post.id}.jpg'))
    # print(posts_for_template)
    if users.get(current_user.id).posts_liked:
        liked = list(map(int, users.get(current_user.id).posts_liked.split(", ")))
    else:
        liked = []
    return render_template("index.html", title='записи', posts=posts_for_template, usr=users, liked=liked, other=True)


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
        logging.info(f'user with id {user.id} was registered')
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
            logging.info(f'user with id {user.id} authorised')
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
                    creator=current_user.id,
                    likes=0)

        if form.file.data:
            # если есть файл
            file = form.file.data

            # нахожу последний id
            if db_sess.query(Post).all():
                last_id = db_sess.query(Post).all()[-1].id
            else:
                last_id = 0
            # сохраниение фаила с именем "file_id записи к которой он отностися.jpg"
            file.save(f'static/img/file_{last_id + 1}.jpg')

        db_sess.add(post)
        db_sess.commit()
        logging.info(f'post with id {post.id} added')
        return redirect('/')
    return render_template('add_post.html', title='Добавление новой записи', form=form)


@app.route('/post_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def post_delete(id):
    db_sess = db_session.create_session()
    post = db_sess.query(Post).filter(Post.id == id).first()
    users = db_sess.query(User)
    if post:
        for user in users:
            if user.posts_liked is not None:
                liked = list(map(int, user.posts_liked.split(", ")))
            else:
                liked = []
            if id in liked:
                liked.remove(id)
            user.posts_liked = ", ".join(list(map(str, liked))) if liked else None
        db_sess.delete(post)
        try:
            os.remove(f'static/img/file_{post.id}.jpg')
        except FileNotFoundError:
            pass
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
    users = db_sess.query(User).filter(User.id.in_(subscriptions_list), User.id != current_user.id)
    # список нужных постов (те, у кого создатель - тот на кого подписан пользователь)
    return render_template("subscriptions_list.html", title='подписки', users=users, flag=0)


@app.route('/all_users')
@login_required
def all_users_list():
    # страница со списком других пользоветелей (посик новых подписок в сети)
    db_sess = db_session.create_session()

    subscriptions_list = get_subscriptions_list()
    # список id пользователей на которых подписан текущий пользователь

    users = db_sess.query(User).filter(User.id.notin_(subscriptions_list), User.id != current_user.id)
    # список нужных постов (те, у кого создатель - тот на кого не подписан пользователь)
    return render_template("subscriptions_list.html", title='подписки', users=users, flag=1)


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
    user.subscriptions = ', '.join(map(str, sorted(subscriptions_list)))
    db_sess.commit()
    return redirect("/all_users")


@app.route('/unsubscribe/<int:id>')
@login_required
def unsubscribe(id):
    db_sess = db_session.create_session()

    user = db_sess.query(User).get(current_user.id)
    # текущий пользователь
    subscriptions_list = get_subscriptions_list()
    # список id пользователей на которых подписан текущий пользователь
    if id in subscriptions_list:
        subscriptions_list.remove(id)
        # удаление id из списка
        user.subscriptions = ', '.join(map(str, subscriptions_list))
        logging.info(f'{user.id} subscroibed {id}')
        db_sess.commit()
        # запись изменнений в user и базу данных
        return redirect("/subscriptions")


@app.route('/add_like/<int:id>')
@login_required
def add_like(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(current_user.id)
    # текущий пользователь
    if user.posts_liked is not None:
        liked_by_user = list(map(int, user.posts_liked.split(', ')))
    else:
        liked_by_user = []
    if id not in liked_by_user:
        # если пользоваетель ещё не лайкнул запись:
        post = db_sess.query(Post).get(id)
        # пост с переданным id
        liked_by_user.append(id)
        # удаление id  в список
        user.posts_liked = ', '.join(map(str, sorted(liked_by_user)))

        post.likes += 1
        logging.info(f'add like post id: {post.id}; user id: {user.id}')
        db_sess.commit()
    return redirect(f"/#{id}")


@app.route('/delete_like/<int:id>')
@login_required
def delete_like(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(current_user.id)

    if user.posts_liked is not None:
        liked_by_user = list(map(int, user.posts_liked.split(', ')))
    else:
        liked_by_user = []

    if id in liked_by_user:
        # если пользоваетель лайкнул запись:
        post = db_sess.query(Post).get(id)
        # пост с переданным id
        liked_by_user.remove(id)
        # удаление id  в список
        if not liked_by_user:
            user.posts_liked = None
        else:
            user.posts_liked = ', '.join(map(str, sorted(liked_by_user)))
        post.likes -= 1
        logging.info(f'delete like post id: {post.id}; user id: {user.id}')
        db_sess.commit()
    return redirect(f"/#{id}")


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


@app.route('/favicon.ico')
def favicon():
    # иконка на вкладке
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'img/favicon.ico', mimetype='image/vnd.microsoft.icon')


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
