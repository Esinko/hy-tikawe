from flask import redirect, request, session
from database.params import database_params
from database.abstract import AbstractDatabase, DatabaseConnection, ProfileEditable, UserNotFoundException
from werkzeug.security import check_password_hash, generate_password_hash

from util.has_permission import has_permission

# MARK: Login & Register
def api_login():
    if "username" not in request.form.keys() or "password" not in request.form.keys():
        return "Username or password missing.", 400

    username = request.form["username"]
    password = request.form["password"]

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
    
def api_register():
    if "username" not in request.form.keys() or "password" not in request.form.keys() or "password-again" not in request.form.keys():
        return "Username or password missing.", 400

    username = request.form["username"]
    password = request.form["password"]
    password_again = request.form["password-again"]

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

# MARK: Profiles
def api_profile_edit():
    if "user" not in session:
        return "Not logged in.", 401
    
    if "description" not in request.form.keys() or "image" not in request.files.keys() or "banner" not in request.files.keys():
        return "Incomplete data.", 400

    username = session["user"]["username"]
    user_id = session["user"]["id"]
    description = request.form["description"]
    image_file = request.files["image"]
    banner_file = request.files["banner"]

    try:
        database = AbstractDatabase(DatabaseConnection(*database_params).open())
        user = database.get_user(username)

        # Delete existing assets, if necessary
        if user.profile.banner_asset and banner_file:
            database.delete_asset(user.profile.banner_asset.id)
        if user.profile.image_asset and image_file:
            database.delete_asset(user.profile.image_asset.id)

        # Create new assets, if necessary
        image_file_id = user.profile.image_asset.id if user.profile.image_asset else None
        banner_file_id = user.profile.banner_asset.id if user.profile.banner_asset else None
        if image_file:
            new_image = database.create_asset(image_file.filename, image_file.stream.read())
            image_file_id = new_image.id
        if banner_file:
            new_banner = database.create_asset(banner_file.filename, banner_file.stream.read())
            banner_file_id = new_banner.id

        # Perform edits
        new_profile: ProfileEditable = {
            "image_asset_id": image_file_id,
            "banner_asset_id": banner_file_id,
            "description": description
        }
        database.edit_profile(user_id, new_profile)
        return redirect("/me")
    except Exception as err:
        print("ERR", err)
        return "Internal Server Error.", 500

# MARK: Post Challenge
def api_post_challenge():
    if "user" not in session:
        return "Not logged in.", 401
    
    if "title" not in request.form.keys() or "category" not in request.form.keys() or "body" not in request.form.keys() or "accepts_submissions" not in request.form.keys():
        return "Incomplete data.", 400

    user_id = session["user"]["id"]
    title = request.form["title"]
    body = request.form["body"]
    try:
        category_id = int(request.form["category"])
        accepts_submissions = int(request.form["accepts_submissions"]) == 1
    except:
        return "Invalid data.", 400

    try:
        # Create database connection
        database = AbstractDatabase(DatabaseConnection(*database_params).open())

        # Check challenge category is valid
        categories = database.get_categories()
        if not any(category.id == category_id for category in categories):
            return "Invalid category.", 400
            
        # Create challenge post
        post_id = database.create_challenge(title, body, category_id, user_id, accepts_submissions)
        return redirect(f"/chall/{post_id}")
        
    except Exception as err:
        print("ERR", err)
        return "Internal Server Error.", 500

# MARK: Edit Challenge
def api_edit_challenge():
    if "user" not in session:
        return "Not logged in.", 401
    
    if "title" not in request.form.keys() or "category" not in request.form.keys() or "id" not in request.form.keys() or "accepts_submissions" not in request.form.keys():
        return "Incomplete data.", 400

    title = request.form["title"]
    body = request.form["body"]
    challenge_id = request.form["id"]
    try:
        accepts_submissions = int(request.form["accepts_submissions"]) == 1
        category_id = int(request.form["category"])
    except:
        return "Invalid data.", 400

    try:
        # Create database connection
        database = AbstractDatabase(DatabaseConnection(*database_params).open())

        # Check challenge category is valid
        categories = database.get_categories()
        if not any(category.id == category_id for category in categories):
            return "Invalid category.", 400
        
        # Check challenge already exists
        if not database.challenge_exists(challenge_id):
            return "Challenge does not exit.", 400
        
        # Check permission
        challenge = database.get_challenge(session["user"]["id"], challenge_id)
        if not has_permission(session["user"], "edit", "challenge", challenge.author_id):
            return "Permission denied.", 401
            
        # Edit challenge post
        # TODO: Add edited date?
        database.edit_challenge(challenge_id, {
            "body": body,
            "category_id": category_id,
            "title": title,
            "accepts_submissions": accepts_submissions
        })
        return redirect(f"/chall/{challenge_id}")
        
    except Exception as err:
        print("ERR", err)
        return "Internal Server Error.", 500
    
# MARK: Delete Challenge
def api_delete_challenge():
    if "user" not in session:
        return "Not logged in.", 401
    
    if "id" not in request.form.keys():
        return "Incomplete data.", 400
    
    challenge_id = request.form["id"]

    try:
        # Create database connection
        database = AbstractDatabase(DatabaseConnection(*database_params).open())
        
        # Check challenge already exists
        if not database.challenge_exists(challenge_id):
            return "Challenge does not exit.", 400
        
        challenge = database.get_challenge(session["user"]["id"], challenge_id)
        
        # Check permission
        if not has_permission(session["user"], "delete", "challenge", challenge.author_id):
            return "Permission denied.", 401

        # Delete challenge
        database.remove_challenge(challenge_id)
        return redirect(f"/")
        
    except Exception as err:
        print("ERR", err)
        return "Internal Server Error.", 500

# MARK: Vote
def api_vote(type, target_id):
    if "user" not in session:
        return "Not logged in.", 401
    
    if "vote_action" not in request.form.keys() or "from_page" not in request.form.keys():
        return "Incomplete data.", 400

    user_id = session["user"]["id"]
    vote_action  = request.form["vote_action"]
    from_page = request.form["from_page"]
    
    try:
        # Create database connection
        database = AbstractDatabase(DatabaseConnection(*database_params).open())

        # Vote for or remove
        if vote_action == "1":
            database.vote_for(type, target_id, user_id)
        else:
            database.remove_vote_from(type, target_id, user_id)
        
        # Redirect back
        # Needs separate rules for each place the request can be from to properly focus/go to the right place back
        if from_page.startswith("/chall/"):
            return redirect("/chall/" + target_id)
        elif from_page == "/":
            return redirect("/#chall-" + target_id)
        else:
            return redirect(from_page + "#chall-" + target_id)
        
    except Exception as err:
        print("ERR", err)
        return "Internal Server Error.", 500 
