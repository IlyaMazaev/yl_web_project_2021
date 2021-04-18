from flask import Flask, render_template, redirect, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from flask_ngrok import run_with_ngrok

from data import db_session
from data.posts import Post
from data.users import User
from forms.post_forms import AddNewPostForm
from forms.user_forms import RegisterForm, LoginForm

app = Flask(__name__)
run_with_ngrok(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/user_data.db")
    app.run()


@app.route('/')
@app.route('/index')
def index():
    # главная страница
    db_sess = db_session.create_session()

    subscriptions = list(map(int(current_user.subscriptions.split(','))))
    # список id пользователей на которых подписан текущий пользователь

    posts = db_sess.query(Post).filter(Post.creator in subscriptions)
    # список нужных постов (те, у кого создатель - тот на кого подписан пользователь)
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


@app.route('/addpost', methods=['GET', 'POST'])
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
            # если прикреплён фаил:
            file_data = request.FILES[form.file.name].read()
            # читаем данные фаила
            open(f'db/users_content_data/file_{post.id}.{form.file.name.split(".")[-1]}', 'w').write(file_data)
            # запись фаила в папке db/users_content_data c именем file_id поста к которому
            # относится запись и расширение исходного фила

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


@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


if __name__ == '__main__':
    main()
