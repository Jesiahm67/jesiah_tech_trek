from flask import Flask, render_template

import pymysql

from dynaconf import Dynaconf

app = Flask(__name__)

config = Dynaconf(settings_file=["settings.toml"])

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