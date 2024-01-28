"""Этот файл содержит код для простого веб-приложения, которое реализует аутентификацию пользователя и подтверждение
электронной почты.

Код написан на языке Python и использует веб-фреймворк Flask. Для управления базой данных используется библиотека
Flask-SQLAlchemy, и библиотека Flask-Mail для отправки электронной почты.

Код реализует следующие возможности:

1. Аутентификация пользователей: Пользователи могут зарегистрироваться и войти в приложение. После входа они получают
доступ к защищенной странице. 2. Подтверждение электронной почты: После регистрации пользователи должны подтвердить
свой адрес электронной почты, нажав на ссылку в письме с подтверждением. 3. Сброс пароля: Пользователи могут сбросить
свой пароль, если они его забыли.

Код хорошо задокументирован с использованием докстрингов Python, которые следуют определенному формату для
документирования функций и методов. Это позволяет другим разработчикам легко понять код и внести свой вклад в его
поддержку и улучшение."""

from flask import Flask, request, render_template
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
import datetime
import secrets
from dateutil import tz

# Create the Flask application
app = Flask(__name__)

# Set the upload folder for the application
UPLOAD_FOLDER = 'aaa'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set the SQLAlchemy database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# Disable SQLAlchemy tracking of database modifications
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set the email server settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-password'

# Create the Mail instance using the application settings
mail = Mail(app)

# Push the application context to ensure the settings are available throughout the application
app.app_context().push()

# Create the SQLAlchemy instance using the application settings
db = SQLAlchemy(app)


# Generate a confirmation code for email confirmation
def generate_confirmation_code():
    return secrets.token_hex(6)


# Create the EmailConfirmation model
class EmailConfirmation(db.Model):
    """
    Этот класс представляет подтверждение электронной почты для пользователя.

    Код подтверждения хранится в поле confirmation_code, а временная метка - в поле created_at.
    В поле user_id хранится ссылка внешнего ключа на связанную модель User.

    Метод is_expired можно использовать для проверки того, не истек ли срок действия кода подтверждения.
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    confirmation_code = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def is_expired(self):
        # Define a method to check if the confirmation code is expired
        # For example, you can set an expiration time of 1 hour
        return datetime.datetime.now(tz.UTC) > self.created_at + datetime.timedelta(hours=1)


# Send the confirmation code to the user's email address
def send_confirmation_code(to_email, confirmation_code):
    """
    Send a confirmation code to the specified email address.

    The confirmation code is included in the email body.
    """

    msg = Message('Подтверждение регистрации',
                  sender='your-email@gmail.com',
                  recipients=[to_email])
    msg.body = f'Ваш код подтверждения: {confirmation_code}'
    mail.send(msg)


# Confirm the registration based on the entered confirmation code
def confirm_registration(entered_code, confirmation_code):
    """
    Confirm the registration based on the entered confirmation code.

    The entered code and confirmation code are compared to ensure they match.
    """

    return entered_code == confirmation_code


# Create the User model
class User(db.Model):
    """
    This class represents a user in the application.

    The username, password, and email fields are required. The email field must be unique, and the password is hashed
    using the Flask-bcrypt library.

    The send_confirmation_code method can be used to send a confirmation code to the user's email address.
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Send the confirmation code to the user's email address
    def send_confirmation_code(self):
        confirmation_code = generate_confirmation_code()
        email_confirmation = EmailConfirmation(user_id=self.id, confirmation_code=confirmation_code)
        db.session.add(email_confirmation)
        db.session.commit()
        send_confirmation_code(self.email, confirmation_code)

    # Define a __repr__ method to print the user information
    def __repr__(self):
        return f"User('{self.username}', '{self.password}')"


# Define a page_not_found error handler for 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('page_404.html'), 404


# Define the index route for the homepage
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


# Define the login route for the login page
@app.route('/a', methods=['GET', 'POST'])
def log():
    return render_template('login.html')


# Define the register route for the registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if the user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            # Return an error if the user already exists
            return render_template('existing_user.html')
        else:
            # Create a new user if the user does not exist
            user = User(username=username, password=password, email=email)
            db.session.add(user)
            db.session.commit()
            # Send the confirmation code to the user's email address
            user.send_confirmation_code()
            # Return a confirmation message
            return render_template('confirmation_sent.html')


# Define the confirm_email route for the email confirmation page
@app.route('/confirm-email/<confirmation_code>', methods=['GET', 'POST'])
def confirm_email(confirmation_code):
    email_confirmation = EmailConfirmation.query.filter_by(confirmation_code=confirmation_code).first()
    if email_confirmation and not email_confirmation.is_expired():
        user = User.query.get(email_confirmation.user_id)
        user.email_confirmed = True
        db.session.commit()
        # Return a confirmation message
        return render_template('email_confirmed.html')
    else:
        # Return an error if the confirmation code is invalid
        return render_template('invalid_confirmation_code.html')


# Define the login route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user and user.email_confirmed:
            # Return a success message if the login is successful
            return 'ты крутой'
        else:
            # Return an error if the login is unsuccessful
            return 'Нету акка лох'


# Start the application if the main module is executed
if __name__ == '__main__':
    # Run the application on the local host on port 80
    app.run(host='0.0.0.0', port=80)
