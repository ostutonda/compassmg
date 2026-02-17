import streamlit as st
from models.database import init_db
from views import home, admin, membres, finance, secretariat
from controllers import auth_controller


# Initialisation de la base de données au lancement
init_db()

# Configuration de la page
st.set_page_config(page_title="COMPASSION MONT-NGAFULA", layout="wide", page_icon="⛪")

# Gestion de la session
if 'role' not in st.session_state:
    st.session_state.role = "Visiteur"
    st.session_state.logged_in = False

# NAVIGATION
if st.session_state.role == "Visiteur":
    # Mode Visiteur : Pas de sidebar, juste l'accueil
    home.show_home()
else:
    # Mode Connecté : Sidebar active
    st.sidebar.title(f"⛪ COMPASMG")
    st.sidebar.write(f"Rôle : **{st.session_state.role}**")
    
    menu = st.sidebar.radio("Menu Principal", 
        ["Accueil", "Membres", "Finance", "Secrétariat", "Administration"])
    
    if st.sidebar.button("Déconnexion"):
        auth_controller.logout()

    # Routage vers les vues
    if menu == "Accueil": home.show_home()
    elif menu == "Membres": membres.show_members_page()
    elif menu == "Finance": finance.show_finance()
    elif menu == "Secrétariat": secretariat.show_secretariat()
    elif menu == "Administration": admin.show_admin_panel()