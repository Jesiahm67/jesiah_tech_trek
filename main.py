from flask import Flask, render_template, request, flash, redirect

from flask_login import LoginManager, login_user # for managing user sessions

import pymysql 

from dynaconf import Dynaconf

app = Flask(__name__)

config = Dynaconf(settings_file=["settings.toml"])

app.secret_key = config.secret_key

login_manager = LoginManager(app) 

class User:
    is_authenticated = True
    is_active = True
    is_anonymous = False

    def __init__(self, result):
        self.name = result['Name']
        self.email = result['Email']
        self.address = result['Address']
        self.id = result['ID']

    def get_id(self):
        return str(self.id) 
    
@login_manager.user_loader
def load_user(user_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `User` WHERE `ID` = %s", (user_id))
    result = cursor.fetchone()
    connection.close()

    if result is None:
        return None
    return User(result)

def connect_db():
    conn = pymysql.connect(
        host="db.steamcenter.tech",
        user="jminott",
        password=config.password,
        database="jminott_pc_parts_and_service_",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    return conn

@app.route("/")
def index():
    
    return render_template("homepage.html.jinja")
@app.route("/browse")
def browse():
    connection = connect_db()
    
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM `Product`")
    
    result = cursor.fetchall()
    
    connection.close()
    
    return render_template("browse.html.jinja", products=result)

@app.route("/product/<product_id>")
def product_page(product_id):
    connection = connect_db()
    
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM `Product` WHERE `ID` = %s", (product_id) )
    
    result = cursor.fetchone()
    
    connection.close()
    
    return render_template("product.html.jinja", product = result)


@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method == 'POST':
        email = request.form["email"]
        password = request.form["password"]
        #connection to the Database
        connection = connect_db()
        cursor = connection.cursor()
        #executing sql code
        cursor.execute("SELECT * FROM `User` WHERE `Email` = %s", (email))
        result = cursor.fetchone()
        connection.close()
        if result is None:
            flash("No user found")
        elif password != result["Password"]:
            flash("Incorrect password")
        else:
            login_user(User(result))#user now is successfully logged in.
            return redirect('/browse')
        

    return render_template("login.html.jinja")
    
    
    
@app.route('/signup', methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        name=request.form["name"]
        email=request.form["email"]
        password=request.form["password"]
        password_repeat=request.form["repeat_password"]
        address=request.form["address"]
        birthdate=request.form["birthdate"]
        
        if password != password_repeat:
            flash("Passwords do not match")
        elif len(password) < 8:
         flash("Password must be at least 8 characters long")     
        else:
            connection = connect_db()
            
            cursor = connection.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO `User` (`Name`, `Password`, `Email`, `Address`)
                    VALUES (%s, %s, %s, %s)
                """, (name, password, email, address))
                connection.close()
            except pymysql.err.IntegrityError:
                flash("User with that email already exists")
                connection.close()
            else:
                return redirect('/login')
        
    return render_template("register.html.jinja")
