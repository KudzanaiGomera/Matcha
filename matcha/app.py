from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_mysqldb import MySQL, MySQLdb
from flask_mail import Mail
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, send
import bcrypt
import smtplib
import re
import os
import secrets
import hashlib
import requests
import time
import datetime
import json



UPLOAD_FOLDER = 'static/pictures/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'matcha'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)
socketio = SocketIO(app)

URL = "https://geocode.search.hereapi.com/v1/geocode"
api_key = 'tBIW-X-kr-_ZlNYQda54YJzoRZh6TpVHmwQUxDt-_rc' # Acquire from developer.here.com

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
        picture VARCHAR(500) NOT NULL DEFAULT 'profile.jpg'
    )''')
    print("Table created: accounts")

    cursor.execute(''' CREATE TABLE IF NOT EXISTS profiles(
        id INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
        user_id INT(11) NOT NULL UNIQUE,
        gender VARCHAR(250) NOT NULL,
        sexual_orientation VARCHAR(250) NOT NULL,
        bio VARCHAR(250) NOT NULL,
        nature TINYINT(1) DEFAULT '0',
        art TINYINT(1) DEFAULT '0',
        music TINYINT(1) DEFAULT '0',
        sports TINYINT(1) DEFAULT '0',
        memes TINYINT(1) DEFAULT '0',
        age1 TINYINT(1) DEFAULT '0',
        age2 TINYINT(1) DEFAULT '0',
        age3 TINYINT(1) DEFAULT '0',
        FOREIGN KEY(user_id) REFERENCES accounts(id)
    )''')
    print("Table created: profiles")

    cursor.execute('''
   CREATE TABLE IF NOT EXISTS images(
        id INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
        user_id INT(11) NOT NULL,
        image_path VARCHAR(500) NOT NULL,
        FOREIGN KEY(user_id) REFERENCES accounts(id)
    )''')
    print("Table created: images")

    cursor.execute('''
   CREATE TABLE IF NOT EXISTS popularity(
        id INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
        profile_id INT(11) NOT NULL,
        upvote INT NOT NULL DEFAULT '1',
        FOREIGN KEY(profile_id) REFERENCES accounts(id)
    )''')
    print("Table created: popularity")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS likes(
        id INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
        user_id INT(11) NOT NULL,
        profile_id INT(100) NOT NULL,
        action TINYINT(1) DEFAULT '0',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES accounts(id),
        FOREIGN KEY(profile_id) REFERENCES accounts(id)
    )''')
    print("Table created: likes")

    cursor.execute('''CREATE TABLE IF NOT EXISTS notification(
        id INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(128),
        user_id INT(100) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        payload_json TEXT,
        FOREIGN KEY(user_id) REFERENCES accounts(id)
    )''')
    print("Table created: notifications")

    cursor.execute('''CREATE TABLE IF NOT EXISTS location(
        id INT(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
        user_id INT(100) NOT NULL,
        location VARCHAR(250) NULL DEFAULT 'pretoria',
        FOREIGN KEY(user_id) REFERENCES accounts(id)
    )''')
    print("Table created: location")


    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            if bcrypt.checkpw(password.encode('utf-8'), account['password'].encode('utf-8')):
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
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        email = request.form['email']
        
        #generate vkey
        v = username
        vk = hashlib.md5(username.encode())
        vkey = vk.hexdigest()

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
                'INSERT INTO accounts VALUES (NULL,%s, %s, %s, %s, %s,%s,%s)', (username, firstname, lastname, hashed, email,vkey,picture,))
            mysql.connection.commit()

            #sending email
            message = MIMEText('<p>Click this link!<a href = "http://localhost:5000/matcha/home"> to verify account and login to your Account</a></p>', 'html')
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            # make sure to change this part last parameter which is your password and as well the first which is the email
            server.login('matchamatcha23@gmail.com', 'Hacker23') #'email''pwd'
            server.sendmail('matchamatcha23@gmail.com', email, message.as_string())#'email' #also change the first parameter whcih is the default sending email
            msg = 'You have successfully registered!'
            return redirect(url_for('check_email'))

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form! ...'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)


