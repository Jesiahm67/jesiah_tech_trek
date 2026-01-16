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
    # Fetch user from database
    cursor = connection.cursor()
    # Execute query to get user by ID
    cursor.execute("SELECT * FROM `User` WHERE `ID` = %s", (user_id))
    # Fetch one result
    result = cursor.fetchone()
    # Close the database connection
    connection.close()
    
# If no user is found, return None
    if result is None:
        return None
    
    # Return a User object
    return User(result)

def connect_db():
# Connect to the database using pymysql
    conn = pymysql.connect(
        host="db.steamcenter.tech",
        user="jminott",
        password=config.password,
        database="jminott_pc_parts_and_service_",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    # Return the database connection
    return conn

@app.route("/")
# Homepage route
def index():
    user = session.get("user")
    return render_template("homepage.html.jinja")



@app.route("/dashboard")
# Dashboard route
def dashboard():
    return render_template("dashboard.html.jinja")

@app.route("/browse")
# Browse products route
@login_required
def browse():
    connection = connect_db()
    
    cursor = connection.cursor()
    # Execute query to get all products
    cursor.execute("SELECT * FROM `Product`")
    # Fetch all results
    result = cursor.fetchall()
    
    connection.close()
    # Render the browse template with the products
    return render_template("browse.html.jinja", products=result)

@app.route("/product/<product_id>")
# Product page route
def product_page(product_id):
    connection = connect_db()
    
    cursor = connection.cursor()
    # Execute query to get product by ID
    cursor.execute("SELECT * FROM `Product` WHERE `ID` = %s", (product_id) )
                
    result = cursor.fetchone()
    
    connection.close()
    
    connection = connect_db()
    
    cursor = connection.cursor()
    # Execute query to get reviews for the product
    cursor.execute("""SELECT * FROM `Review` JOIN `User` ON `Review`.`UserID` = `User`.`ID` WHERE `ProductID` = %s""", (product_id) )
    
    reviews = cursor.fetchall()
    
    connection.close()
    # If no product is found, redirect to dashboard
    if result is None: 
       return redirect("/dashboard") # If no product is found, return a 404 error
    
    return render_template("product.html.jinja", product = result , reviews=reviews)
   
@app.route('/signup', methods=["POST", "GET"])# User Registration
def signup():
    # Handle POST request for user registration
    if request.method == "POST":
        name=request.form["name"]
        email=request.form["email"]
        password=request.form["password"]
        password_repeat=request.form["repeat_password"]
        address=request.form["address"]
        birthdate=request.form["birthdate"]
        # Validate password and confirmation
        if password != password_repeat:
            flash("Passwords do not match")
            # Redirect back to the signup page
        elif len(password) < 8:
         flash("Password must be at least 8 characters long") 
         # Redirect back to the signup page    
        else:
            connection = connect_db()
            
            cursor = connection.cursor()
            # Insert new user into the database
            try:
                cursor.execute("""
                    INSERT INTO `User` (`Name`, `Password`, `Email`, `Address`)
                    VALUES (%s, %s, %s, %s)
                """, (name, password, email, address))
                connection.close()
            # Handle duplicate email error
            except pymysql.err.IntegrityError:
                flash("User with that email already exists")
                connection.close()
            # If registration is successful, redirect to login page
            else:
                return redirect('/login')
        
    return render_template("register.html.jinja")

@app.route("/login", methods = ["POST", "GET"])
def login():
    # Handle POST request for user login
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
    # Insert or update cart item in the database
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
    # View cart route
    connection = connect_db()
    
    cursor = connection.cursor()
    # Execute query to get cart items for the current user
    cursor.execute("""
        SELECT * FROM `Cart`
        JOIN `Product` ON `Product`.`ID` = `Cart`.`ProductID`
        WHERE `UserID` = %s
    """, (current_user.id))
    
    results = cursor.fetchall()
    
    connection.close()
    # Calculate grand total
    grand_total = sum(item['Price'] * item['Quantity'] for item in results)
    
    # Pass 'total' to the template
    return render_template("cart.html.jinja", cart_items=results, total=grand_total)

@app.route("/cart/<product_id>/update_qty", methods=['POST'])
@login_required
def update_cart(product_id):
    # Update cart quantity route
    new_quantity = request.form["qty"]
    
    connection = connect_db()
    
    cursor = connection.cursor()
    # Update or delete cart item based on new quantity
    if int(new_quantity) <= 0:
                cursor.execute("""
                DELETE FROM `Cart`
                WHERE `ProductID` = %s AND `UserID` = %s
            """,(product_id, current_user.id))
    # Commit the changes
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
    # Remove from cart route
    new_quantity = request.form["qty"]
    
    connection = connect_db()
    
    cursor = connection.cursor()
    # Update or delete cart item based on new quantity
    if int(new_quantity) <= 0:
                cursor.execute("""
                DELETE FROM `Cart`
                WHERE `ProductID` = %s AND `UserID` = %s
            """,(product_id, current_user.id))
            
            
                connection.commit()
    
    connection.close()
    
    return redirect("/cart")

@app.route("/checkout", methods=['GET', 'POST'])
@login_required
def checkout():
    # Checkout route
    connection = connect_db()
    
    cursor = connection.cursor()
    # Execute query to get cart items for the current user
    cursor.execute("""
        SELECT * FROM `Cart`
        JOIN `Product` ON `Product`.`ID` = `Cart`.`ProductID`
        WHERE `UserID` = %s
    """, (current_user.id))
    
    results = cursor.fetchall()


    # Process checkout on POST request
    if request.method == 'POST':
        cursor.execute("INSERT INTO `Order_Sale` (`UserID`) VALUES (%s)", (current_user.id) )
        # store product bought
        sale = cursor.lastrowid
        for item in results:
            cursor.execute("INSERT INTO `Order_cart` (`Order_SaleID`, `ProductID`,`Quantity`) VALUES (%s, %s, %s) ",
                           (sale, item['ProductID'], item['Quantity']) )
    # clear the cart
        cursor.execute("DELETE FROM `Cart` WHERE `UserID` = %s", (current_user.id) )
        return redirect("/order")
    #thank the user for their purchase
        
    connection.close()
    
    grand_total = sum(item['Price'] * item['Quantity'] for item in results)
    
    # Pass 'total' to the template
    return render_template("checkout.html.jinja", cart_items=results, total=grand_total)
@app.route("/thank_you")
@login_required
def thank_you():
    return render_template("thank_you.html.jinja")

@app.route("/order")
@login_required
def Order():
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT
        `Order_Sale`.`ID`,
        `Order_Sale`.`Timestamp`, 
        SUM(`Order_cart`. Quantity ) AS 'Quantity', 
        SUM(`Order_cart`.`Quantity` * `Product`.`Price`) AS 'Total'
    FROM `Order_Sale`
    JOIN `Order_cart` ON `Order_SaleID` = `Order_Sale`.`ID`
    JOIN `Product` ON `Product`.`ID` = `Order_cart`.`ProductID`
    WHERE `UserID` = %s 
    GROUP BY `Order_Sale`.`ID`;
    """, (current_user.id,) )

    result = cursor.fetchall()
    connection.close()  

    return render_template("order.html.jinja", order=result)

@app.route("/product/<product_id>/review", methods=['POST'])
@login_required
def add_review(product_id):
    
    rating = request.form["rating"]
    comment = request.form["comments"]
    
    connection = connect_db()
    cursor = connection.cursor()
    
    cursor.execute("""
        INSERT INTO `Review` (`Ratings`, `Comments`, `ProductID`, `UserID`)
        VALUES (%s, %s, %s, %s)
    """, (rating, comment, product_id, current_user.id))
    
    connection.close()
    
    return redirect(f"/product/{product_id}")