from flask import Flask, render_template, request, flash, redirect

import pymysql

from dynaconf import Dynaconf

app = Flask(__name__)

config = Dynaconf(settings_file=["settings.toml"])

app.secret_key = config.secret_key

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


@app.route("/login")
def login():
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
            
            cursor.execute("INSERT INTO `User` (`Name`, `Email`, `Password`, `Address`, `Birthdate`) VALUES (%s, %s, %s, %s, %s)", (name, email, password, address, birthdate))
            
            return redirect("/login")
        
    return render_template("register.html.jinja")
