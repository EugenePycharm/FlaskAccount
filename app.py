import secrets
from datetime import datetime, timedelta, timezone
from flask import Flask, request, render_template, redirect, url_for
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy

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
app.config['MAIL_USERNAME'] = 'rprocess58@gmail.com'
app.config['MAIL_PASSWORD'] = 'adxj cpnb fnua lwaq'

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
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    confirmation_code = db.Column(db.String(120), nullable=False, unique=True)




# Send the confirmation code to the user's email address
def send_confirmation_code(to_email, confirmation_code):
    """
    Отправка кода подтверждения на указанный адрес электронной почты.

    Код подтверждения включается в тело письма.
    """

    msg = Message('Подтверждение регистрации',
                  sender='your-email@gmail.com',
                  recipients=[to_email])
    msg.body = f'Ваш код подтверждения: {confirmation_code}'
    mail.send(msg)


# Confirm the registration based on the entered confirmation code
def confirm_registration(entered_code, confirmation_code):
    return entered_code == confirmation_code


# Create the User model
class User(db.Model):
    """
    Этот класс представляет пользователя в приложении.

    Поля имени пользователя, пароля и электронной почты являются обязательными. Поле электронной почты должно быть
    уникальным, а пароль хэшируется с помощью библиотеки Flask-bcrypt.

    Метод send_confirmation_code можно использовать для отправки кода подтверждения на адрес электронной почты
    пользователя.
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
        return f"User('{self.username}', '{self.password}', {self.email})"


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


# ...

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
            confirmation_code = generate_confirmation_code()
            email_confirmation = EmailConfirmation(user_id=user.id, confirmation_code=confirmation_code)
            db.session.add(email_confirmation)
            db.session.commit()
            send_confirmation_code(user.email, confirmation_code)
            # Redirect to the confirm_email page with the confirmation code
            return redirect(url_for('confirm_email', confirmation_code=email_confirmation.confirmation_code))


# Define the confirm_email route for the email confirmation pa

@app.route('/confirm-email/<confirmation_code>', methods=['GET', 'POST'])
def confirm_email(confirmation_code):
    email_confirmation = EmailConfirmation.query.filter_by(confirmation_code=confirmation_code).first()
    if email_confirmation:
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
