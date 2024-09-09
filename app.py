from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, current_user

from utilis import activate_integration, auto_register_user
from extensions import db
from models import User
from payment import send_payment_webhook, refund_request

import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db.init_app(app)
with app.app_context():
    db.create_all()

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


PARTNER_TOKEN = os.getenv('PARTNER_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')

# # Модель пользователя
# class User(UserMixin, db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(150), unique=True, nullable=False)
#     password = db.Column(db.String(60), nullable=False)
#     robot_count = db.Column(db.Integer, default=0)  # Количество роботов

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Форма регистрации
class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

# Форма авторизации
class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')




# Главная страница
@app.route('/')
def home():
    robot_count = current_user.robot_count if current_user.is_authenticated else None
    return render_template('home.html', robot_count=robot_count)


# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    salon_ids = [request.args.get(f'salon_ids[{i}]') for i in range(len(request.args)) if f'salon_ids[{i}]' in request.args]
    if not salon_ids:
        salon_ids = request.args.get('salon_id', None)
        if salon_ids:
            salon_ids = [salon_ids]
    salon_ids = [int(x) for x in salon_ids] if salon_ids else []

    if current_user.is_authenticated:
        print(activate_integration(salon_ids))
        return redirect(url_for('home'))
    
    user = auto_register_user()
    if user:
        print(activate_integration(salon_ids))
        login_user(user)
        return redirect(url_for('home'))

    form = RegistrationForm()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(activate_integration(salon_ids))

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Ваш аккаунт был создан! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form, salon_id=salon_ids)

# Страница авторизации
@app.route('/login', methods=['GET', 'POST'])
def login():
    salon_id = request.args.get('salon_id')
    if current_user.is_authenticated:
        print(activate_integration(salon_id))

        return redirect(url_for('home'))
    form = LoginForm()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            print(activate_integration(salon_id))

            login_user(user)
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Не удалось войти. Пожалуйста, проверьте имя пользователя и пароль.', 'danger')
    return render_template('login.html', form=form)

# Выход из системы
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# Оплата
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        # Получаем значение salon_id из формы
        salon_id = request.form.get('salon_id')
        # Теперь вы можете обработать salon_id, например, вывести на экран
        print(send_payment_webhook(salon_id))
    return render_template('payment.html')

# Возврат
@app.route('/refund', methods=['GET', 'POST'])
def refund():
    if request.method == 'POST':
        # Получаем значение payment_id из формы
        payment_id = request.form.get('payment_id')
        # Вызываем функцию для обработки возврата (например, refund_request)
        print(refund_request(payment_id)) # Можно заменить это на вызов вашей логики refund_request
    # Возвращаем HTML-шаблон для отображения формы
    return render_template('refund.html')



@app.route('/marketplace_webhook', methods=['POST'])
def marketplace_webhook():
    # Получаем данные из запроса
    data = request.json

    # Проверяем наличие необходимых полей
    required_fields = ['salon_id', 'application_id', 'event', 'partner_token']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Обрабатываем событие
    salon_id = data['salon_id']
    application_id = data['application_id']
    event = data['event']
    partner_token = data['partner_token']

    # Проверяем тип события
    if event == "uninstall":
        # Логика обработки события отключения приложения
        print(f"Приложение с ID {application_id} было отключено в салоне с ID {salon_id}")
    elif event == "freeze":
        # Логика обработки события заморозки интеграции
        print(f"Интеграция приложения с ID {application_id} была заморожена в салоне с ID {salon_id}")
    else:
        return jsonify({"error": "Unknown event type"}), 400

    # Возвращаем успешный ответ
    return jsonify({"success": True}), 200


def create_user(username, password):
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return user

app.create_user = create_user



if __name__ == '__main__':
    app.run(debug=True)
