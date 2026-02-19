import streamlit as st
import pandas as pd
from models.database import get_connection
from controllers.auth_controller import login_logic

def show_home():
    st.title("🏠 Bienvenue sur COMPASMG")
    
    # FORMULAIRE DE CONNEXION (Visible seulement si non connecté)
    if not st.session_state.get('logged_in'):
        with st.expander("🔐 Connexion (Membre ou Staff)", expanded=True):
            col1, col2 = st.columns(2)
            u = col1.text_input("Nom ou Identifiant")
            p = col2.text_input("Mot de passe (Laisser vide si membre)", type="password")
            if st.button("Se connecter", use_container_width=True):
                if login_logic(u, p if p else None):
                    st.success("Connexion réussie !")
                    st.rerun()
                else:
                    st.error("Accès refusé.")
        st.divider()

    # AFFICHAGE DES ANNONCES (Filtrage dynamique)
    st.subheader("📢 Dernières Annonces")
    conn = get_connection()
    role = st.session_state.get('role', 'Visiteur')
    user_dept = st.session_state.get('dept', 'Tous')

    # Logique SQL pour la visibilité
    if role == "Admin":
        query = "SELECT * FROM announcements ORDER BY date_pub DESC"
        df = pd.read_sql(query, conn)
    elif role == "Visiteur":
        query = "SELECT * FROM announcements WHERE type='Public' ORDER BY date_pub DESC"
        df = pd.read_sql(query, conn)
    else: # Membre, Secrétaire, Trésorier
        query = "SELECT * FROM announcements WHERE type='Public' OR (type='Privé' AND department_name=?) ORDER BY date_pub DESC"
        df = pd.read_sql(query, conn, params=(user_dept,))

    if df.empty:
        st.info("Aucune annonce disponible.")
    else:
        for _, row in df.iterrows():
            with st.chat_message("user" if row['type'] == 'Public' else "assistant"):
                st.write(f"**{row['title']}**")
                st.caption(f"Le {row['date_pub']} | {row['type']} - {row['department_name']}")
                st.write(row['content'])