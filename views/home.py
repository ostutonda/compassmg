import streamlit as st
import pandas as pd
import hashlib
import os
from models.database import get_connection

def show_home():
    st.title("🏠 Accueil COMPASMG")
    conn = get_connection()
    
    # --- LOGIQUE DE CONNEXION ---
    if not st.session_state.get('logged_in'):
        st.write("### Identifiez-vous")
        username_input = st.text_input("Nom d'utilisateur")
        
        if username_input:
            user_data = conn.execute("SELECT id, isUser, password, role, privileges FROM members WHERE nom = ?", (username_input,)).fetchone()
            
            if user_data:
                member_id, is_user, pwd_hash, role, privs = user_data
                if is_user == 1 and pwd_hash:
                    pwd_input = st.text_input("Mot de passe", type="password")
                    if st.button("Se connecter"):
                        if hashlib.sha256(pwd_input.encode()).hexdigest() == pwd_hash:
                            st.session_state.update({"logged_in": True, "username": username_input, "user_id": member_id, "role": role, "privileges": privs.split(",")})
                            st.rerun()
                        else:
                            st.error("Mot de passe incorrect.")
                else:
                    if st.button("Accéder"):
                        st.session_state.update({"logged_in": True, "username": username_input, "user_id": member_id, "role": "Membre", "privileges": []})
                        st.rerun()
            else:
                st.warning("Utilisateur non trouvé.")
        st.divider()

    # --- ANNONCES PUBLIQUES ---
    st.subheader("📢 Annonces Publiques")
    df = pd.read_sql("SELECT title, content, date_pub, image_path FROM announcements WHERE type='Public' ORDER BY date_pub DESC", conn)
    
    if df.empty:
        st.info("Aucune annonce pour le moment.")
    else:
        for _, row in df.iterrows():
            with st.container():
                st.markdown(f"### {row['title']}")
                st.caption(f"Publié le {row['date_pub']}")
                
                # --- AFFICHAGE DE L'IMAGE SI ELLE EXISTE ---
                if pd.notna(row['image_path']) and row['image_path'] != "":
                    if os.path.exists(row['image_path']):
                        st.image(row['image_path'], use_container_width=True)
                
                st.write(row['content'])
                st.divider()
