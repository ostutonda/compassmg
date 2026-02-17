import sqlite3
from datetime import datetime

def get_connection():
    # Permet de partager la connexion entre les threads Streamlit
    return sqlite3.connect("compasmg.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. TABLE DEPARTEMENTS (Nom, Date, Président)
    c.execute('''CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at DATE NOT NULL,
        president_id INTEGER
    )''')

    # 2. TABLE MEMBRES (Les 9 champs demandés + département)
    c.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT, 
        prenom TEXT, 
        postnom TEXT,
        date_naissance DATE, 
        adresse TEXT,
        qualification TEXT, 
        email TEXT, 
        telephone TEXT,
        department_id INTEGER,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )''')

    # 3. TABLE FINANCES
    c.execute('''CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT, 
        categorie TEXT, 
        montant REAL, 
        date DATE, 
        description TEXT
    )''')

    # 4. TABLE USERS (Pour l'admin et les rôles)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE, 
        password TEXT, 
        role TEXT
    )''')

    # Création de l'Admin par défaut (Plein pouvoir)
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
              ('admin', 'admin123', 'Administrateur'))

    conn.commit()
    conn.close()