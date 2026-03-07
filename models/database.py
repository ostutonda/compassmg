import sqlite3
import hashlib
from datetime import datetime

def get_connection():
    return sqlite3.connect("compasmg.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Départements
    c.execute('CREATE TABLE IF NOT EXISTS departments (name TEXT PRIMARY KEY, description TEXT, created_at DATE)')
    
    # Table unique Membres/Utilisateurs fusionnée
    c.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nom TEXT UNIQUE, prenom TEXT, postnom TEXT, telephone TEXT,
        isUser INTEGER DEFAULT 0, 
        password TEXT, 
        role TEXT DEFAULT 'Membre', 
        privileges TEXT DEFAULT ''
    )''')

    # Table de liaison (Un membre <-> Plusieurs Départements)
    c.execute('''CREATE TABLE IF NOT EXISTS member_departments (
        member_id INTEGER, 
        department_name TEXT,
        is_leader INTEGER DEFAULT 0,
        FOREIGN KEY(member_id) REFERENCES members(id),
        FOREIGN KEY(department_name) REFERENCES departments(name),
        PRIMARY KEY (member_id, department_name)
    )''')

    # Nouvelles tables pour le menu Département
    c.execute('CREATE TABLE IF NOT EXISTS activities (id INTEGER PRIMARY KEY, dept_name TEXT, title TEXT, date DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY, activity_id INTEGER, member_id INTEGER, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS programs (id INTEGER PRIMARY KEY, dept_name TEXT, content TEXT, date DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS announcements (id INTEGER PRIMARY KEY, title TEXT, content TEXT, type TEXT, department_name TEXT, date_pub DATE)')
    
    # Admin par défaut
    pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO members (nom, prenom, isUser, password, role, privileges) VALUES (?, ?, ?, ?, ?, ?)",
              ('admin', 'Super', 1, pwd_hash, 'Admin', 'ALL'))
              
    conn.commit()
    conn.close()
