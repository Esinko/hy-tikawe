from flask import Flask, redirect, render_template, request, send_from_directory, session
from util.database import AbstractDatabase, DatabaseConnection, UserNotFoundException
from werkzeug.security import check_password_hash, generate_password_hash

# Initialize database
database_params = ("./main.db", "./db/schema.sql", "./db/init.sql")
database_connection = DatabaseConnection(*database_params).open()
database_connection.close()

# Initialize Flask
app = Flask(__name__)
app.secret_key = "TOTALLY_SECRET_KEY"

# Public dir route
@app.route("/public/<path>")
def public(path):
    return send_from_directory("public", path)

# MARK: Pages
@app.route("/")
def home():
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    categories = database.get_categories()
    database.connection.close()
    return render_template("./home.html", categories=categories)

@app.route("/login")
def login():
    return render_template("./login.html")

@app.route("/register")
def register():
    return render_template("./register.html")

@app.get("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.get("/me")
def profile_me():
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    categories = database.get_categories()
    database.connection.close()
    return render_template("./profile.html", profile=session["user"]["profile"], username=session["user"]["username"], categories=categories)

@app.get("/u/<username>")
def profile(username):
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    categories = database.get_categories()
    try:
        user = database.get_user(username)
    except UserNotFoundException:
        redirect("/")
    database.connection.close()
    return render_template("./profile.html", profile=user.__dict__()["profile"], username=username, categories=categories)

# MARK: API

@app.post("/api/login")
def api_login():
    username = request.form["username"]
    password = request.form["password"]
    print(username, password)
    if not username or not password:
        return "Username or password missing.", 400

    # Attempt to get user
    try:
        database = AbstractDatabase(DatabaseConnection(*database_params).open())
        user = database.get_user(username)
        database.connection.close()
    except UserNotFoundException:
        return redirect("/login?fail")
    except Exception:
        return "Internal Server Error", 500

    # Check password
    if check_password_hash(user.password_hash, password):
        session["user"] = user.__dict__()
        return redirect("/")
    else:
        return redirect("/login?fail")
    
@app.post("/api/register")
def api_register():
    username = request.form["username"]
    password = request.form["password"]
    password_again = request.form["password-again"]
    if not username or not password or not password_again:
        return "Some required field missing.", 400

    # Make sure username is free
    try:
        database = AbstractDatabase(DatabaseConnection(*database_params).open())
        exists = database.user_exists(username)
        if exists:
            database.user_exists(username)
            return redirect("/register?taken")
    except Exception:
        return "Internal Server Error", 500
    
    # Check passwords match
    if password != password_again:
        return redirect("/register?mismatch")
    
    # Create user
    try:
        user = database.create_user(username, generate_password_hash(password))
        session["user"] = user.__dict__()
        return redirect("/")
    except:
        return "Internal Server Error", 500

