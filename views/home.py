import streamlit as st
import hashlib
from models.database import get_connection

def show_login_page():
    st.markdown("""
        <style>
        .login-box {
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("🔐 Connexion Sécurisée")
    
    with st.container():
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            submit = st.form_submit_button("Se connecter")

            if submit:
                # Hachage du mot de passe pour la comparaison
                hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
                
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", 
                               (username, hashed_pwd))
                result = cursor.fetchone()
                conn.close()

                if result:
                    st.session_state.logged_in = True
                    st.session_state.role = result[0]
                    st.session_state.username = username
                    st.success(f"Bienvenue, {username} !")
                    st.rerun()
                else:
                    st.error("Identifiants incorrects. Veuillez réessayer.")

    if st.button("⬅️ Retour à l'accueil"):
        st.session_state.role = "Visiteur"
        st.rerun()
