from flask_login import LoginManager, login_user, current_user, login_required, logout_user, UserMixin
from flask import Flask,jsonify,request,render_template,Response,flash,redirect,url_for
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
import string
import pandas as pd
import json

from decimal import *

app = Flask(__name__)

DATABASE_PATH = 'sqlite:///database/venmodata.db'

UPLOAD_FOLDER = os.path.join(app.instance_path, 'uploads')
# only allow images to be uploaded
ALLOWED_EXTENSIONS = set(['csv'])
def allowed_file(filename):
	return '.' in filename and \
		   filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
db = SQLAlchemy(app)

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
	__tablename__ = 'transactions'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(32))
	transaction_id = db.Column(db.Float())
	datetime = db.Column(db.String(32))
	transaction_type = db.Column(db.String(32))
	status = db.Column(db.String(32))
	note = db.Column(db.String(128))
	sender = db.Column(db.String(32))
	recipient = db.Column(db.String(32))
	amount_total = db.Column(db.Float())
	funding_source = db.Column(db.String(32))
	destination = db.Column(db.String(32))
	statement_period_venmo_fees = db.Column(db.Float())
	terminal_location = db.Column(db.String(32))
	year_to_date_venmo_fees = db.Column(db.Float())

	@property
	def formatted_date(self):
		datetime_object = datetime.datetime.strptime(self.datetime, '%d-%m-%Y %H:%M')
		return datetime_object.strftime("%B %d, %Y")

	@property
	def formatted_amount_total(self):
		return '{:0.2f}'.format(self.amount_total)

	def as_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}

	def __init__(self, username, transaction_id, _datetime, transaction_type, status, note, sender, recipient, amount_total, amount_fee, funding_source, destination, statement_period_venmo_fees, terminal_location, year_to_date_venmo_fees):
		self.username = username
		self.transaction_id = transaction_id
		self.datetime = _datetime
		self.transaction_type = transaction_type
		self.status = status
		self.note = note
		self.sender = sender
		self.recipient = recipient
		self.amount_total = amount_total
		self.amount_fee = amount_fee
		self.funding_source = funding_source
		self.destination = destination
		self.statement_period_venmo_fees = statement_period_venmo_fees
		self.terminal_location = terminal_location
		self.year_to_date_venmo_fees = year_to_date_venmo_fees


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

class FileUploadForm(Form):
	file = FileField('Upload Venmo CSV File', [validators.Required()])
	submit = SubmitField('Upload')

	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)

	def validate(self):
		if not self.file:
			return False
		return True

class SortTableForm(Form):
	sort_by = SelectField('Sort Transactions', choices=[('id', 'ID ASC'), ('iddesc', 'ID DSC'), ('date', 'Date ASC'), ('datedesc', 'Date DSC'), ('amount', 'Amount ASC'), ('amountdesc', 'Amount DSC')])
	submit = SubmitField('Sort')

	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)

	def validate(self):
		if not self.sort_by:
			return False
		return True

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

def sort_csv(file):
    df = pd.read_csv(file)
    username = df.iloc[0, 0]
    df["Username"] = username
    df["Datetime"] = pd.to_datetime(df.Datetime).dt.strftime("%d-%m-%Y %H:%S").astype(str)
    df.drop(axis=0, index=[0, len(df.index) - 1], inplace=True)
    df.drop(["Beginning Balance", "Ending Balance", "Disclaimer"], axis=1, inplace=True)
    df.update(df[["Amount (fee)", "Statement Period Venmo Fees", "Year to Date Venmo Fees"]].fillna(0))
    df.update(df[["Destination", "Funding Source"]].fillna(""))
    df["Amount (total)"] = df["Amount (total)"].str.strip("$()")
    df["Note"] = df["Note"].str.capitalize()
    df.columns = df.columns.str.replace(r"(\()|(\))", "", regex=True).str.strip(" ").str.replace(" ", "_").str.lower()
    df = df.rename({"from": "sender", "id": "transaction_id", "type": "transaction_type", "to": "recipient"}, axis=1)

    df.sort_values('datetime')
    return df

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
	form = FileUploadForm()
	if request.files:
		if form.validate_on_submit():
			if form.validate():
				# check if the post request has the file part)
				file = request.files['file']
				# if user does not select file, browser also
				# submit an empty part without filename
				if file.filename == '':
					flash('No selected file', category='red')
					return redirect(request.url)
				if file and allowed_file(file.filename):
					readcsv = sort_csv(file)
					for row in readcsv.values:
						username = row[0] or ''
						transaction_id = row[1] or 0
						_datetime = row[2] or ''
						transaction_type = row[3] or ''
						status = row[4] or ''
						note = row[5] or ''
						sender = row[6] or ''
						recipient = row[7] or ''
						amount_total = row[8] or 0.0
						amount_fee = row[9] or 0.0
						funding_source = row[10] or ''
						destination = row[11] or ''
						statement_period_venmo_fees = row[12] or 0
						terminal_location = row[13] or ''
						year_to_date_venmo_fees = row[14] or 0

						transaction = VenmoData(username, transaction_id, _datetime, transaction_type, status, note, sender, recipient, amount_total, amount_fee, funding_source, destination, statement_period_venmo_fees, terminal_location, year_to_date_venmo_fees)
						db.session.add(transaction)

					db.session.commit()

				flash('Upload successful', category='green')
				return redirect('/dashboard')
			else:
				flash('Upload failed', category='red')

	sort_form = SortTableForm()
	if sort_form.validate_on_submit():
		if sort_form.validate():
			key = sort_form.sort_by.data
			if key == 'id':
				data = VenmoData.query.order_by(VenmoData.id.asc()).all()
			elif key == 'iddesc':
				data = VenmoData.query.order_by(VenmoData.id.desc()).all()
			elif key == 'date':
				data = VenmoData.query.order_by(VenmoData.datetime.asc()).all()
			elif key == 'datedesc':
				data = VenmoData.query.order_by(VenmoData.datetime.desc()).all()
			elif key == 'amount':
				data = VenmoData.query.order_by(VenmoData.amount_total.asc()).all()
			elif key == 'amountdesc':
				data = VenmoData.query.order_by(VenmoData.amount_total.desc()).all()
		else:
			data = VenmoData.query.order_by(VenmoData.id).all()
	else:
		data = VenmoData.query.order_by(VenmoData.id).all()

	return render_template('dashboard.html', company=COMPANY, transactions=data, form=form, sort_form=sort_form)

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

if __name__ == "__main__":
<<<<<<< Updated upstream
	app.run(host="0.0.0.0", debug=True)

=======
	pass
	# app.run(host="0.0.0.0", debug=True)
	# app.run(host='0.0.0.0', port=80)
>>>>>>> Stashed changes
