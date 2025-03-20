from sqlite3 import connect, Connection, Cursor
from pathlib import Path
from typing import Any, List, Tuple, TypedDict

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
        print("EXEC", query, parameters)
        cursor.execute(query, parameters)
        self.connection.commit()
        return self.connection, cursor
    
    # Query the database
    def query(self, query = str, parameters: Tuple[Any] | dict = {}, limit: int = -1) -> list[Any]:
        print("IN QUERY", query, self.connection, parameters)
        if not self.connection:
            raise Exception("Database not open!")
        cursor = self.connection.cursor()
        print("PERFORM")
        try:
            cursor.execute(query, parameters)
        except Exception as e:
            print("ERR", e)
        print("DID")
        results = cursor.fetchmany(limit)
        #print("QUERY RES", results)
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
    "get_categories": "SELECT id, name FROM ChallengeCategories"
}

class AbstractDatabase:
    def __init__(self, connection=DatabaseConnection):
        self.connection = connection

    # MARK: User Abstractions
    def user_exists(self, username: str) -> bool:
        # Check if user exists
        print(self.connection.query(query=sql_table["user_exists"], parameters=(username,)))
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
        print("GET USER")
        [user_data] = self.connection.query(query=sql_table["get_user"], parameters=(username,), limit=1)
        print("GOT", user_data)
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
        print("PROFILE DAT", profile_data)
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