# http://localhost:5000/matcha/forget_pwd - this will be the forgotten pwd page, we need to use both GET and POST requests


@app.route('/matcha/forget_pwd', methods=['GET', 'POST'])
def forget_pwd():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        # Create variables for easy access
        email = request.form['email']
        password = request.form['password']
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE email = %s', (email,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database

        
        if account:
            if not re.match(r'^[A-Z]\w{5}.*[*@#]$', password):
                msg = 'Please make sure your pwd contains atleast six alphanu characters, start with uppercase and end with atleast one special symbol(*,@,# etc)!'
            else:
                 cursor.execute(
                    'UPDATE accounts SET password=%s WHERE email=%s', (hashed, email,))
                 mysql.connection.commit()

            #sending email
            message = MIMEText('<p>Click this link!<a href = "http://localhost:5000/matcha/home"> to reset your password click this link and login</a></p>', 'html')
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            # make sure to change this part last parameter which is your password and as well the first which is the email
            server.login('matchamatcha23@gmail.com', 'Hacker23') #'email''pwd'
            server.sendmail('matchamatcha23@gmail.com', email, message.as_string())#'email' #also change the first parameter whcih is the default sending email
            msg = 'You have successfully registered!'
            return redirect(url_for('forget_pwd_check'))

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form! ...'
    # Show registration form with message (if any)
    return render_template('forget_pwd.html', msg=msg)

# http://localhost:5000/matcha/extended_profile - this will be the page the user is directed to complete his or her profile, we need to use both GET and POST requests


@app.route('/matcha/extended_profile', methods=['GET', 'POST'])
def extended_profile():
    # Output message if something goes wrong...
    msg = ''
    print("Here1")
        # User is loggedin show them the home page so they can change infomation on their profile
        #Create variables for easy access
    if request.method == 'POST':
        user_id = session['id']
        if 'gender' in request.form:
            gender = request.form['gender']
        if 'sexual_orientation' in request.form:
            sexual_orientation = request.form['sexual_orientation']
        if 'bio' in request.form:
            bio = request.form['bio']
        if 'nature' in request.form:
            nature = 1
        else:
            nature = 0
        if 'art' in request.form:
            art = 1
        else:
            art = 0
        if 'music' in request.form:
            music = 1
        else:
            music = 0
        if 'sports' in request.form:
            sports = 1
        else:
            sports = 0
        if 'memes' in request.form:
            memes = 1
        else:
            memes = 0
        if 'age1' in request.form:
            age1 = 1
        else:
            age1 = 0
        if 'age2' in request.form:
            age2 = 1
        else:
            age2 = 0
        if 'age3' in request.form:
            age3 = 1
        else:
            age3 = 0
            
            #check if the above already exits in the databasse
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
             'INSERT INTO profiles VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',(user_id, gender, sexual_orientation, bio, nature, art, music, sports, memes,age1, age2, age3,))
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
    print("Here1")
        # User is loggedin show them the home page so they can change infomation on their profile
        #Create variables for easy access
    if request.method == 'POST':
        user_id = session['id']
        if 'gender' in request.form:
            gender = request.form['gender']
        if 'sexual_orientation' in request.form:
            sexual_orientation = request.form['sexual_orientation']
        if 'bio' in request.form:
            bio = request.form['bio']
        if 'nature' in request.form:
            nature = 0
        else:
            nature = 1
        if 'art' in request.form:
            art = 0
        else:
            art = 1
        if 'music' in request.form:
            music = 0
        else:
            music = 1
        if 'sports' in request.form:
            sports = 0
        else:
            sports = 1
        if 'memes' in request.form:
            memes = 0
        else:
            memes = 1
        if 'age1' in request.form:
            age1 = 0
        else:
            age1 = 1
        if 'age2' in request.form:
            age2 = 0
        else:
            age2 = 1
        if 'age3' in request.form:
            age3 = 0
        else:
            age3 = 1
            
            #check if the above already exits in the databasse
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'UPDATE profiles SET gender=%s, sexual_orientation=%s, bio=%s, nature=%s, art=%s, music=%s, sports=%s, memes=%s, age1=%s, age2=%s, age3=%s WHERE user_id=%s ', (gender, sexual_orientation, bio, nature, art, music, sports, memes, age1, age2, age3, user_id,))
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
    tags = ''
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

        #for profiles tags
        cursor.execute(
            'SELECT * FROM profiles WHERE user_id=%s', (user_id,))
        # Fetch all record and return result
        tags = cursor.fetchall()
        print (tags)

        # User is loggedin show them the home page so they can check their profile
        return render_template('profile.html', username=session['username'], user_id=user_id, record=record,  profile=profile, tags=tags)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

    
