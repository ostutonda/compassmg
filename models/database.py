import sqlite3
import hashlib
from datetime import datetime

def get_connection():
    return sqlite3.connect("compasmg.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # --- TABLES EXISTANTES ---
    c.execute('''CREATE TABLE IF NOT EXISTS departments (name TEXT PRIMARY KEY, description TEXT, created_at DATE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE, prenom TEXT, postnom TEXT, telephone TEXT,
        adresse TEXT, profession TEXT, date_naissance DATE,
        isUser INTEGER DEFAULT 0, password TEXT, role TEXT DEFAULT 'Membre', privileges TEXT DEFAULT '')''')

    c.execute('''CREATE TABLE IF NOT EXISTS member_departments (
        member_id INTEGER, department_name TEXT, is_leader INTEGER DEFAULT 0,
        FOREIGN KEY(member_id) REFERENCES members(id), FOREIGN KEY(department_name) REFERENCES departments(name),
        PRIMARY KEY (member_id, department_name))''')

    c.execute('''CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT, type TEXT, department_name TEXT, date_pub DATE, image_path TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, action TEXT, role TEXT, timestamp DATETIME)''')

    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS exchange_rates (date_rate DATE PRIMARY KEY, rate REAL)''')

    # --- TABLES FINANCE MISES À JOUR ---
    c.execute('''CREATE TABLE IF NOT EXISTS finance_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT UNIQUE)''')

    c.execute('''CREATE TABLE IF NOT EXISTS finances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_trans DATE, 
        type TEXT, 
        category TEXT,
        label TEXT, 
        total_usd REAL, 
        total_cdf REAL, 
        rate REAL, 
        billetage_json TEXT)''')

    # --- DONNÉES PAR DÉFAUT ---
    # Catégories initiales
    default_cats = [('Offrandes',), ('Dîmes',), ('Action de grâce',), ('Construction',), ('Social',), ('Fonctionnement',)]
    c.executemany("INSERT OR IGNORE INTO finance_categories (name) VALUES (?)", default_cats)

    # Admin par défaut
    pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO members (nom, prenom, isUser, password, role, privileges) VALUES (?, ?, ?, ?, ?, ?)",
              ('admin', 'Super', 1, pwd_hash, 'Admin', 'ALL'))
    
    for key, val in [('primary_color', '#2E7D32'), ('bg_color', '#F5F7F9'), ('app_name', 'COMPASMG'), ('logo_url', '')]:
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
              
    conn.commit()
    conn.close()

def add_log(user, action, role):
    try:
        conn = get_connection()
        conn.execute("INSERT INTO logs (user, action, role, timestamp) VALUES (?, ?, ?, ?)",
                     (user, action, role, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erreur Log: {e}")
