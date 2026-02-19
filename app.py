import streamlit as st
import os
from models.database import init_db
from views import home, admin, membres, finance, secretariat

# 1. Configuration de la page avec un icône (emoji ou lien image)
st.set_page_config(
    page_title="COMPASMG Portal",
    page_icon="⛪",
    layout="wide"
)

# 2. Ajout du Logo dans la Sidebar
# Remplacez 'logo.png' par le chemin de votre image
# --- LOGO AVEC VÉRIFICATION ---
logo_path = "assets/logo.png"

if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)
else:
    # Si l'image n'est pas là, on affiche un bel emoji ou un texte stylé
    st.sidebar.markdown("""
        <div style='text-align: center; padding: 10px; border: 2px dashed #2E7D32; border-radius: 10px;'>
            <span style='font-size: 50px;'>⛪</span>
            <p style='color: #2E7D32; font-weight: bold;'>COMPASMG</p>
        </div>
    """, unsafe_allow_html=True)

def apply_custom_style():
    st.markdown("""
        <style>
        /* Modernisation des boutons */
        .stButton>button {
            border-radius: 8px;
            border: none;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        /* Style des cartes d'annonces */
        div[data-testid="stExpander"] {
            background-color: white;
            border-radius: 12px;
            border: 1px solid #E0E0E0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }
        
        /* En-tête de page plus propre */
        h1 {
            color: #1B5E20;
            font-weight: 800 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# À appeler juste après le set_page_config
apply_custom_style()






# Initialisation
st.set_page_config(page_title="COMPASMG", layout="wide")
init_db()

if 'role' not in st.session_state:
    st.session_state.update({"role": "Visiteur", "logged_in": False, "username": "Invité", "privileges": []})

# Sidebar dynamique
st.sidebar.title("⛪ COMPASMG")
if st.session_state.logged_in:
    st.sidebar.write(f"Utilisateur : **{st.session_state.username}**")
    if st.sidebar.button("Déconnexion"):
        st.session_state.clear()
        st.rerun()

menu = ["Accueil"]
if st.session_state.role != "Visiteur":
    menu.append("Membres")
if st.session_state.role in ["Admin", "Tresorier"]:
    menu.append("Finance")
if st.session_state.role in ["Admin", "Secretaire"]:
    menu.append("Secrétariat")
if st.session_state.role == "Admin":
    menu.append("Administration")

choice = st.sidebar.radio("Navigation", menu)

# Routage
if choice == "Accueil": home.show_home()
elif choice == "Membres": membres.show_members()
elif choice == "Finance": finance.show_finance()
elif choice == "Secrétariat": secretariat.show_secretariat()
elif choice == "Administration": admin.show_admin_panel()