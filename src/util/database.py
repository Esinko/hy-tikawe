from sqlite3 import connect, Connection, Cursor
from pathlib import Path
from time import time
from typing import Any, List, Literal, Tuple, TypedDict

class DatabaseConnection:
    def __init__(self, database="./main.db", schema="./schema.sql", init="./init.sql"):
        self.database_filepath = database
        self.schema_filepath = schema
        self.init_filepath = init
        self.connection = None

    # Open the database connection
    def open(self):
        if self.connection != None:
            raise Exception("Database already opened!")

        # Read schema
        schema_file = Path(self.schema_filepath)
        if not schema_file.exists():
            raise FileNotFoundError("Schema file not found.")
        
        # Read init
        init_file = Path(self.init_filepath)
        if not init_file.exists():
            raise FileNotFoundError("Init file not found.")
        
        # Open database and write schema, if it does not exist
        database_file = Path(self.database_filepath)
        if not database_file.exists():
            schema = schema_file.read_text()
            self.connection = connect(database_file)
            self.connection.executescript(schema)

            # Do the db init too
            init = init_file.read_text()
            self.connection.executescript(init)

            self.connection.commit()
        else:
            self.connection = connect(database_file)

        return self
    
    def close(self):
        if not self.connection:
            raise Exception("Database not open!")
        self.connection.close()
    
    # Execute a command against the database
    def execute(self, query: str, parameters: Tuple[Any] | dict) -> Tuple[Connection, Cursor]:
        if not self.connection:
            raise Exception("Database not open!")
        cursor = self.connection.cursor()
        cursor.execute(query, parameters)
        self.connection.commit()
        return self.connection, cursor
    
    # Query the database
    def query(self, query = str, parameters: Tuple[Any] | dict = {}, limit: int = -1) -> list[Any]:
        if not self.connection:
            raise Exception("Database not open!")
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, parameters)
        except Exception as e:
            print("ERR", e)
        results = cursor.fetchmany(limit)
        cursor.close()
        return results
    

