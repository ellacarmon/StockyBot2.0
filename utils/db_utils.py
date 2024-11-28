from contextlib import contextmanager
import sqlite3


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.commit()
            conn.close()

    def init_tables(self):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id INTEGER PRIMARY KEY, 
                      username TEXT, 
                      requests_today INTEGER, 
                      last_request_date TEXT, 
                      is_authorized BOOLEAN,
                      is_admin BOOLEAN DEFAULT FALSE)''')