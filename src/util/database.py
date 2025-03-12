from sqlite3 import connect, Connection, Cursor
from pathlib import Path
from typing import Any, Tuple

class DatabaseConnection:
    def __init__(self, database="./main.db", schema="./schema.sql"):
        self.database_filepath = database
        self.schema_filepath = schema
        self.connection = None

    # Open the database connection
    def open(self):
        if self.connection != None:
            raise Exception("Database already opened!")

        # Read schema
        schema_file = Path(self.schema_filepath)
        if not schema_file.exists():
            raise FileNotFoundError("Schema file not found.")
        
        # Open database and write schema, if it does not exist
        database_file = Path(self.database_filepath)
        if not database_file.exists():
            schema = schema_file.read_text()
            self.connection = connect(database_file)
            self.connection.executescript(schema)
        else:
            self.connection = connect(database_file)
    
    # Execute a command against the database
    def _execute(self, query: str, parameters: Tuple[Any] | dict) -> Tuple[Connection, Cursor]:
        if self.connection == None:
            raise Exception("Database not open!")
        cursor = self.connection.cursor()
        cursor.execute(query, parameters)
        return (self.connection, cursor)
    
    # Query the database
    def _query(self, query: str, parameters: Tuple[Any] | dict, limit: int = 1) -> list[Any]:
        cursor = self.connection.cursor()
        cursor.execute(query, parameters)
        results = cursor.fetchmany(limit)
        cursor.close()
        return results