# MARK: Abstract types

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
    def __init__(self, id, username, password_hash, require_new_password, profile):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.require_new_password = require_new_password
        self.profile = profile

    def __dict__(self):
        return {
            "id": self.id,
            "username": self.username,
            "password_hash": self.password_hash,
            "require_new_password": self.require_new_password,
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
    category_name: str
    author_image_id: int
    votes: int
    has_my_vote: bool
    def __init__(self, id, created, title, body, category_name, author_name, author_image_id, votes, has_my_vote):
        self.id = id
        self.created = created
        self.title = title
        self.body = body
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
    
class ChallengeNotFoundException(Exception):
    def __init__(self, challenge_id):
        super().__init__(f"Challenge'{challenge_id}' not found.")

# MARK: Query table
sql_table = {
    "user_exists": "SELECT EXISTS (SELECT username FROM Users WHERE username = ?)",
    "create_user": "INSERT INTO Users (username, password_hash, require_new_password) VALUES (?, ?, False)",
    "get_user": "SELECT id, username, password_hash, require_new_password FROM Users WHERE username = ?",
    "edit_user": "UPDATE Users SET name = ?, password_hash = ?, require_new_password = ? WHERE name = ?",
    "create_profile": "INSERT INTO Profiles (user_id, description, image_asset_id, banner_asset_id) VALUES (?, '', NULL, NULL)",
    "get_profile": "SELECT id, description, image_asset_id, banner_asset_id FROM Profiles WHERE user_id = ?",
    "profile_exists": "SELECT EXISTS (SELECT user_id FROM Profiles WHERE user_id = ?)",
    "edit_profile": "UPDATE Profiles SET description = ?, image_asset_id = ?, banner_asset_id = ? WHERE user_id = ?",
    "create_asset": "INSERT INTO Assets (filename, value) VALUES (?, ?)",
    "get_asset": "SELECT filename, value FROM Assets WHERE id = ?",
    "delete_asset": "DELETE FROM Assets WHERE id = ?",
    "get_categories": "SELECT id, name FROM ChallengeCategories",
    "get_full_challenges": """
        SELECT 
            C.id, 
            C.created, 
            C.title, 
            C.body, 
            ChallengeCategories.name AS category_name, 
            Users.username, 
            Profiles.image_asset_id AS profile_image,
            COALESCE(VoteCounts.vote_count, 0) AS vote_count,
            CASE WHEN UserVotes.voter_id IS NOT NULL THEN 1 ELSE 0 END AS has_voted
        FROM Challenges C
        JOIN ChallengeCategories ON C.category_id = ChallengeCategories.id
        JOIN Users ON C.author_id = Users.id
        JOIN Profiles ON Profiles.user_id = Users.id
        LEFT JOIN (
            SELECT challenge_id, COUNT(*) AS vote_count
            FROM Votes
            WHERE challenge_id IS NOT NULL
            GROUP BY challenge_id
        ) AS VoteCounts ON VoteCounts.challenge_id = C.id
        LEFT JOIN (
            SELECT challenge_id, voter_id
            FROM Votes
            WHERE voter_id = ?
        ) AS UserVotes ON UserVotes.challenge_id = C.id
        WHERE (? IS NULL OR C.category_id = ?)
        ORDER BY C.created DESC
        LIMIT ? OFFSET ?;
    """,
    "get_full_challenge": """
        SELECT 
            C.id, 
            C.created, 
            C.title, 
            C.body, 
            ChallengeCategories.name AS category_name, 
            Users.username, 
            Profiles.image_asset_id AS profile_image,
            COALESCE(VoteCounts.vote_count, 0) AS vote_count,
            CASE WHEN UserVotes.voter_id IS NOT NULL THEN 1 ELSE 0 END AS has_voted
        FROM Challenges C
        JOIN ChallengeCategories ON C.category_id = ChallengeCategories.id
        JOIN Users ON C.author_id = Users.id
        JOIN Profiles ON Profiles.user_id = Users.id
        LEFT JOIN (
            SELECT challenge_id, COUNT(*) AS vote_count
            FROM Votes
            WHERE challenge_id IS NOT NULL
            GROUP BY challenge_id
        ) AS VoteCounts ON VoteCounts.challenge_id = C.id
        LEFT JOIN (
            SELECT challenge_id, voter_id
            FROM Votes
            WHERE voter_id = ?
        ) AS UserVotes ON UserVotes.challenge_id = C.id
        WHERE C.id = ?
        LIMIT 1
    """,
    "create_challenge": "INSERT INTO Challenges (created, title, body, category_id, author_id) VALUES (?, ?, ?, ?, ?)",
    "challenge_exists": "SELECT EXISTS (SELECT id FROM Challenges WHERE id = ?)",
    "edit_challenge": "UPDATE Challenges SET title = ?, body = ?, category_id = ? WHERE id = ?",
    "create_vote_for_challenge": "INSERT INTO Votes (challenge_id, voter_id) VALUES (?, ?)",
    "create_vote_for_comment": "INSERT INTO Votes (comment_id, voter_id) VALUES (?, ?)" ,
    "create_vote_for_submission": "INSERT INTO Votes (submission_id, voter_id) VALUES (?, ?)",
    "remove_vote_from_challenge": "DELETE FROM Votes WHERE challenge_id = ? AND voter_id = ?",
    "remove_vote_from_comment": "DELETE FROM Votes WHERE comment_id = ? AND voter_id = ?" ,
    "remove_vote_from_submission": "DELETE FROM Votes WHERE submission_id = ? AND voter_id = ?",
    "create_comment": "INSERT INTO Comments (created, challenge_id, body, author_id) VALUES (?, ?, ?, ?)",
    "get_comments": """ 
        SELECT
            Comments.id,
            Comments.created,
            Comments.body,
            Users.username,
            Profiles.image_asset_id
        FROM Comments
        JOIN Users ON Comments.author_id = Users.id
        LEFT JOIN Profiles ON Users.id = Profiles.user_id
        WHERE Comments.challenge_id = ?
        ORDER BY Comments.created ASC
    """ 
}

class AbstractDatabase:
    def __init__(self, connection=DatabaseConnection):
        self.connection = connection

    # MARK: User Abstractions
    def user_exists(self, username: str) -> bool:
        # Check if user exists
        return self.connection.query(query=sql_table["user_exists"], parameters=(username,), limit=1)[0][0] == 1

    def create_user(self, username: str, password_hash: str) -> User:
        # Check if user exists
        if self.user_exists(username):
            raise UserExistsException(username)
        
        # Create user
        _, cursor = self.connection.execute(query=sql_table["create_user"], parameters=(username, password_hash))
        user_id = cursor.lastrowid
        cursor.close()

        # Crete profile
        _, cursor = self.connection.execute(query=sql_table["create_profile"], parameters=(user_id,))
        cursor.close()
        return self.get_user(username)
    
    def get_user(self, username: str) -> User:
        # TODO: Use table joins to get all the user info at once?
        # Get user
        [user_data] = self.connection.query(query=sql_table["get_user"], parameters=(username,), limit=1)
        if not user_data:
            raise UserNotFoundException(username)
        
        user_profile = self.get_profile(user_data[0])
        
        return User(user_data[0],
                    user_data[1],
                    user_data[2],
                    user_data[3] == 1,
                    user_profile)
    
    def edit_user(self, username: str, new_fields: UserEditable):
        # Check if user exists
        if not self.user_exists(username):
            raise UserNotFoundException(username)
        
        _, cursor = self.connection.execute(query=sql_table["edit_user"], parameters=(new_fields["username"], new_fields["password_hash"], new_fields["require_new_password"], username))
        cursor.close()

    # MARK: Profile Abstractions
    def get_profile(self, user_id: int):
        # Get profile
        [profile_data] = self.connection.query(query=sql_table["get_profile"], parameters=(user_id,))
        if not profile_data:
            raise ProfileNotFoundException(user_id)
        
        # Get assets
        image_asset = self.get_asset(profile_data[2]) if profile_data[2] else None
        banner_asset = self.get_asset(profile_data[3]) if profile_data[3] else None
        
        return Profile(profile_data[0],
                       user_id,
                       profile_data[1],
                       image_asset,
                       banner_asset)

    def profile_exists(self, user_id: int):
        return self.connection.query(query=sql_table["profile_exists"], parameters=(user_id,), limit=1)[0][0] == 1

    def edit_profile(self, user_id: int, new_fields: ProfileEditable):
        if not self.profile_exists(user_id):
            raise ProfileNotFoundException(user_id)
        
        _, cursor = self.connection.execute(query=sql_table["edit_profile"], parameters=(new_fields["description"], new_fields["image_asset_id"], new_fields["banner_asset_id"], user_id))
        cursor.close()
        
    # MARK: Asset abstractions
    def create_asset(self, filename: str, value: bytes) -> Asset:
        _, cursor = self.connection.execute(query=sql_table["create_asset"], parameters=(filename, value))
        asset_id = cursor.lastrowid
        cursor.close()

        return Asset(asset_id, filename, value)
    
    def get_asset(self, asset_id: int) -> Asset:
        [asset] = self.connection.query(query=sql_table["get_asset"], parameters=(asset_id,), limit=1)
        if not asset:
            raise AssetNotFoundException(asset_id)
        return Asset(asset_id, asset[0], asset[1])
    
    def delete_asset(self, asset_id: int):
        self.connection.execute(query=sql_table["delete_asset"], parameters=(asset_id,))
    
    # MARK: Categ. abstractions
    def get_categories(self) -> List[Category]:
        results = self.connection.query(query=sql_table["get_categories"])
        categories = []
        for result in results:
            categories.append(Category(result[0], result[1]))

        return categories
    
    # MARK: Chall. abstractions
    def get_challenges(self, current_user_id: int, category_id: int | None, page: int) -> List[Challenge]:
        page_size = 10
        results = self.connection.query(query=sql_table["get_full_challenges"], parameters=(current_user_id, category_id, category_id, page_size, page * page_size))
        challenges = []
        for result in results:
            challenges.append(Challenge(result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7], result[8]))
        return challenges
    
    def get_challenge(self, current_user_id: int, challenge_id: int) -> Challenge:
        [result] = self.connection.query(query=sql_table["get_full_challenge"], parameters=(current_user_id, challenge_id))
        if not result:
            raise ChallengeNotFoundException(challenge_id)
        return Challenge(result[0], result[1], result[2], result[3], result[4], result[5], result[6], result[7], result[8])
    
    def challenge_exists(self, challenge_id) -> bool:
        return self.connection.query(query=sql_table["challenge_exists"], parameters=(challenge_id,), limit=1)[0][0] == 1

    def edit_challenge(self, challenge_id: int, new_fields: ChallengeEditable):
        # Check if challenge exists
        if not self.challenge_exists(challenge_id):
            raise ChallengeNotFoundException(challenge_id)
        
        _, cursor = self.connection.execute(query=sql_table["edit_user"], parameters=(new_fields["title"], new_fields["body"], new_fields["category_id"], challenge_id))
        cursor.close()

    def create_challenge(self, title: str, body: str, category_id: int, author_id: int) -> int:
        _, cursor = self.connection.execute(query=sql_table["create_challenge"], parameters=(int(time()), title, body, category_id, author_id))
        post_id = cursor.lastrowid
        cursor.close()
        return post_id

    # MARK: Voting abstractions
    def vote_for(self, type: Literal["submission", "comment", "challenge"], target_id: int, user_id: int):
        statement = ""
        if type == "submission":
            statement = sql_table["create_vote_for_submission"]
        elif type == "challenge":
            statement = sql_table["create_vote_for_challenge"]
        elif type == "comment":
            statement  = sql_table["create_vote_for_comment"]
        else:
            raise Exception("Unknown target type!")

        _, cursor = self.connection.execute(query=statement, parameters=(target_id, user_id))
        cursor.close()

    def remove_vote_from(self, type: Literal["submission", "comment", "challenge"], target_id: int, user_id: int):
        statement = ""
        if type == "submission":
            statement = sql_table["remove_vote_from_submission"]
        elif type == "challenge":
            statement = sql_table["remove_vote_from_challenge"]
        elif type == "comment":
            statement  = sql_table["remove_vote_from_comment"]
        else:
            raise Exception("Unknown target type!")

        _, cursor = self.connection.execute(query=statement, parameters=(target_id, user_id))
        cursor.close()
