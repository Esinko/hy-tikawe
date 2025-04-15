from flask import g
from database.abstract import AbstractDatabase
from database.connection import DatabaseConnection
from database.params import database_params

# Get an abstract database instance in Flask context
def get_db() -> AbstractDatabase:
    db = getattr(g, "_database", None)
    if db is None:
        db = AbstractDatabase(DatabaseConnection(*database_params).open())
    return db