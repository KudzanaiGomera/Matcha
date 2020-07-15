from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL, MySQLdb
import bcrypt
import re
import os

UPLOAD_FOLDER = 'static/pictures/'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'matcha'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)


@app.route('/matcha/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
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
        email = request.form['email']
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
        elif not re.match(r'[A-Za-z0-9]+', password):
            msg = 'Invalid password!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not firstname or not lastname or not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute(
                'INSERT INTO accounts VALUES (NULL,%s, %s, %s, %s, %s)', (firstname, lastname, username, password, email,))
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
            'INSERT INTO profiles VALUES (NULL,%s, %s, %s, %s, %s)', (user_id, gender, sexual_orientation, bio, listofinterest,))
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
            'UPDATE profiles SET VALUES (%s, %s, %s, %s)', (gender, sexual_orientation, bio, listofinterest,)) #TODo
        mysql.connection.commit()
        msg = 'You have successfully edit your profile'
        return redirect(url_for('profile'))

    elif request.method == 'POST':
            msg = 'Please fill out the form! ...'
    return render_template('extended_profile.html', msg=msg)



# http://localhost:5000/matcha/upload - this will be the registration page, we need to use both GET and POST requests


@app.route('/matcha/upload', methods=['GET', 'POST'])
def upload():
    # Output message if something goes wrong...
    msg = ''
    if request.method == 'POST':
        user_id = session['id']
        if 'image' not in request.files:
            return 'No file choosen!'
        image = request.files['image']
        path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(path)
        image_path = path
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'INSERT INTO images VALUES (NULL,%s,%s)',(user_id,image_path,))
        mysql.connection.commit()
        msg = 'You have successfully uploaded you image'
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
    if request.method == 'POST' and 'firstname' in request.form and 'lastname' in request.form and 'email' in request.form:
        # Create variables for easy access
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        user_id = session['id']

     # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not firstname or not lastname or not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute(
                'UPDATE accounts SET VALUES (%s, %s, %s)', (firstname, lastname, email,))  # TODo
            mysql.connection.commit()
            msg = 'You have successfully changed your firstname, email and lastname!'
            return redirect(url_for('profile'))

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form! ...'
    # Show registration form with message (if any)
    return render_template('edit_profile.html', msg=msg)

  # http://localhost:5000/matcha/profile - this will be the home page, only accessible for loggedin users

@app.route('/matcha/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page so they can check their profile
        return render_template('profile.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

    # http://localhost:5000/matcha/home - this will be the home page, only accessible for loggedin users


@app.route('/matcha/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.secret_key = "kudzanai123456789gomera"
    app.run(debug=True)
