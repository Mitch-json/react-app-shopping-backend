from flask import Flask, json, request, url_for, send_from_directory,send_file, make_response
from flask_mysqldb import MySQL, MySQLdb
from werkzeug.utils import secure_filename
import mysql.connector as mq
from mysql.connector import errorcode
from flask.json import jsonify
from serializers import products_serializer, categories_serializer, orders_serializer, prods_serializer, users_serializer
import jwt
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from itsdangerous import URLSafeSerializer, SignatureExpired
from flask_cors import CORS, cross_origin



UPLOAD_FOLDER = 'static/images/product_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app = Flask(__name__)
bcrypt = Bcrypt(app)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

app.config["MYSQL_HOST"] = 'sql5.freesqldatabase.com'
app.config["MYSQL_USER"] = 'sql5407697'
app.config["MYSQL_PASSWORD"] = 'dmy1zjAqk3'
app.config["MYSQL_DB"] = 'sql5407697'
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'mitchjaga@gmail.com'
app.config['MAIL_PASSWORD'] = 'gzmqjhinejescgnk'
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USE_TLS'] = True

mail = Mail(app)


mysql = MySQL(app)

TABLES = {}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/admin/users', methods=["GET"])
def get_all_users():
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT _id, name, email, isAdmin, suspended FROM users")
        results = cur.fetchall()
        users = users_serializer(results)
        resp = make_response({"users": users})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except MySQLdb.Error as err:
        resp = make_response({"err": err.args[1]})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

@app.route('/api/admin/user/<column>/<_id>/<value>', methods=["GET"])
def suspend(column, _id, value):
    cur = mysql.connection.cursor()
    sql = "UPDATE users SET "+ str(column) + "=" + "'"+ value + "' " + "WHERE _id="+"'"+_id+"'"
    try:
        cur.execute(sql)
        cur.connection.commit()
        cur.close()
        resp = make_response({"msg": "User updated"})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except MySQLdb.Error as err:
        resp = make_response({"err": err.args[1]})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

@app.route("/api/users/signin", methods=["POST"])
def signin():
    username = request.json.get("email", None)
    password = request.json.get("password", None)

    cur = mysql.connection.cursor()
    sql ="select _id, name, email, password, isAdmin, suspended from users where email="+ "'"+username+"'"
    try:
        cur.execute(sql)
        user = cur.fetchall()
        
        if user:
            if user[0][5] == 1:
                resp = make_response({"sus": "Account Suspended"})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            pw_hash = user[0][3]
            if not bcrypt.check_password_hash(pw_hash, password):
                resp = make_response({"err": "Invalid password"})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            
            encoded_jwt = jwt.encode(
                {
                    "_id": user[0][0],
                    "name": user[0][1],
                    "email": user[0][2],
                    "isAdmin": user[0][4],
                }, '28736746835476527365475263rtuyfdcvxvcvskek6ftwefdgfvshcvzghcygsveyfgyefdsbmv', algorithm="HS256")
            
            if user[0][5] == 0:
                resp = make_response({"_id": user[0][0], "name": user[0][1],"email": user[0][2],"isAdmin": user[0][4],"token":encoded_jwt})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
        else:
            resp = make_response({"err": "Email does not exist"})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
    except MySQLdb.Error as err:
        resp = make_response({"err": err.args[1]})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

@app.route("/api/email", methods=["POST"])
def send_email():
    code = request.json.get("code", None)
    email = request.json.get("email", None)

    msg = Message('Email Verification', sender='mitchjaga@gmail.com', recipients=[email])
    msg.body = code
    try:
        mail.send(msg)
        resp = make_response({"msg": "Verification Code sent"})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except:
        resp = make_response({"err": "Email Not sent, please try again Later"})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


@app.route("/api/users/register", methods=["POST"])
def register():
    name = request.json.get("name", None)
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    pw_hash = bcrypt.generate_password_hash(password)

    cur = mysql.connection.cursor()
    cur.execute("show tables like 'users'")
    allUsers = cur.fetchall()

    if allUsers:
        sql ="select _id, name, email, password, isAdmin from users where email="+ "'"+email+"'"
        cur.execute(sql)
        user = cur.fetchall()
        if user:
            resp = make_response({"exists": "Email Already Exists"})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        else:
            sql = "INSERT INTO users(name, email, password) VALUES(%s, %s, %s)"
            try:
                cur.execute(sql, (name, email, pw_hash))
                cur.connection.commit()      
                resp = make_response({"msg": "user created"})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            except MySQLdb.Error as err:
                resp = make_response({"err": err.args[1]})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp       
    else:
        admin_hash = bcrypt.generate_password_hash("I@manartist1")
        cur.execute("CREATE TABLE users(_id int(50) not null auto_increment PRIMARY KEY, name varchar(200) NOT NULL ,email varchar(80) NOT NULL UNIQUE,password varchar(800) NOT NULL,isAdmin INT DEFAULT 0, suspended INT DEFAULT 0)")
        sql1 = "INSERT INTO users(name, email, password, isAdmin) VALUES(%s, %s, %s, %s)"
        cur.execute(sql1, ('Mitch', 'mitchjaga@gmail.com', admin_hash, 1))
        cur.connection.commit()
        sql2 = "INSERT INTO users(name, email, password) VALUES(%s, %s, %s)"
        try:
            cur.execute(sql2, (name, email, pw_hash))
            cur.connection.commit()      
            resp = make_response({"msg": "user created"})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        except MySQLdb.Error as err:
            resp = make_response({"err": err.args[1]})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
                      
    


