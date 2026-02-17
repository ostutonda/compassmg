import streamlit as st
from controllers.auth_controller import verify_login


def show_home():
    # Injection CSS pour une bannière plein écran et un style épuré
    st.markdown("""
        <style>
        .main {
            background-color: #f5f7f9;
        }
        .stImage > img {
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            max-height: 400px;
            object-fit: cover;
        }
        </style>
        """, unsafe_allow_html=True)

    # Bannière (Remplacez l'URL par votre image locale si besoin)
    st.image("https://images.unsplash.com/photo-1438232992991-995b7058bbb3", 
             use_container_width=True)
    
    st.title("⛪ Système de Gestion COMPASMG")
    # ... reste du code visiteur


def verify_login(username, password):
    conn = sqlite3.connect('COMPASMG.db')
    cursor = conn.cursor()
    
    # On hache le mot de passe saisi pour le comparer à la base
    hashed_input = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute('SELECT role FROM users WHERE username = ? AND password = ?', 
                   (username, hashed_input))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]  # Retourne le rôle (ex: "Administrateur")
    return None



def login_page():
    st.title("🔐 Connexion COMPASMG")
    
    with st.form("login_form"):
        user = st.text_input("Identifiant")
        pwd = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter")
        
        if submit:
            role = verify_login(user, pwd)
            if role:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = user
                st.success(f"Bienvenue {user} ({role})")
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect")
