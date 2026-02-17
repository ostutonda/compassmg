import sqlite3
from datetime import datetime


import sqlite3
import hashlib

def init_admin_account():
    conn = sqlite3.connect('COMPASMG.db')
    cursor = conn.cursor()

    # 1. Création de la table users si elle n'existe pas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # 2. Hachage du mot de passe (SHA-256 pour cet exemple)
    username = "admin"
    raw_password = "admin123"
    hashed_password = hashlib.sha256(raw_password.encode()).hexdigest()

    # 3. Insertion de l'admin
    try:
        cursor.execute('''
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        ''', (username, hashed_password, "Administrateur"))
        conn.commit()
        print("Utilisateur Admin créé avec succès !")
    except sqlite3.IntegrityError:
        print("L'utilisateur admin existe déjà.")
    
    conn.close()

if __name__ == "__main__":
    init_admin_account()






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