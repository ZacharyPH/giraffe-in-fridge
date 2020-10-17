from flask_login import LoginManager, login_user, current_user, login_required, logout_user, UserMixin
from flask import Flask,jsonify,request,render_template,Response,flash,redirect,url_for
from flask_restless import APIManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_wtf import Form
from wtforms import TextField, BooleanField, validators, PasswordField, SubmitField, SelectField, FileField, \
	SelectMultipleField, BooleanField, DateTimeField, TextAreaField
from werkzeug.security import generate_password_hash, \
	 check_password_hash
import datetime
from sqlalchemy import create_engine
#from wtforms.validators import Required
from werkzeug.utils import secure_filename
import os
import uuid

from flask_mail import Mail, Message

import smtplib
import string

from decimal import *

app = Flask(__name__)

DATABASE_PATH = 'sqlite:///database/venmodata.db'

UPLOAD_FOLDER = '/static/images'
# only allow images to be uploaded
ALLOWED_EXTENSIONS = set(['csv'])
def allowed_file(filename):
	return '.' in filename and \
		   filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)

# app.config.update(dict(
# 	DEBUG = True,
# 	MAIL_SERVER = 'smtp.gmail.com',
# 	MAIL_PORT = 587,
# 	MAIL_USE_TLS = True,
# 	MAIL_USE_SSL = False,
# 	MAIL_USERNAME = 'asikerd@gmail.com',
# 	MAIL_PASSWORD = 'CheesePuppy',
# ))

db = SQLAlchemy(app)
# mail = Mail(app)

app.config.update(dict(
	SECRET_KEY="powerful secretkey",
	WTF_CSRF_SECRET_KEY="a csrf secret key"
))

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_PATH
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

e = create_engine(DATABASE_PATH)

login_manager = LoginManager()

COMPANY = {
	'name': 'Giraffe in Fridge',
	'motto': 'GIF is pronounced with a hard G.',
	'initials': 'GIF'
}


@login_manager.user_loader
def get_user(ident):
	return User.query.get(int(ident))

class User(db.Model, UserMixin):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(32))
	firstname = db.Column(db.String(32))
	lastname = db.Column(db.String(32))
	email = db.Column(db.String(32))
	password = db.Column(db.String(32))

	def __init__(self, username, firstname, lastname, email, password):
		self.username = username
		self.set_password(password)
		self.email = email
		self.firstname = firstname
		self.lastname = lastname

	def set_password(self, password):
		self.password = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password, password)
		#return password == self.password

class VenmoData(db.Model):
	__tablename__ = 'venmodata'
	id = db.Column(db.Integer, primary_key=True)
	

class LoginForm(Form):
	username = TextField('Username', [validators.Required()])
	password = PasswordField('Password', [validators.Required()])
	submit = SubmitField('Log In')

	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
		self.user = None

	def validate(self):
		user = User.query.filter_by(
			username=self.username.data).first()
		if user is None:
			self.password.errors = ['Invalid username or password']
			return False

		if not user.check_password(self.password.data):
			self.password.errors = ['Invalid username or password']
			return False

		self.user = user
		login_user(user)
		return True

class RegisterForm(Form):
	username = TextField('Username', validators=[validators.Required()])
	email = TextField('E-Mail', validators=[validators.Required(), validators.Email()])
	password = PasswordField('Password', [
		validators.Required(),
		validators.EqualTo('confirm', message='Passwords must match')
	])
	confirm = PasswordField('Repeat Password')
	firstname = TextField('First Name', validators=[validators.Required(), validators.Length(min=8, max=32, message="Password must be between 8 and 32 characters long")])
	lastname = TextField('Last Name', validators=[validators.Required()])
	submit = SubmitField('Register Now')

	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)

	def validate(self):
		if self.username.data and self.password.data and self.confirm.data:
			if User.query.filter_by(username=self.username.data).first():
				flash('An account with that username already exists.', category='red')
				return False
			if User.query.filter_by(email=self.email.data).first():
				flash('An account with that email already exists.', category='red')
				return False
			return True
		return False

@app.route('/', methods=['GET', 'POST'])
def home():
	form = RegisterForm()
	if form.validate_on_submit():
		if form.validate():
			user = User(form.username.data, form.firstname.data, form.lastname.data, form.email.data, form.password.data)
			db.session.add(user)
			db.session.commit()
			flash("You're now registered!", category='green')
			return redirect('/login')
		else:
			flash("Error: Check your inputs", category='red')
	return render_template('index.html', company=COMPANY, form=form)

@app.route('/login', methods=['GET', 'POST'])
def admin_login():
	form = LoginForm()
	if form.validate_on_submit():
		if form.validate():
			flash("You're now logged in!", category='green')
			return redirect('/dashboard')
		else:
			flash("No user with that email/password combo", category='red')
	return render_template('login.html', form=form, company=COMPANY)

@app.route('/admin', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		if form.validate():
			flash("You're now logged in!", category='green')
			return redirect('/dashboard')
		else:
			flash("No user with that email/password combo", category='red')
	return render_template('login.html', form=form, company=COMPANY)

@app.route('/uploadcsv', methods=['POST'])
def upload_file():
	# check if the post request has the file part
	if 'file' not in request.files:
		flash('No file part')
		return redirect(request.url)
	file = request.files['file']
	# if user does not select file, browser also
	# submit an empty part without filename
	if file.filename == '':
		flash('No selected file')
		return redirect(request.url)
	if file and allowed_file(file.filename):
		filename = secure_filename(file.filename)
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		return redirect(url_for('uploaded_file', filename=filename))
	return redirect(request.url)

@app.route('/dashboard')
@login_required
def dashboard():
	return render_template('dashboard.html', company=COMPANY)

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect('/')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	form = RegisterForm()
	if form.validate_on_submit():
		if form.validate():
			user = User(form.username.data, form.firstname.data, form.lastname.data, form.email.data, form.password.data)
			db.session.add(user)
			db.session.commit()
			flash("You're now registered!", category='green')
			return redirect('/login')
		else:
			flash("Error: Check your inputs", category='red')
	return render_template('register.html', form=form, company=COMPANY)

@app.route('/about')
def about():
	return render_template('about.html', company=COMPANY)

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html', company=COMPANY)


login_manager.init_app(app)

manager = APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(User, methods=['GET'],results_per_page=10)

if __name__ == "__main__":
	app.run(host="0.0.0.0", debug=True)
	#app.run(host='0.0.0.0', port=80)