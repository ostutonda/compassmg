import streamlit as st
import hashlib
from models.database import get_connection, add_log

def check_privilege(perm_name):
    """Retourne True si l'utilisateur a le droit de voir/cliquer"""
    if st.session_state.get('role') == "Admin": 
        return True
    return perm_name in st.session_state.get('privileges', [])

def login_logic(username, password=None):
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Mode Staff (Mot de passe fourni)
    if username and password:
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        c.execute("""SELECT u.role, u.privileges, m.department_name 
                     FROM users u LEFT JOIN members m ON u.member_id = m.id 
                     WHERE u.username = ? AND u.password = ?""", (username, pwd_hash))
        res = c.fetchone()
        if res:
            st.session_state.update({"logged_in": True, "role": res[0], "username": username,
                                     "privileges": res[1].split(",") if res[1] else [], "dept": res[2] or "Tous"})
            add_log(username, "Connexion Staff", res[0])
            return True
            
    # 2. Mode Membre Simple (Pas de mot de passe)
    elif username and not password:
        c.execute("SELECT nom, department_name FROM members WHERE nom = ?", (username,))
        res = c.fetchone()
        if res:
            st.session_state.update({"logged_in": True, "role": "Membre", "username": res[0],
                                     "privileges": [], "dept": res[1]})
            add_log(res[0], "Connexion Membre", "Membre")
            return True
            
    return False

def logout():
    add_log(st.session_state.get("username", "Inconnu"), "Déconnexion", st.session_state.get("role", "Visiteur"))
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()