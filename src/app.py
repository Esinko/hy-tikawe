from flask import Flask, Response, redirect, render_template, request, send_from_directory, session
from util.database import AbstractDatabase, AssetNotFoundException, ChallengeNotFound, DatabaseConnection, ProfileEditable, UserNotFoundException
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from util.filetype import filename_to_file_type

# Initialize database
database_params = ("./main.db", "./db/schema.sql", "./db/init.sql")
database_connection = DatabaseConnection(*database_params).open()
database_connection.close()

# Initialize Flask
app = Flask(__name__)
app.secret_key = "TOTALLY_SECRET_KEY"

# MARK: Filters
@app.template_filter("epoch_to_date")
def epoch_to_date_filter(epoch):
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")

# Public dir route
@app.route("/public/<path>")
def public(path):
    return send_from_directory("public", path)

# MARK: Pages
@app.route("/")
def home():
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    categories = database.get_categories()
    challenges = database.get_challenges(session["user"]["id"] if "user" in session else -1 , None, 0)
    database.connection.close()
    return render_template("./home.html", categories=categories, challenges=challenges, autofocus_id=-1)

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

@app.get("/new-post")
def new_post():
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    categories = database.get_categories()
    database.connection.close()
    return render_template("./new-post.html", categories=categories)

@app.get("/chall/<challenge_id>")
def challenge(challenge_id):
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    categories = database.get_categories()
    try:
        challenge = database.get_challenge(session["user"]["id"] if "user" in session else -1, challenge_id)
        database.connection.close()
        return render_template("./challenge.html", categories=categories, challenge=challenge)
    except ChallengeNotFound:
        database.connection.close()
        return render_template("./challenge.html", categories=categories, challenge=challenge)
    except Exception as err:
        database.connection.close()
        print("ERR", err)
        return "Internal Server Error.", 500

@app.get("/me")
def profile_me():
    return profile(session["user"]["username"])

@app.get("/me/edit")
def profile_edit():
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    categories = database.get_categories()
    user = database.get_user(session["user"]["username"])
    database.connection.close()
    return render_template("./profile-edit.html", profile=user.__dict__()["profile"], username=user.username, categories=categories)

@app.get("/u/<username>")
def profile(username):
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    categories = database.get_categories()
    try:
        user = database.get_user(username)
        database.connection.close()
    except UserNotFoundException:
        return redirect("/")
    return render_template("./profile.html", profile=user.__dict__()["profile"], username=username, categories=categories)

@app.get("/a/<id>")
def asset(id):
    database = AbstractDatabase(DatabaseConnection(*database_params).open())
    try:
        asset = database.get_asset(id)
        database.connection.close()
    except AssetNotFoundException:
        return redirect("/")

    print("GOT ASSET", asset)
    response = Response(asset.value)
    response.headers["Content-Type"] = filename_to_file_type(asset.filename)
    return response


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
    except Exception as err:
        print("ERR", err)
        return "Internal Server Error.", 500

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
        return "Internal Server Error.", 500
    
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

@app.post("/api/profile/edit")
def api_profile_edit():
    username = session["user"]["username"]
    user_id = session["user"]["id"]
    description = request.form["description"]
    image_file = request.files["image"]
    banner_file = request.files["banner"]

    # Check required fields
    if not description:
        return "Some required field missing.", 400
    
    try:
        database = AbstractDatabase(DatabaseConnection(*database_params).open())
        user = database.get_user(username)

        print("> GOT USER", user)

        # Delete existing assets, if necessary
        if user.profile.banner_asset and banner_file:
            print("> Remove banner")
            database.delete_asset(user.profile.banner_asset.id)
        if user.profile.image_asset and image_file:
            print("> Remove image")
            database.delete_asset(user.profile.image_asset.id)

        # Create new assets, if necessary
        image_file_id = user.profile.image_asset.id if user.profile.image_asset else None
        banner_file_id = user.profile.banner_asset.id if user.profile.banner_asset else None
        if image_file:
            print("> Create image")
            new_image = database.create_asset(image_file.filename, image_file.stream.read())
            image_file_id = new_image.id
        if banner_file:
            print("> Create banner")
            new_banner = database.create_asset(banner_file.filename, banner_file.stream.read())
            banner_file_id = new_banner.id

        # Perform edits
        new_profile: ProfileEditable = {
            "image_asset_id": image_file_id,
            "banner_asset_id": banner_file_id,
            "description": description
        }
        print("Sending:", new_profile)
        database.edit_profile(user_id, new_profile)
        return redirect("/me")
    except Exception as err:
        print("ERR", err)
        return "Internal Server Error.", 500

@app.post("/api/post/challenge")
def api_post_challenge():
    user_id = session["user"]["id"]
    title = request.form["title"]
    category_id = int(request.form["category"])
    description = request.form["description"]

    if not title or not category_id or not description:
        return "Some required field missing.", 400

    try:
        # Create database connection
        database = AbstractDatabase(DatabaseConnection(*database_params).open())

        # Check challenge category is valid
        categories = database.get_categories()
        if not any(category.id == category_id for category in categories):
            return "Invalid category.", 400
            
        # Create challenge post
        post_id = database.create_challenge(title, description, category_id, user_id)
        return redirect(f"/chall/{post_id}")
        
    except Exception as err:
        print("ERR", err)
        return "Internal Server Error.", 500
    