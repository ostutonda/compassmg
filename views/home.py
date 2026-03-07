import streamlit as st
import pandas as pd
import hashlib
from models.database import get_connection

def show_home():
    st.title("🏠 Accueil COMPASMG")
    conn = get_connection()
    
    # --- LOGIQUE DE CONNEXION DISCRÈTE ---
    if not st.session_state.get('logged_in'):
        st.write("### Identifiez-vous")
        username_input = st.text_input("Nom d'utilisateur")
        
        if username_input:
            # Vérifier si l'utilisateur existe et s'il a un mot de passe
            user_data = conn.execute("SELECT id, isUser, password, role, privileges FROM members WHERE nom = ?", (username_input,)).fetchone()
            
            if user_data:
                member_id, is_user, pwd_hash, role, privs = user_data
                
                # Si c'est un User avec mot de passe
                if is_user == 1 and pwd_hash:
                    pwd_input = st.text_input("Mot de passe", type="password")
                    if st.button("Se connecter"):
                        if hashlib.sha256(pwd_input.encode()).hexdigest() == pwd_hash:
                            st.session_state.update({"logged_in": True, "username": username_input, "user_id": member_id, "role": role, "privileges": privs.split(",")})
                            st.rerun()
                        else:
                            st.error("Mot de passe incorrect.")
                else:
                    # Simple membre sans mot de passe
                    if st.button("Accéder"):
                        st.session_state.update({"logged_in": True, "username": username_input, "user_id": member_id, "role": "Membre", "privileges": []})
                        st.rerun()
            else:
                st.warning("Utilisateur non trouvé.")
        st.divider()

    # --- ANNONCES PUBLIQUES ---
    st.subheader("📢 Annonces Publiques")
    df = pd.read_sql("SELECT title, content, date_pub FROM announcements WHERE type='Public' ORDER BY date_pub DESC", conn)
    for _, row in df.iterrows():
        with st.expander(f"{row['title']} - {row['date_pub']}"):
            st.write(row['content'])