@app.route('/upload-image', methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
    
        if file and allowed_file(file.filename):
            pat = UPLOAD_FOLDER + "/" + file.filename
            try:
                file.save(pat)
                resp = make_response({"msg": "Image saved"})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            except:
                resp = make_response({"err": "Image not saved"})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
        else:
            resp = make_response({"err": "Image Type not supported"})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

@app.route('/delete-image/<fileName>', methods=["GET"])
def delete_file(fileName):
    pat = UPLOAD_FOLDER+ "/" +fileName
    try:
        os.remove(pat)
        resp = make_response({"msg": "Image removed"})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except:
        resp = make_response({"err": "Image does not exist"})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

@app.route('/api/product/<_id>', methods=["GET"])
def get_a_product(_id):
    cur = mysql.connection.cursor()

    try:
        sql = "SELECT * FROM products WHERE _id="+str(_id)
        cur.execute(sql)
        results = cur.fetchall()
        product = products_serializer(results)
        resp = make_response({"product": product})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except MySQLdb.Error as err:
        resp = make_response({"err": err.args[1]})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

@app.route('/api/category/<_id>', methods=["GET"])
def get_a_cat(_id):
    cur = mysql.connection.cursor()

    try:
        sql = "SELECT * FROM categories WHERE _id="+str(_id)
        cur.execute(sql)
        results = cur.fetchall()
        category = categories_serializer(results)
        resp = make_response({"category": category})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except MySQLdb.Error as err:
        resp = make_response({"err": err.args[1]})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

@app.route('/api/categories/<cat>', methods=["GET"])
def get_a_category(cat):
    cur = mysql.connection.cursor()

    sql = "SELECT * FROM products WHERE category="+"'"+ cat + "'"
    try:
        cur.execute(sql)
        results = cur.fetchall()
        products = products_serializer(results)
        resp = make_response({"products": products})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except MySQLdb.Error as err:
        resp = make_response({"err": err.args[1]})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

@app.route('/api/products/offer', methods=["GET"])
def get_offer_products():
    cur = mysql.connection.cursor()

    try:
        cur.execute("SELECT * FROM products WHERE offer > 0 ORDER BY RAND()")
        results = cur.fetchall()
        products = products_serializer(results)
        resp = make_response({"products_with_offer": products})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except MySQLdb.Error as err:
        resp = make_response({"err": err.args[1]})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

@app.route('/api/admin/products', methods=["POST", "GET"])
def add_products():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        request_data = json.loads(request.data)
        title = request_data["title"]
        slug = title.replace(' ', '-').lower()
        description = request_data['description']
        price = request_data['price']
        category = request_data['category']
        image = request_data['image']
        rating = request_data['rating']
        reviews = request_data['reviews']

        cur.execute("show tables like 'products';")
        result = cur.fetchall()

        if result:
            try:
                cur.execute("INSERT INTO products(title, slug, description, price, category, image, origPrice, rating, reviews) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)", (title, slug, description, price, category, image, price, rating, reviews))
                cur.connection.commit()
                cur.close()

                resp = make_response({"msg": "Product successfully added"})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            except MySQLdb.Error as err:
                resp = make_response({"err": err.args[1]})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            
        else:
            try:
                sql ='CREATE TABLE products(_id int(50) not null auto_increment PRIMARY KEY,title varchar(80) NOT NULL,slug varchar(80) NOT NULL,description varchar(200) NOT NULL,price INT NOT NULL,category varchar(40) NOT NULL,image varchar(200) NOT NULL,countInStock INT DEFAULT 120, offer INT DEFAULT 0, origPrice INT, rating FLOAT, reviews INT ,UNIQUE (slug));'
                cur.execute(sql)
            except MySQLdb.Error as err:
                resp = make_response({"err": err.args[1]})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            
            try:
                cur.execute("INSERT INTO products(title, slug, description, price, category, image, origPrice, rating, reviews) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s);", (title, slug, description, price, category, image, price, rating, reviews))
                cur.connection.commit()
                cur.close()
                resp = make_response({"msg": "Product successfully added"})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            except MySQLdb.Error as err:
                resp = make_response({"err": err.args[1]})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
    elif request.method == "GET":
        try:
            cur.execute("SELECT * FROM products ORDER BY RAND()")
            results = cur.fetchall()
            products = products_serializer(results)
            resp = make_response({"products": products})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        except MySQLdb.Error as err:
            resp = make_response({"err": err.args[1]})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

@app.route('/api/admin/product/<_id>/offer/<action>', methods=["GET", "POST"])
def offer(_id, action):
    cur = mysql.connection.cursor()

    sql = "SELECT origPrice FROM products WHERE _id="+"'"+ _id + "'"
    cur.execute(sql)

    origPrice = cur.fetchall()
    origPrice = origPrice[0][0]

    if request.method == "POST":
        request_data = json.loads(request.data)
        value = request_data["offer"]
        value = int(value)

        off = (value/100)*origPrice
        newPrice = origPrice - off
        sql1 = "UPDATE products SET offer="+"'"+str(value)+"'"+ "WHERE _id="+"'"+_id+"'"
        sql2 = "UPDATE products SET price="+ "'"+str(newPrice)+"'" + "WHERE _id="+"'"+_id+"'"

        try:
            cur.execute(sql1)
            cur.execute(sql2)
            cur.connection.commit()
            cur.close()
            resp = make_response({"msg": "Offer Added"})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        except MySQLdb.Error as err:
            resp = make_response({"err": err.args[1]})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

    elif request.method == "GET":
        sql = "UPDATE products SET offer='0', price="+"'"+str(origPrice)+"'"+ "WHERE _id="+"'"+_id+"'"
        try:
            cur.execute(sql)
            cur.connection.commit()
            cur.close()
            resp = make_response({"msg": "Offer Removed"})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        except MySQLdb.Error as err:
            resp = make_response({"err": err.args[1]})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp


@app.route('/api/products/delete/<_id>', methods=["GET"])
def remove_product(_id):
    cur = mysql.connection.cursor()
    sql = "DELETE FROM products WHERE _id=" + "'" + _id + "'"
    try:
        cur.execute(sql)
        cur.connection.commit()
        cur.close()
        resp = make_response({"msg": "Product Deleted"})        
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except  MySQLdb.Error as err:
        resp = make_response({"err": err.args[1]})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

@app.route('/api/categories/delete/<_id>', methods=["GET"])
def remove_category(_id):
    cur = mysql.connection.cursor()
    sql = "DELETE FROM categories WHERE _id=" + "'" + _id + "'"
    try:
        cur.execute(sql)
        cur.connection.commit()
        cur.close()
        resp = make_response({"msg": "Category Deleted"})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except  MySQLdb.Error as err:
        resp = make_response({"err": err.args[1]})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
        
@app.route('/api/products/edit/<_id>', methods=["POST", "GET"])
def edit_product(_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        request_data = json.loads(request.data)
        title = request_data["title"]
        description = request_data["description"]
        price = request_data["price"]
        category = request_data["category"]
        slug = title.replace(' ', '-').lower()
        offer = request_data["offer"]
        offer = int(offer)

        off = (offer/100)* int(price)
        newPrice =  int(price) - off

        sql = "UPDATE products SET title= %s, slug=%s, description=%s, category=%s, price=%s, origPrice=%s WHERE _id=%s"

        try:
            cur.execute(sql, (title, slug, description, category,newPrice, price, _id))
            cur.connection.commit()
            cur.close()
            resp = make_response({"msg": "Product Updated"})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        except MySQLdb.Error as err:
            resp = make_response({"err": err.args[0]})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

@app.route('/api/categories/edit/<_id>', methods=["POST", "GET"])
def edit_category(_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        request_data = json.loads(request.data)
        title = request_data["title"]
        slug = title.replace(' ', '-').lower()

        sql = "UPDATE categories SET title= %s, slug=%s WHERE _id=%s"

        try:
            cur.execute(sql, (title, slug, _id))
            cur.connection.commit()
            cur.close()
            resp = make_response({"msg": "Category Updated"})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        except MySQLdb.Error as err:
            resp = make_response({"err": err.args[0]})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

@app.route('/api/admin/categories', methods=["POST", "GET"])
def add_category():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        request_data = json.loads(request.data)
        title = request_data["title"]
        slug = title.replace(' ', '-').lower()

        cur.execute("show tables like 'categories';")
        result = cur.fetchall()

        if result:
            try:
                cur.execute("INSERT INTO categories(title, slug) VALUES(%s, %s);", (title, slug))
                cur.connection.commit()
                cur.close()
                resp = make_response({"msg": "Category successfully added"})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            except MySQLdb.Error as err:
                resp = make_response({"err": err.args[1]})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
        else:
            try:
                sql ='CREATE TABLE categories(_id int(50) not null auto_increment primary key, title varchar(80) NOT NULL,slug varchar(80) NOT NULL, UNIQUE (slug))'
                cur.execute(sql)
                
            except MySQLdb.Error as err:
                resp = make_response({"err": err.args[1]})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp

            try:
                cur.execute("INSERT INTO categories(title, slug) VALUES(%s, %s);", (title, slug))
                cur.connection.commit()
                cur.close()
                resp = make_response({"msg": "Category successfully added"})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            except MySQLdb.Error as err:
                resp = make_response({"err": err.args[1]})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
    elif request.method == "GET":
        try:
            cur.execute("SELECT * FROM categories")
            results = cur.fetchall()
            categories = categories_serializer(results)
            resp = make_response({"categories": categories})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        except MySQLdb.Error as err:
            resp = make_response({"err": err.args[1]})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

@app.route('/api/orders/<userId>', methods=["POST", "GET"])
def place_order(userId):
    cur = mysql.connection.cursor()

    if request.method == "POST":
        products = request.json.get("products", None)
        cur.execute("SHOW TABLES LIKE 'orders'")
        orders = cur.fetchall()

        if orders:
            cur.executemany("INSERT INTO orders(userId,productId, price, qty) VALUES(%(userId)s,%(productId)s,%(price)s,%(qty)s)", (products))
            cur.connection.commit()

        else:
            cur.execute("CREATE TABLE orders(userId INT, productId INT, ordertime datetime DEFAULT now(), price INT, qty INT)")
            cur.executemany("INSERT INTO orders(userId,productId, price, qty) VALUES(%(userId)s,%(productId)s,%(price)s,%(qty)s)", (products))
            cur.connection.commit()

        for product in products:
            newStock = product["countInStock"] - product["qty"]
            cur.execute("UPDATE products SET countInStock=%s WHERE _id=%s", (newStock, product["productId"]))
            cur.connection.commit()

        cur.close()
        resp = make_response({"msg": "ok"})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    elif request.method == "GET":
        cur.execute("SELECT orders.userId, orders.productId, orders.ordertime, orders.price, orders.qty, products.title FROM orders, products WHERE orders.productId = products._id AND orders.userId=%s", (userId))
        results = cur.fetchall()
        cur.execute("SELECT SUM(price) FROM orders WHERE userId=%s", (userId))
        total = cur.fetchall()
        ords = orders_serializer(results)
        total1 = int(total[0][0])
        resp = make_response({"orders": ords, "totalPrice": total1 })
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

@app.route('/api/shipping/address/<userId>', methods=["POST", "GET"])
def shipping_address(userId):
    cur = mysql.connection.cursor()

    if request.method == "POST":
        fullName = request.json.get("fullName", None)
        address = request.json.get("address", None)
        city = request.json.get("city", None)
        postalCode = request.json.get("postalCode", None)
        country = request.json.get("country", None)

        cur.execute("show tables like 'addresses'")
        addresses = cur.fetchall()

        if addresses:
            sql = "INSERT INTO addresses(_id , fullname, address, city, postalcode, country) VALUES(%s,%s,%s,%s,%s,%s);"
            try:
                cur.execute(sql, (userId, fullName, address, city, postalCode, country))
                cur.connection.commit()
                cur.close()
                resp = make_response({"msg": "User address added"})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            except MySQLdb.Error as err:
                resp = make_response({"err": err.args[1]})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
        else:
            try:
                sql ='CREATE TABLE addresses(_id int(50) not null primary key, fullname varchar(80) NOT NULL,address varchar(80) NOT NULL, city varchar(80) NOT NULL, postalcode varchar(80) NOT NULL, country varchar(80) NOT NULL)'
                cur.execute(sql)
                
            except MySQLdb.Error as err:
                resp = make_response({"err": err.args[1]})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp

            try:
                sql1 = "INSERT INTO addresses(_id , fullname, address, city, postalcode, country) VALUES(%s,%s,%s,%s,%s,%s)"
                cur.execute(sql1, (userId, fullName, address, city, postalCode, country))
                cur.connection.commit()
                cur.close()
                resp = make_response({"msg": "User address added"})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            except MySQLdb.Error as err:
                resp = make_response({"err": err.args[1]})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
    elif request.method == "GET":
        cur.execute("show tables like 'addresses'")
        addresses = cur.fetchall()

        if addresses:
            cur.execute("SELECT * FROM addresses WHERE _id=%s", (userId))
            address = cur.fetchall()
            if address:
                address = address[0]
                resp = make_response({"address": "Current User has an address"})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            else:
                resp = make_response({"msg": "Current User has no address"})
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
        else:
            resp = make_response({"msg": "Current User has no address"})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp



if __name__ == "__main__":
    app.run(debug=True)