# Typings for database abstractions and some related exceptions

from typing import TypedDict

class Asset:
    id: str
    filename: str
    value: bytes
    def __init__(self, id, filename, value):
        self.id = id
        self.filename = filename
        self.value = value
    def __dict__(self):
        return {
            "id": self.id,
            "filename": self.filename
        }

class AssetNotFoundException(Exception):
    def __init__(self, asset_id):
        super().__init__(f"Asset for id '{asset_id}' not found.")

class Profile:
    id: str
    user_id: str
    description: str
    image_asset: Asset | None
    banner_asset: Asset | None
    def __init__(self, id, user_id, description, image_asset, banner_asset):
        self.id = id
        self.user_id = user_id
        self.description = description
        self.image_asset = image_asset
        self.banner_asset = banner_asset
    
    def __dict__ (self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "description": self.description,
            "image_asset": self.image_asset.__dict__() if self.image_asset else None,
            "banner_asset": self.banner_asset.__dict__() if self.banner_asset else None
        }

class ProfileEditable(TypedDict):
    description: str
    image_asset_id: int | None
    banner_asset_id: int | None

class User:
    id: str
    username: str
    password_hash: str
    require_new_password: bool
    profile: Profile
    is_admin: bool
    def __init__(self, id, username, password_hash, require_new_password, is_admin, profile):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.require_new_password = require_new_password == 1
        self.is_admin = is_admin == 1
        self.profile = profile

    def __dict__(self):
        return {
            "id": self.id,
            "username": self.username,
            "password_hash": self.password_hash,
            "require_new_password": self.require_new_password,
            "is_admin": self.is_admin,
            "profile": self.profile.__dict__()
        }

class UserEditable(TypedDict):
    username: str
    password_hash: str
    require_new_password: bool

class UserExistsException(Exception):
    def __init__(self, username):
        super().__init__(f"User '{username}' already exists!")

class UserNotFoundException(Exception):
    def __init__(self, username):
        super().__init__(f"User '{username}' not found.")
        
class ProfileNotFoundException(Exception):
    def __init__(self, user_id):
        super().__init__(f"Profile for user_id '{user_id}' not found.")

class Category:
    id: int
    name: str
    def __init__(self, id, name):
        self.id = id
        self.name = name

class Challenge:
    id: int
    created: int
    title: str
    body: str
    accepts_submissions: bool
    category_id: str
    category_name: str
    author_image_id: int
    votes: int
    has_my_vote: bool
    def __init__(self, id, created, title, body, accepts_submissions, category_id, category_name, author_name, author_image_id, votes, has_my_vote):
        self.id = id
        self.created = created
        self.title = title
        self.body = body
        self.accepts_submissions = accepts_submissions == 1
        self.category_id = category_id
        self.category_name = category_name
        self.author_name = author_name
        self.author_image_id = author_image_id
        self.votes = votes
        self.has_my_vote = has_my_vote == 1

    def __dict__(self):
        return {
            "id": self.id,
            "created": self.created,
            "title": self.title,
            "body": self.body,
            "category_name": self.category_name,
            "author_name": self.author_name,
            "author_image_id": self.author_image_id,
            "votes": self.votes,
            "has_my_vote": self.has_my_vote
        }
    
class ChallengeEditable(TypedDict):
    title: str
    body: str
    category_id: int
    accepts_submissions: bool
    
class ChallengeNotFoundException(Exception):
    def __init__(self, challenge_id):
        super().__init__(f"Challenge'{challenge_id}' not found.")
