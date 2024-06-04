from flask import Flask, Blueprint
from flask import redirect
from flask import render_template, request, redirect, url_for, session

# db toolz
from flask_mysqldb import MySQL
from mysql.connector import connect

#utilz
import os, re, hashlib, string, random, uuid

# Database config
config = {
    "user": "flask_mysql_usr",
    "password": "webapp",
    "host": "localhost",
    "database": "flask_webapp",
}

connection = connect(**config)

webapp = Blueprint('app', __name__)

## Start flask server
app = Flask(__name__)
app.register_blueprint(webapp)

#app.secret_key = 'a07190638d442494385a87840b788b3f5'
app.secret_key = uuid.uuid4().hex

@app.route('/')
def welcome_home():
    print('root redirect to /home')
    return redirect('/home')

# http://localhost:5000/home - 
# this will be the home page, only accessible for logged in users
@app.route('/home')
def home():
    print ('Welcome Home !')
    print('/home -  check if logged in to redirect /profile -- if no logged in session -> redirect /login')
    # Check if the user is logged in
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('/cryptoweb/index.html', username=session['username'])
    # User is not loggedin redirect to index page
    return render_template('/cryptoweb/index.html')


# http://localhost:5000/cryptoweb/login - 
# the following will be our login page, which will use both GET and POST requests
@app.route('/login', methods=['GET', 'POST'])
def login():
    print ('/login')
    # Output a message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        print('## METHOD=[POST]')
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = connection.cursor(dictionary=True)
        #cursor.execute('SELECT * FROM accounts WHERE username = %s', (username))
        sql = """SELECT * FROM accounts WHERE username = %s"""
        cursor.execute(sql, (username,))
        # Fetch one record and return result
        account = cursor.fetchone()
        cursor.close()
        # If account exists in accounts table in out database
        if account:
            print('debug account true')
            # double check with hashed_password
            hashed_password_db = account['password']
            hashed_password_req = hashlib.sha512((password + account['salt']).encode("utf-8")).hexdigest()
            if hashed_password_db == hashed_password_req:
                print('debug hashed_password_ true')
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['email'] = account['email']
                session['username'] = account['username']
                # Redirect to home page
                return redirect('/home')
            else:
                # Account exists and password is incorrect
                msg = 'Sorry, Password is wrong !'
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    
    # Show the login homepage with message (if any)
    print('## METHOD=[GET] --> redirect to /cryptoweb/login.html')
    return render_template('/cryptoweb/login.html')

# http://localhost:5000/cryptoweb/register - 
# this will be the registration page, we need to use both GET and POST requests
@app.route('/cryptoweb/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = 'Please fill the form'
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        print(username)
        password = request.form['password']
        print(password)
        email = request.form['email']
        print(email)

        # Check if account exists using MySQL
        cursor = connection.cursor(dictionary=True)
        #cursor.execute('SELECT * FROM accounts WHERE username = %s', (username))
        sql = """SELECT * FROM accounts WHERE username = %s"""
        cursor.execute(sql, (username,))
        account = cursor.fetchone()         
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists.'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Hash the password
            salt = os.urandom(12).hex()
            hashed_password = hashlib.sha512((password + salt).encode("utf-8")).hexdigest()
            # Account doesn't exist, and the form data is valid, so insert the new account into the accounts table
            cursor.execute('INSERT INTO accounts (username, password, email, salt) VALUES (%s, %s, %s, %s)', (username, hashed_password, email, salt))
            connection.commit() 
            msg = 'You have successfully registered!'
            # Create session data, we can access this data in other routes
            print('session true')
            session['loggedin'] = True
            session['email'] = email
            session['username'] = username
            return redirect('/profile')
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('/cryptoweb/register.html', msg=msg)


# http://localhost:5000/cryptoweb/profile - 
# this will be the profile page, only accessible for logged in users
@app.route('/profile')
def profile():
    # Check if the user is logged in
    if 'loggedin' in session:
        print('--> loggedin in session')
        # We need all the account info for the user so we can display it on the profile page
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (session['username'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('/cryptoweb/profile.html', account=account)
    # User is not logged in redirect to login page
    return redirect('/login')

# http://localhost:5000/cryptoweb/logout 
# this will be the logout page
@app.route('/cryptoweb/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.clear()
    # Redirect to login page
    return redirect('/login')


@app.route('/dashboard')
def dashboard():
    return render_template('/cryptoweb/dashboard.html')


@app.route('/portfolio')
def portfolio():
    return render_template('/cryptoweb/portfolio.html')