@app.route('/matcha/user_profile', methods=(['GET', 'POST']))
def user_profile():
    # Check if user is loggedin
    record = ''
    profile = ''
    tags = ''
    profile_id = request.args.get('profile_id')
    print(profile_id)
    if 'loggedin' in session:
        #Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        #for profile picture
        cursor.execute(
            'SELECT username, picture, gender, bio, sexual_orientation FROM `accounts`, `profiles` WHERE accounts.id= user_id AND accounts.id = %s', (profile_id,))
        # Fetch all record and return result
        profile = cursor.fetchall()
        print(profile)

        cursor.execute(
            'SELECT * FROM images WHERE user_id=%s', (profile_id,))
            # Fetch all record and return result
        record = cursor.fetchall()

        # User is loggedin show them the home page so they can check their profile
        return render_template('user_profile.html', record=record,  profile=profile)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

    # http://localhost:5000/matcha/home - this will be the home page, only accessible for loggedin users

@app.route('/matcha/preferences', methods=['GET', 'POST'])
def preferences():
    profile = ''
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        user_id = session['id']
        status = 'Active...'
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if request.method == 'POST':
            if 'nature' in request.form:
                cursor.execute(
                    'SELECT username, picture, user_id FROM accounts, profiles WHERE accounts.id = user_id AND profiles.nature=%s',(1,))
                # Fetch all record and return result
                profile = cursor.fetchall()
            if 'art' in request.form:
                cursor.execute(
                    'SELECT username, picture, user_id FROM accounts, profiles WHERE accounts.id = user_id AND profiles.art=%s',(1,))
                # Fetch all record and return result
                profile = cursor.fetchall()
            if 'music' in request.form:
                cursor.execute(
                    'SELECT username, picture, user_id FROM accounts, profiles WHERE accounts.id = user_id AND profiles.music=%s',(1,))
                # Fetch all record and return result
                profile = cursor.fetchall()
            if 'sports' in request.form:
                cursor.execute(
                    'SELECT username, picture, user_id FROM accounts, profiles WHERE accounts.id = user_id AND profiles.sports=%s',(1,))
                # Fetch all record and return result
                profile = cursor.fetchall()
            if 'memes' in request.form:
                cursor.execute(
                    'SELECT username, picture, user_id FROM accounts, profiles WHERE accounts.id = user_id AND profiles.memes=%s',(1,))
                # Fetch all record and return result
                profile = cursor.fetchall()
            if 'age1' in request.form:
                cursor.execute(
                    'SELECT username, picture, user_id FROM accounts, profiles WHERE accounts.id = user_id AND profiles.age1=%s',(1,))
                # Fetch all record and return result
                profile = cursor.fetchall()
            if 'age2' in request.form:
                cursor.execute(
                    'SELECT username, picture, user_id FROM accounts, profiles WHERE accounts.id = user_id AND profiles.age2=%s',(1,))
                # Fetch all record and return result
                profile = cursor.fetchall()
            if 'age3' in request.form:
                cursor.execute(
                    'SELECT username, picture, user_id FROM accounts, profiles WHERE accounts.id = user_id AND profiles.age3=%s',(1,))
                # Fetch all record and return result
                profile = cursor.fetchall()
            if 'location' in request.form:
                location = request.form['location']
                cursor.execute(
                    'SELECT username, picture, user_id FROM accounts, location WHERE accounts.id = user_id AND location.location=%s',(location,))
                # Fetch all record and return result
                profile = cursor.fetchall()
        return render_template('preferences.html', username=session['username'], profile=profile, status=status)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/matcha/home', methods=['GET', 'POST'])
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        user_id = session['id']
        status = 'Active...'
     # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        #for profile picture
        cursor.execute(
            'SELECT username, picture, profile_id, COUNT(*) FROM accounts, popularity WHERE accounts.id = profile_id GROUP BY profile_id ORDER BY COUNT(*) DESC', ())
        # Fetch all record and return result
        profile = cursor.fetchall()
        
        if request.method == 'POST':
            profile_id = request.form['profile_id']

        #get likes value from form
        if request.method == 'POST' and 'like' in request.form:
            # store in variable
            action = request.form['like']
            action = 1
        
            cursor.execute(
                'INSERT INTO likes VALUES (NULL,%s, %s, %s, NULL)', (user_id, profile_id, action, ) #silenced the error not fixed
            )
            mysql.connection.commit()
        elif request.method == 'POST' and 'dislike' in request.form:
            action = request.form['dislike']
            action = 0

            cursor.execute(
                'DELETE FROM likes WHERE profile_id=%s', (profile_id,)
            )
            mysql.connection.commit()
        
        if request.method == 'POST':
            profile_id = request.form['profile_id']
        

        if request.method == 'POST' and 'upvote' in request.form:
            upvote = request.form['upvote']
            upvote = 1
            upvote += 1 

            cursor.execute(
                'INSERT INTO popularity VALUES (NULL, %s, %s)', (profile_id, upvote,)
            )
            mysql.connection.commit()

        return render_template('home.html', username=session['username'], profile=profile, status=status)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/matcha/check_email')
