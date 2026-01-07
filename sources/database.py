import sqlite3
from logging import Logger

from lib.basesearch import BaseSearch


class DatabaseSearch(BaseSearch):
    def __init__(self, db_path, logging: Logger | None = None):
        """Initialize the database connection."""
        self.db_path = db_path
        self.logger = logging

    def _format_data(self, dbdata) -> dict | None:
        """Format the database data into a structured dictionary."""
        if dbdata is None:
            return None

        source = dbdata[4].replace(" ", "-").lower()
        res = {
            "risk": dbdata[2],
            "notices": {source: {"id": "", "charges": [dbdata[3]]}},
        }
        return res

    def search(self, first_name: str, last_name: str) -> dict | None:
        """Search for a person by first and last name and retrieve the whole row."""
        query = "SELECT * FROM data WHERE fname = ? AND lname = ?"

        try:
            with sqlite3.connect(self.db_path) as connection:
                cursor = connection.cursor()
                cursor.execute(query, (first_name.title(), last_name.title()))
                data = cursor.fetchone()
                result = self._format_data(data)

                return self.validate_response(result) if result else None
        except sqlite3.Error as e:
            print(f"Database error occurred: {e}")
            return None
