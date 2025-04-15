# SQLite3 database connection library for the first layer of abstraction and the basics

from sqlite3 import connect, Connection, Cursor
from pathlib import Path
from time import time
from typing import Any, List, Optional, Tuple, Union

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

        # Enforce foreign keys
        self.connection.execute("PRAGMA foreign_keys = ON")

        return self
    
    def close(self):
        if not self.connection:
            raise Exception("Database not open!")
        self.connection.close()
    
    # Execute a command against the database
    def execute(self, query: str, parameters: Union[Tuple[Any], dict]) -> Tuple[Connection, Cursor]:
        try:
            if not self.connection:
                raise Exception("Database not open!")
            cursor = self.connection.cursor()
            cursor.execute(query, parameters)
            self.connection.commit()
        except Exception as err:
            print("Database execution error:", err)
            self.connection.rollback()
        return self.connection, cursor
    
    # Query the database
    def query(self, query = str, parameters: Optional[Union[Tuple[Any], dict]] = None, limit: int = -1) -> List[Any]:
        if not self.connection:
            raise Exception("Database not open!")
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, parameters)
        except Exception as e:
            print("Database execution error:", e)
            self.connection.rollback()
        results = cursor.fetchmany(limit)
        return results
