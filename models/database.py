import sqlite3
import hashlib
from datetime import datetime

def get_connection():
    return sqlite3.connect("compasmg.db", check_same_thread=False)

def add_log(username, action, role):
    conn = get_connection()
    conn.execute("INSERT INTO logs (username, action, role, timestamp) VALUES (?,?,?,?)",
                 (username, action, role, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Table pour la configuration visuelle
    conn.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    # Valeurs par défaut si la table est vide
    defaults = [
        ('primary_color', '#2E7D32'),
        ('bg_color', '#F5F7F9'),
        ('app_name', 'COMPASMG'),
        ('logo_url', '')
    ]
    for key, val in defaults:
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
    
    
    c.execute('''CREATE TABLE IF NOT EXISTS departments (
        name TEXT PRIMARY KEY, created_at DATE NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, prenom TEXT, postnom TEXT,
        date_naissance DATE, adresse TEXT, qualification TEXT, email TEXT, telephone TEXT,
        department_name TEXT, FOREIGN KEY (department_name) REFERENCES departments(name)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER,
        username TEXT UNIQUE, password TEXT, role TEXT, privileges TEXT,
        FOREIGN KEY (member_id) REFERENCES members(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, 
        type TEXT, department_name TEXT, date_pub DATE
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS finance_categories (name TEXT PRIMARY KEY)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS finance_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, amount REAL, 
        currency TEXT, rate REAL, date DATE, type TEXT, description TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, action TEXT, role TEXT, timestamp DATETIME
    )''')

    # Création Admin par défaut
    pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password, role, privileges) VALUES (?, ?, ?, ?)",
              ('admin', pwd_hash, 'Admin', 'TOUT'))

    conn.commit()
    conn.close()