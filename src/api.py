from flask import redirect, request, session
from database.abstract import ProfileEditable, UserNotFoundException
from werkzeug.security import check_password_hash, generate_password_hash
from util.has_permission import has_permission
from util.get_db import get_db

# MARK: Login & Register
def api_login():
    if "username" not in request.form.keys() or "password" not in request.form.keys():
        return "Username or password missing.", 400

    username = request.form["username"]
    password = request.form["password"]

    # Attempt to get user
    try:
        user = get_db().get_user(username)
    except UserNotFoundException:
        return redirect("/login?fail")
    except Exception as err:
        print("Login Error:", err)
        return "Internal Server Error.", 500

    # Check password
    if check_password_hash(user.password_hash, password):
        session["user"] = user.to_dict()
        return redirect("/")
    else:
        return redirect("/login?fail")
    
def api_register():
    if (
        "username" not in request.form.keys() or
        "password" not in request.form.keys() or
        "password-again" not in request.form.keys()
    ):
        return "Username or password missing.", 400

    username = request.form["username"]
    password = request.form["password"]
    password_again = request.form["password-again"]

    # Make sure username is free
    try:
        exists = get_db().user_exists(username)
        if exists:
            return redirect("/register?taken")
    except Exception:
        return "Internal Server Error.", 500
    
    # Check passwords match
    if password != password_again:
        return redirect("/register?mismatch")
    
    # Create user
    try:
        user = get_db().create_user(username, generate_password_hash(password))
        session["user"] = user.to_dict()
        return redirect("/")
    except:
        return "Internal Server Error", 500

# MARK: Profiles
def api_profile_edit():
    if "user" not in session:
        return "Not logged in.", 401
    
    if (
        "description" not in request.form.keys() or
        "image" not in request.files.keys() or
        "banner" not in request.files.keys()
    ):
        return "Incomplete data.", 400

    username = session["user"]["username"]
    user_id = session["user"]["id"]
    description = request.form["description"]
    image_file = request.files["image"]
    banner_file = request.files["banner"]

    try:
        # Get user
        user = get_db().get_user(username)

        # Delete existing assets, if necessary
        if user.profile.banner_asset and banner_file:
            get_db().delete_asset(user.profile.banner_asset.id)
        if user.profile.image_asset and image_file:
            get_db().delete_asset(user.profile.image_asset.id)

        # Create new assets, if necessary
        image_file_id = user.profile.image_asset.id if user.profile.image_asset else None
        banner_file_id = user.profile.banner_asset.id if user.profile.banner_asset else None
        if image_file:
            new_image = get_db().create_asset(image_file.filename,
                                                        image_file.stream.read())
            image_file_id = new_image.id
        if banner_file:
            new_banner = get_db().create_asset(banner_file.filename,
                                                        banner_file.stream.read())
            banner_file_id = new_banner.id

        # Perform edits
        new_profile: ProfileEditable = {
            "image_asset_id": image_file_id,
            "banner_asset_id": banner_file_id,
            "description": description
        }
        get_db().edit_profile(user_id, new_profile)

        # Refresh session
        session["user"] = get_db().get_user(username).to_dict() 
        return redirect("/me")
    except Exception as err:
        print("Profile Edit Error:", err)
        return "Internal Server Error.", 500

# MARK: Post Challenge
def api_post_challenge():
    if "user" not in session:
        return "Not logged in.", 401
    
    if (
        "title" not in request.form.keys() or
        "category" not in request.form.keys() or
        "body" not in request.form.keys() or
        "accepts_submissions" not in request.form.keys()
    ):
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
        # Check challenge category is valid
        categories = get_db().get_categories()
        if not any(category.id == category_id for category in categories):
            return "Invalid category.", 400
            
        # Create challenge post
        post_id = get_db().create_challenge(title,
                                                body,
                                                category_id,
                                                user_id,
                                                accepts_submissions)
        return redirect(f"/chall/{post_id}")
        
    except Exception as err:
        print("Challenge Post Error:", err)
        return "Internal Server Error.", 500

