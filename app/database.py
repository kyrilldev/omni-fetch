import sqlite3
import json

class Database:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect('omnifetch.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blueprints (
                api_id TEXT PRIMARY KEY,
                selectors TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def save_blueprint(self, api_id, selectors, url):
        conn = sqlite3.connect('omnifetch.db')
        cursor = conn.cursor()
        
        # Maak van de dict een tekst-string (JSON)
        selectors_string = json.dumps(selectors) 
        
        cursor.execute(
            "INSERT INTO blueprints (api_id, selectors, url) VALUES (?, ?, ?)",
            (api_id, selectors_string, url)
        )
        conn.commit()
        conn.close()
        return True

    def get_blueprint(self, api_id: str): # Vergeet 'self' niet!
        conn = sqlite3.connect('omnifetch.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM blueprints WHERE api_id = ?", (api_id,))
            row = cursor.fetchone()
            
            print(f"row: {row}")
            
            if row:
                data = dict(row)
                # FIX: Zet de JSON string weer terug naar een Python dict
                data['selectors'] = json.loads(data['selectors'])
                return data
            return None
        finally:
            conn.close()