from flask import Flask, redirect, session, render_template, request, flash
from mysqlconnection import MySQLConnector
import re, datetime
from flask.ext.bcrypt import Bcrypt
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "I<3SecretsToo"
EMailRegex = re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$')
mysql = MySQLConnector(app, 'TheWall')
@app.route('/')
def main():
	return render_template('main.html')

@app.route('/login', methods = ['POST'])
def validate_login():
	session['errors'] = {}
	if not EMailRegex.match(request.form['email']):
		session['errors'].update({'email2': 'The E-Mail must be a valid e-mail address'})
	if len(request.form['password']) < 8:
		session['errors'].update({'password2': 'Password must be at least 8 characters'})
	if len(session['errors']) > 0:
		flash(session['errors'])
		return redirect('/')
	else:
		query = "SELECT * FROM users WHERE email = :email LIMIT 1"
		data = {'email': request.form['email']}
		user = mysql.query_db(query, data)
		if user == []:
			session['errors'].update({'notreg': 'E-Mail is not registered.'})	
			return redirect('/')
		else:
			if bcrypt.check_password_hash(user[0]['password'], request.form['password']):
				session['logged_info'] = {'id': user[0]['id'], 'first_name': user[0]['first_name'], 'last_name': user[0]['last_name']}
				return redirect('/wall')
			else:
				session['errors'].update({'passmatch': 'Incorrect password entered for registered E-Mail.'})
				flash(session['errors'])
				return redirect('/')

@app.route('/wall')
def welcome():

	query1 = "SELECT messages.users_id, messages.message, messages.id AS message_id, messages.created_on, concat(users.first_name, ' ', users.last_name) as author FROM messages LEFT JOIN users ON users.id = messages.users_id ORDER BY messages.created_on DESC;"

	query2 = "SELECT comments.id AS comment_id, comments.comment, comments.created_on, messages_id, users_id, concat(users.first_name, ' ', users.last_name) AS author FROM comments LEFT JOIN users ON users.id = comments.users_id"
	all_messages = mysql.query_db(query1)
	all_comments = mysql.query_db(query2)
	now = datetime.datetime.now()
	for message in all_messages:
		newTime =  now - message['created_on']
		if newTime.seconds/60 <= 30:
			message.update({'btn': True})
		else:
			message.update({'btn': False})
	return render_template('user_wall.html', all_messages = all_messages, all_comments = all_comments)

@app.route('/wall/message/<id>', methods = ['POST'])
def add_message(id):
	query = "INSERT INTO messages(message, created_on, updated_on, users_id) VALUES(:message, now(), now(), :id)"
	info = {
			'message': request.form['message'],
			'id': id
			}
	mysql.query_db(query, info)
	return redirect('/wall')

@app.route('/wall/comment/<msg_id>/<usr_id>', methods = ['POST'])
def add_comment(msg_id, usr_id):
	query = "INSERT INTO comments(comment, created_on, updated_on, messages_id, users_id) VALUES(:comment, now(), now(), :msg_id, :user_id)"
	info = {
			'comment': request.form['comment'],
			'msg_id': msg_id,
			'user_id': usr_id
			}
	mysql.query_db(query, info)
	return redirect('/wall')

@app.route('/wall/message/delete/<message_id>')
def remove_message(message_id):
	if 'del_msg' in session:
		del session['del_msg']


	query1 = "DELETE FROM comments WHERE messages_id = :message_id"
	query2 = "DELETE FROM messages WHERE id = :message_id"
	info = {
			'message_id': message_id
			}
	msg_time = mysql.query_db("SELECT created_on FROM messages WHERE id = :message_id", info)
	now = datetime.datetime.now()
	newTime = now - msg_time[0]['created_on']
	if newTime.seconds/60 <= 30:
		mysql.query_db(query1, info)
		mysql.query_db(query2, info)
	else:
		session['del_msg'] = "Sorry but message can only be deleted if done within 30 minutes of creating it."
	return redirect('/wall')

@app.route('/wall/remove_warning')
def remove_warning():
	del session['del_msg']
	return redirect('/wall')

@app.route('/process', methods = ['POST'])
def validate_():
	session['errors'] = {}
	if len(request.form['fname']) < 2:
		session['errors'].update({'fname': 'The first name field must be at least two characters'})
	elif not str.isalpha(str(request.form['fname'])):
		session['errors'].update({'fname': 'First name cannot have number or symbols'})
	if len(request.form['lname']) < 2:
		session['errors'].update({'lname': 'The last name field must be at least two characters'})
	elif not str.isalpha(str(request.form['lname'])):
		session['errors'].update({'lname': 'Last name cannot have numbers or symbols'})
	if not EMailRegex.match(request.form['email']):
		session['errors'].update({'email': 'The E-Mail must be a valid e-mail address'})
	if len(request.form['password']) < 8:
		session['errors'].update({'password': 'Password must be at least 8 characters'})
	elif not any(char.isdigit() for char in str(request.form['password'])):
		session['errors'].update({'password': 'Password must contain at least one number'})
	elif not any(char.isupper() for char in str(request.form['password'])):
		session['errors'].update({'password': 'Password must contain at least one uppercase letter'})
	if request.form['confirmpass'] != request.form['password']:
		session['errors'].update({'confirmpass': 'The password confirmation does not match the password'})
	if len(session['errors']) > 0:
		flash(session['errors'])
		return render_template('main.html')
	else:
		query1 = "SELECT email FROM users WHERE email = :email"
		data1 = {"email": request.form['email']}
		if not mysql.query_db(query1, data1):
			session['registered'] = "registered"
			pw_hash = bcrypt.generate_password_hash(request.form['password'])
			query = "INSERT INTO users(first_name, last_name, email, password, created_on, updated_on) VALUES(:first_name, :last_name, :email, :password, now(), now())"
			info = {
			"first_name": request.form['fname'],
			"last_name": request.form['lname'],
			"email": request.form['email'],
			"password": pw_hash
			}
			mysql.query_db(query, info)
		else:
			session['errors'].update({'user_registered': 'This E-Mail is already registered'})
		return redirect('/')

@app.route('/logout')
def logout():
	session.clear()
	return redirect('/')
app.run(debug=True)

	