def check_email():
    return render_template('check_email.html')


@app.route('/matcha/forget_pwd_check')
def forget_pwd_check():
    return render_template('forget_pwd_check.html')


@app.route('/matcha/Does_not_exists')
def Does_not_exists():
    return render_template('Does_not_exists.html')


@app.route('/matcha/verify')
def verify():
    # Output message if something goes wrong...
    return render_template('verify.html')

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

users = {}

@app.route('/matcha/messages')
def messages():
    if 'loggedin' in session:
        return render_template('messages.html', username=session['username']) 

@socketio.on('message from user', namespace='/messages')
def receive_message_from_user(message):
    print('USER MESSAGE: {}'.format(message))
    emit('from flask', message.upper(), broadcast=True)

@socketio.on('username', namespace='/private')
def receive_username(username):
    users[username] = request.sid
    print('Username added!')

@socketio.on('private_message', namespace='/private')
def private_message(payload):
    recipient_session_id = users[payload['username']]
    message = payload['message']

    emit('new_private_message', message, room=recipient_session_id)


@app.route('/matcha/map', methods=['GET', 'POST'])
def map_func():
    longitude = ''
    latitude = ''
    if 'loggedin' in session:
        user_id = session['id']
        if request.method in 'POST':
            # location = input("Enter the location here: ") #taking user input
            location = request.form['location']
            # location = location.lower
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
            'SELECT * FROM location WHERE user_id = %s', (user_id,))
            location2 = cursor.fetchone()
            # check if location is set then update it
            if location2:
                cursor.execute(
                'UPDATE location SET location=%s WHERE user_id=%s',(location,user_id,)
                )
                mysql.connection.commit()
            
            else:
                # check if location is not set then insert it
                cursor.execute(
                    'INSERT INTO location VALUES (NULL, %s, %s)',(user_id, location,)
                )
                mysql.connection.commit()
                print (location)
            PARAMS = {'apikey':api_key,'q':location} 

            # sending get request and saving the response as response object 
            r = requests.get(url = URL, params = PARAMS) 
            data = r.json()
            #print(data)

            #Acquiring the latitude and longitude from JSON 
            latitude = data['items'][0]['position']['lat']
            #print(latitude)
            longitude = data['items'][0]['position']['lng']
            #print(longitude)
        return render_template('map.html',apikey=api_key,latitude=latitude,longitude=longitude)
    
if __name__ == '__main__':
    app.secret_key = "kudzanai123456789gomera"
    app.run(debug=True)
