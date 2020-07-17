from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_mysqldb import MySQL, MySQLdb
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import re
import os
import secrets
import hashlib


UPLOAD_FOLDER = 'static/pictures/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'matcha'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)
socketio = SocketIO(app)

@app.route('/matcha/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Creating all the db and tables needed can add your if necessary
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''CREATE DATABASE IF NOT EXISTS matcha''')
    print("Databse created")

    cursor.execute('''CREATE TABLE  IF NOT EXISTS accounts(
        id INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(250) NOT NULL UNIQUE,
        firstname VARCHAR(250) NOT NULL UNIQUE,
        lastname VARCHAR(250) NOT NULL UNIQUE,
        password VARCHAR(250) NOT NULL,
        email VARCHAR(250) NOT NULL UNIQUE,
        vkey VARCHAR(250) NOT NULL,
        user_email_status enum('not verified','verified') NOT NULL DEFAULT 'not verified',
        picture VARCHAR(500) NOT NULL DEFAULT 'profile.jpg'
    )''')
    print("Table created")

    cursor.execute(''' CREATE TABLE IF NOT EXISTS profiles(
        id INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
        user_id INT(11) NOT NULL UNIQUE,
        gender VARCHAR(250) NOT NULL UNIQUE,
        sexual_orientation VARCHAR(250) NOT NULL UNIQUE,
        bio VARCHAR(250) NOT NULL UNIQUE,
        listofinterest VARCHAR(250) NOT NULL UNIQUE,
        FOREIGN KEY(user_id) REFERENCES accounts(id)
    )''')
    print("Table created")

    cursor.execute('''
   CREATE TABLE IF NOT EXISTS images(
        id INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
        user_id INT(11) NOT NULL,
        image_path VARCHAR(500) NOT NULL,
        FOREIGN KEY(user_id) REFERENCES accounts(id)
    )''')
    print("Table created")


    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM accounts WHERE username = %s AND password = %s', (username, check_password_hash(password, password),))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!... Please check you login details'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)

    # http://localhost:5000/matcha/logout - this will be the logout page


@app.route('/matcha/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

# http://localhost:5000/matcha/register - this will be the registration page, we need to use both GET and POST requests


@app.route('/matcha/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'firstname' in request.form and 'lastname' in request.form and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']
        password = request.form['password']
        hashdpw = generate_password_hash(password, method='sha256', salt_length=6)
        email = request.form['email']
        
        #generate vkey
        v = username
        vk = hashlib.md5(username.encode())
        vkey = vk.hexdigest()

        user_email_status = ''
        picture = 'profile.jpg'
     # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM accounts WHERE email = %s', (email,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Email Account already exists!...'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'^[A-Z]\w{5}.*[*@#]$', password):
            msg = 'Please make sure your pwd contains atleast six alphanu characters, start with uppercase and end with atleast one special symbol(*,@,# etc)!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not firstname or not lastname or not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute(
                'INSERT INTO accounts VALUES (NULL,%s, %s, %s, %s, %s,%s,%s,%s)', (username, firstname, lastname, hashdpw, email,vkey,user_email_status,picture,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            return redirect(url_for('login'))

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form! ...'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)


# http://localhost:5000/matcha/extended_profile - this will be the page the user is directed to complete his or her profile, we need to use both GET and POST requests


@app.route('/matcha/extended_profile', methods=['GET', 'POST'])
def extended_profile():
    # Output message if something goes wrong...
    msg = ''
        # User is loggedin show them the home page so they can change infomation on their profile
    if request.method == 'POST' and 'gender' in request.form and 'sexual_orientation' in request.form and 'bio' in request.form and 'listofinterest' in request.form:
            #Create variables for easy access
        gender = request.form['gender']
        sexual_orientation = request.form['sexual_orientation']
        bio = request.form['bio']
        listofinterest = request.form['listofinterest']
        user_id = session['id']
            #check if the above already exits in the databasse
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
             'INSERT INTO accounts (NULL,%s, %s, %s, %s, %s,%s,%s) VALUES ( , firstname, lastname, username, password, email, vkey, user_email_status)')
        mysql.connection.commit()
        msg = 'You have successfully completed your profile' 
        return redirect(url_for('profile'))

    elif request.method == 'POST':
            msg = 'Please fill out the form! ...'
    return render_template('extended_profile.html', msg=msg)


# http://localhost:5000/matcha/edit_extended_profile - this will be the page the user is directed to complete his or her profile, we need to use both GET and POST requests


@app.route('/matcha/edit_extended_profile', methods=['GET', 'POST'])
def edit_extended_profile():
    # Output message if something goes wrong...
    msg = ''
        # User is loggedin show them the home page so they can change infomation on their profile
    if request.method == 'POST' and 'gender' in request.form and 'sexual_orientation' in request.form and 'bio' in request.form and 'listofinterest' in request.form:
            #Create variables for easy access
        gender = request.form['gender']
        sexual_orientation = request.form['sexual_orientation']
        bio = request.form['bio']
        listofinterest = request.form['listofinterest']
        user_id = session['id']
            #check if the above already exits in the databasse
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'UPDATE profiles SET gender=%s, sexual_orientation=%s, bio=%s, listofinterest=%s WHERE user_id=%s', (gender, sexual_orientation, bio, listofinterest, user_id,))
        mysql.connection.commit()
        msg = 'You have successfully edit your profile'
        return redirect(url_for('profile'))

    elif request.method == 'POST':
            msg = 'Please fill out the form! ...'
    return render_template('edit_extended_profile.html', msg=msg)



# http://localhost:5000/matcha/upload - this will be the registration page, we need to use both GET and POST requests

def save_picture(fname):
    random_hex = secrets.token_hex(8)
    f_name, f_ext = os.path.splitext(fname.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/pictures', picture_fn)
    fname.save(picture_path)
    return picture_fn


def save_profile_picture(fname):
    random_hex = secrets.token_hex(8)
    f_name, f_ext = os.path.splitext(fname.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pic', picture_fn)
    fname.save(picture_path)
    return picture_fn


@app.route('/matcha/upload', methods=['GET', 'POST'])
def upload():
    # Output message if something goes wrong...
    msg = ''
    if request.method == 'POST':
        user_id = session['id']
        if 'image' not in request.files:
            return 'No file choosen!'
        img = request.files['image']
        picture = save_picture(img)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'INSERT INTO images VALUES (NULL,%s,%s)',(user_id,picture,))
        mysql.connection.commit()
        msg = 'You have successfully uploaded you image'
        return redirect(url_for('profile'))

    elif request.method == 'POST':
        msg = 'No file choosen! ...'
    return render_template('upload.html', msg=msg)


@app.route('/matcha/profile_pic', methods=['GET', 'POST'])
def profile_pic():
    # Output message if something goes wrong...
    msg = ''
    if request.method == 'POST':
        user_id = session['id']
        if 'image' not in request.files:
            return 'No file choosen!'
        img = request.files['image']
        picture = save_profile_picture(img)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'UPDATE accounts SET picture=%s WHERE id=%s',(picture, user_id,))
        mysql.connection.commit()
        msg = 'You have successfully uploaded your image'
        return redirect(url_for('profile'))

    elif request.method == 'POST':
        msg = 'No file choosen! ...'
    return render_template('upload.html', msg=msg)


# http://localhost:5000/matcha/edit_profile - this will be the edit_profile page to change your firstname, lastname and email, we need to use both GET and POST requests


@app.route('/matcha/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'firstname' in request.form and 'lastname' in request.form and 'email' in request.form:
        # Create variables for easy access
        username  = request.form['username']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        user_id = session['id']

     # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not username or not firstname or not lastname or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute(
                'UPDATE accounts SET username=%s, firstname=%s, lastname=%s, email=%s WHERE id =%s', (username, firstname, lastname, email, user_id,))
            mysql.connection.commit()
            msg = 'You have successfully changed your username, firstname, email and lastname! Please login with your new username and old password'
            return redirect(url_for('login'))

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form! ...'
    # Show registration form with message (if any)
    return render_template('edit_profile.html', msg=msg)

  # http://localhost:5000/matcha/profile - this will be the home page, only accessible for loggedin users

@app.route('/matcha/profile')
def profile():
    # Check if user is loggedin
    record = ''
    profile = ''
    if 'loggedin' in session:
        
        user_id = session['id']

     # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM images WHERE user_id=%s', (user_id,))
        # Fetch all record and return result
        record = cursor.fetchall()
        
        #for profile picture
        cursor.execute(
            'SELECT * FROM accounts WHERE id=%s', (user_id,))
        # Fetch all record and return result
        profile = cursor.fetchall()

        # User is loggedin show them the home page so they can check their profile
        return render_template('profile.html', username=session['username'], user_id=user_id, record=record,  profile=profile)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

    # http://localhost:5000/matcha/home - this will be the home page, only accessible for loggedin users


@app.route('/matcha/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        user_id = session['id']

     # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        #for profile picture
        cursor.execute(
            'SELECT * FROM accounts', ())
        # Fetch all record and return result
        profile = cursor.fetchall()
        return render_template('home.html', username=session['username'], profile=profile)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/matcha/chatpage')
def chat():
    # Check is user is loggedin
    if 'loggedin' in session:
        #User is logged in they may see chatpage
        return render_template('chatpage2.html', username=session['username'])

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')


@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)

    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.secret_key = "kudzanai123456789gomera"
    app.run(debug=True)