# MARK: Edit Challenge
def api_edit_challenge():
    if "user" not in session:
        return "Not logged in.", 401
    
    if (
        "title" not in request.form.keys() or
        "category" not in request.form.keys() or
        "id" not in request.form.keys() or
        "accepts_submissions" not in request.form.keys()
    ):
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
        # Check challenge category is valid
        categories = get_db().get_categories()
        if not any(category.id == category_id for category in categories):
            return "Invalid category.", 400
        
        # Check challenge already exists
        if not get_db().challenge_exists(challenge_id):
            return "Challenge does not exit.", 400
        
        # Check permission
        challenge = get_db().get_challenge(session["user"]["id"], challenge_id)
        if not has_permission(session["user"], "edit", "challenge", challenge.author_id):
            return "Permission denied.", 401
            
        # Edit challenge post
        # TODO: Add edited date?
        get_db().edit_challenge(challenge_id, {
            "body": body,
            "category_id": category_id,
            "title": title,
            "accepts_submissions": accepts_submissions
        })
        return redirect(f"/chall/{challenge_id}")
        
    except Exception as err:
        print("Challenge Edit Error", err)
        return "Internal Server Error.", 500
    
# MARK: Delete Challenge
def api_delete_challenge():
    if "user" not in session:
        return "Not logged in.", 401
    
    if "id" not in request.form.keys():
        return "Incomplete data.", 400
    
    challenge_id = request.form["id"]

    try:
        # Check challenge already exists
        if not get_db().challenge_exists(challenge_id):
            return "Challenge does not exit.", 400
        
        challenge = get_db().get_challenge(session["user"]["id"], challenge_id)
        
        # Check permission
        if not has_permission(session["user"], "delete", "challenge", challenge.author_id):
            return "Permission denied.", 401

        # Delete challenge
        get_db().remove_challenge(challenge_id)
        return redirect(f"/")
        
    except Exception as err:
        print("Challenge Delete Error:", err)
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
        # Vote for or remove
        if vote_action == "1":
            get_db().vote_for(type, target_id, user_id)
        else:
            get_db().remove_vote_from(type, target_id, user_id)
        
        # Redirect back
        # Needs separate rules for each place the request can be from to properly focus/go to the right place back
        if from_page.startswith("/chall/"):
            if type == "comment":
                return redirect(from_page + "#com-" + target_id)
            
            return redirect("/chall/" + target_id)
        elif from_page == "/":
            return redirect("/#chall-" + target_id)
        else:
            return redirect(from_page + "#chall-" + target_id)
        
    except Exception as err:
        print("Vote Error:", err)
        return "Internal Server Error.", 500 

# MARK: Comment
def api_post_comment():
    if "user" not in session:
        return "Not logged in.", 401
    
    if "body" not in request.form.keys() or "challenge_id" not in request.form.keys():
        return "Incomplete data.", 400

    user_id = session["user"]["id"]
    challenge_id = request.form["challenge_id"]
    body = request.form["body"]

    try:
        # Check that challenge exists
        if not get_db().challenge_exists(challenge_id):
            return "Challenge does not exit.", 400
            
        # Create challenge comment
        comment_id = get_db().create_comment(challenge_id, body, user_id)
        return redirect(f"/chall/{challenge_id}/#c-{comment_id}")
        
    except Exception as err:
        print("Comment Post Error:", err)
        return "Internal Server Error.", 500

def api_edit_comment():
    if "user" not in session:
        return "Not logged in.", 401
    
    if "body" not in request.form.keys() or "id" not in request.form.keys():
        return "Incomplete data.", 400

    body = request.form["body"]
    comment_id = request.form["id"]

    try:
        # Check that comment exists
        if not get_db().comment_exists(comment_id):
            return "Comment does not exit.", 400
        
        # Check permission
        comment = get_db().get_comment(session["user"]["id"], comment_id)
        if not has_permission(session["user"], "edit", "comment", comment.author_id):
            return "Permission denied.", 401
            
        # Edit challenge post
        # TODO: Add edited date?
        get_db().edit_comment(comment_id, {
            "body": body
        })
        return redirect(f"/chall/{comment.challenge_id}/#com-{comment_id}")
        
    except Exception as err:
        print("Comment Edit Error", err)
        return "Internal Server Error.", 500
    
def api_delete_comment():
    if "user" not in session:
        return "Not logged in.", 401
    
    if "id" not in request.form.keys():
        return "Incomplete data.", 400
    
    comment_id = request.form["id"]

    try:
        # Check challenge already exists
        if not get_db().comment_exists(comment_id):
            return "Challenge does not exit.", 400
        
        comment = get_db().get_comment(session["user"]["id"], comment_id)
        
        # Check permission
        if not has_permission(session["user"], "delete", "challenge", comment.author_id):
            return "Permission denied.", 401

        # Delete challenge
        get_db().remove_comment(comment_id)
        return redirect(f"/chall/{comment.challenge_id}")
        
    except Exception as err:
        print("Comment Delete Error", err)
        return "Internal Server Error.", 500
    
# MARK: Submissions
