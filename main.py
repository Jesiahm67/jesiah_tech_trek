from flask import Flask, render_template, request, flash, redirect, session, abort  # for web framework and rendering templates

from flask_login import LoginManager, login_user, logout_user, login_required, current_user# for user authentication

login_manager = LoginManager()# for managing user sessions and authentication

import pymysql # for connecting to the database

from dynaconf import Dynaconf # for managing configuration settings

app = Flask(__name__) 
# Load configuration from settings.toml

config = Dynaconf(settings_file=["settings.toml"])# Load secret key from configuration

app.secret_key = config.secret_key

login_manager = LoginManager(app) 

login_manager.login_view = "/login"

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
    user = session.get("user")
    return render_template("homepage.html.jinja")

@app.route("/contact")
def contacts():
    return render_template("contacts.html.jinja")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html.jinja")

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
    
    if result is None: 
       return redirect("/dashboard") # If no product is found, return a 404 error
    
    return render_template("product.html.jinja", product = result)
   
@app.route('/signup', methods=["POST", "GET"])# User Registration
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

@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method == 'POST':
        email = request.form["email"]
        password = request.form["psw"]
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

@app.route("/logout", methods=['GET', 'POST'] )
@login_required
def logout():
    logout_user() # Logs out the current user
    flash("You have been logged out.") # Notify the user
    return redirect("/")

@app.route("/product/<product_id>/add_to_cart", methods=['POST'])
@login_required
def add_to_cart(product_id):
    
    quantity = request.form["Quantity"]# Get quantity from form data
    
    connection = connect_db()
    
    cursor = connection.cursor()
    
    cursor.execute("""
        INSERT INTO `Cart` (`Quantity`, `ProductID`, `UserID`) 
        VALUES (%s, %s, %s) 
        ON DUPLICATE KEY UPDATE 
        `Quantity` = `Quantity` + %s
        
    """, (quantity, product_id, current_user.id, quantity))
    
    connection.close()
    
    return redirect("/cart")

@app.route("/cart")
@login_required
def view_cart():
    connection = connect_db()
    
    cursor = connection.cursor()
    
    cursor.execute("""
        SELECT * FROM `Cart`
        JOIN `Product` ON `Product`.`ID` = `Cart`.`ProductID`
        WHERE `UserID` = %s
    """, (current_user.id))
    
    results = cursor.fetchall()
    
    connection.close()
    
    grand_total = sum(item['Price'] * item['Quantity'] for item in results)
    
    # Pass 'total' to the template
    return render_template("cart.html.jinja", cart_items=results, total=grand_total)

@app.route("/cart/<product_id>/update_qty", methods=['POST'])
@login_required
def update_cart(product_id):
    new_quantity = request.form["qty"]
    
    connection = connect_db()
    
    cursor = connection.cursor()
    
    if int(new_quantity) <= 0:
                cursor.execute("""
                DELETE FROM `Cart`
                WHERE `ProductID` = %s AND `UserID` = %s
            """,(product_id, current_user.id))
                    
    else:
            cursor.execute("""
            UPDATE `Cart`
            SET `Quantity` = %s
            WHERE `ProductID` = %s AND `UserID` = %s
        """, (new_quantity, product_id, current_user.id))
    
    connection.close()
    
    return redirect("/cart")

@app.route("/cart/<product_id>/delete_qty", methods=['POST'])
@login_required
def remove_from_cart(product_id):
    new_quantity = request.form["qty"]
    
    connection = connect_db()
    
    cursor = connection.cursor()
    
    if int(new_quantity) <= 0:
                cursor.execute("""
                DELETE FROM `Cart`
                WHERE `ProductID` = %s AND `UserID` = %s
            """,(product_id, current_user.id))
            
            
                connection.commit()
                flash("Item removed from cart.")
    
    connection.close()
    
    return redirect("/cart")