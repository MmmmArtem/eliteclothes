import base64
from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, SelectField, FileField
from wtforms.validators import DataRequired
from data import db_session, users
from data.products import Categories, Products
from data.users import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
db_session.global_init("db/shop.sqlite")
session = db_session.create_session()
login_manager = LoginManager()
login_manager.init_app(app)
current_shop_page = ""
basket = []


@login_manager.user_loader
def load_user(user_id):
    return session.query(users.User).get(user_id)


class Product2:
    pass


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/shop/', defaults={'category': 1})
@app.route('/shop/<int:category>')
def return_shop_page(category):
    global current_shop_page
    current_shop_page = "/shop/" + str(category)
    user = {'username': 'Test'}
    cats = session.query(Categories)
    catw = 100 / cats.count()
    products = session.query(Products).filter(Products.cat_id == category)
    products2 = []
    i = 0
    for product in products:
        product2 = Product2()
        product2.id = product.id
        product2.index = i
        product2.title = product.title
        product2.content = product.content
        product2.price = product.price
        if product.image:
            product2.image = base64.b64encode(product.image).decode('ascii')
        products2.append(product2)
        i = i + 1
    while i % 6 != 0:
        product2 = Product2()
        product2.index = i
        product2.title = 'none'
        products2.append(product2)
        i = i + 1
    return render_template('shop.html', title='Home', basket_len=len(basket), user=user,
                           cat_id=category, cats=cats, catw=catw, products=products2)


class AddCatForm(FlaskForm):
    cat_title = StringField("Название", validators=[DataRequired()])
    submit = SubmitField('Сохранить')


@app.route('/addcat', methods=['GET', 'POST'])
def return_addcat_page():
    form = AddCatForm(request.form)
    if form.is_submitted():
        cat = Categories()
        cat.title = form.cat_title.data
        session.add(cat)
        session.commit()
        return redirect('/shop')
    return render_template('addcat.html', basket_len=len(basket), form=form)


class AddProdForm(FlaskForm):
    prod_title = StringField("Название", validators=[DataRequired()])
    prod_content = StringField('Описание')
    price = StringField('Цена')
    cat = SelectField("Категория")
    image = FileField("Выберите изображение")
    submit = SubmitField('Сохранить')


@app.route('/addprod', methods=['GET', 'POST'])
def return_addprod_page():
    form = AddProdForm(request.form)
    form.cat.choices = [(cat.id, cat.title) for cat in session.query(Categories)]
    if request.method == 'POST':
        product = Products()
        product.title = form.prod_title.data
        product.content = form.prod_content.data
        product.price = form.price.data
        product.cat_id = form.cat.data
        f = request.files['image_file']
        product.image = f.read()
        session.add(product)
        session.commit()
        return redirect('/shop')
    return render_template('addprod.html', basket_len=len(basket), form=form)


@app.route('/delcat/<int:cat_id>')
def return_delcat_page(cat_id):
    cat = session.query(Categories).filter(Categories.id == cat_id).first()
    session.delete(cat)
    session.commit()
    global current_shop_page
    return redirect('/shop')


@app.route('/delprod/<int:prod_id>')
def return_delprod_page(prod_id):
    product = session.query(Products).filter(Products.id == prod_id).first()
    session.delete(product)
    session.commit()
    global current_shop_page
    return redirect(current_shop_page)


@app.route('/buy/<int:prod_id>')
def return_buy_page(prod_id):
    basket.append(prod_id)
    global current_shop_page
    return redirect(current_shop_page)


@app.route('/basket')
def return_basket_page():
    cats = session.query(Categories)
    products = session.query(Products)
    products2 = []
    i = 0
    full_price = 0
    for product_id in basket:
        product = products.get(product_id)
        if product:
            product2 = Product2()
            product2.id = product.id
            cat = cats.get(product.cat_id)
            if cat:
                product2.category = cat.title
            product2.index = i
            product2.title = product.title
            product2.content = product.content
            product2.price = product.price
            if product.image:
                product2.image = base64.b64encode(product.image).decode('ascii')
            if product2.price:
                full_price += product2.price
            products2.append(product2)
            i = i + 1
    return render_template('basket.html', basket_len=len(basket), products=products2, full_price=full_price)


@app.route('/payment')
def return_payment_page():
    return render_template('payment.html')


class RegisterForm(FlaskForm):
    email = StringField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    submit = SubmitField('Войти')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        if session.query(users.User).filter(users.User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if "Админ" == form.email.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message='Нельзя выбрать имя "Админ"')
        user = User()
        user.name = form.name.data
        user.email = form.email.data
        user.about = form.about.data
        user.hashed_password = form.password.data
        #        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


class LoginForm(FlaskForm):
    email = StringField("Почта", validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = session.query(users.User).filter(users.User.email == form.email.data).first()
        if user and user.hashed_password == form.password.data:
            login_user(user, remember=form.remember_me.data)
            global basket
            basket = []
            return redirect('/shop')
        return render_template('login.html', message='Неправильный логин или пароль', form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/shop')


if __name__ == '__main__':
    app.run()
