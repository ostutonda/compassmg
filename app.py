import streamlit as st
import os
from models.database import init_db, get_connection

# Remplacez la ligne 4 par ceci :
from views import home
print("Home OK")
from views import admin
print("Admin OK")
from views import membres
print("Membres OK")
from views import finance
print("Finance OK")
from views import secretariat
print("Secretariat OK")
from views import departement
print("Departement OK")
 

#from views import home, admin, membres, finance, secretariat, departement

# ==========================================
# 1. CONFIGURATION DE LA PAGE (DOIT ÊTRE EN PREMIER)
# ==========================================
st.set_page_config(
    page_title="COMPASMG Portal",
    page_icon="⛪",
    layout="wide"
)

# ==========================================
# 2. INITIALISATION DE LA BASE ET DE LA SESSION
# ==========================================
init_db()

# Valeurs par défaut pour un visiteur non connecté
if 'logged_in' not in st.session_state:
    st.session_state.update({
        "logged_in": False, 
        "username": "Invité", 
        "user_id": None,
        "role": "Visiteur", 
        "privileges": []
    })

# ==========================================
# 3. GESTION DU DESIGN DYNAMIQUE
# ==========================================
def apply_dynamic_design():
    # Vérifie si on est en mode "Aperçu" depuis l'Administration
    if 'preview_design' in st.session_state:
        settings = st.session_state.preview_design
    else:
        # Sinon, on lit les vraies couleurs dans la base de données
        conn = get_connection()
        settings = dict(conn.execute("SELECT key, value FROM settings").fetchall())
        conn.close()

    p_color = settings.get('primary_color', '#2E7D32')
    bg_color = settings.get('bg_color', '#F5F7F9')
    
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {bg_color}; }}
        h1, h2, h3 {{ color: {p_color} !important; }}
        
        /* Style des formulaires */
        div[data-testid="stForm"] {{
            border: 2px solid {p_color}33;
            background-color: white;
            border-radius: 15px;
            padding: 20px;
        }}

        /* Style des zones de texte */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
            border-radius: 8px !important;
            border: 1px solid #D0D0D0 !important;
        }}
        .stTextInput input:focus {{
            border-color: {p_color} !important;
            box-shadow: 0 0 0 2px {p_color}33 !important;
        }}

        /* Boutons */
        .stButton>button {{
            background-color: white;
            color: {p_color} !important;
            border: 2px solid {p_color} !important;
            border-radius: 8px;
            font-weight: bold;
        }}
        .stButton>button:hover {{
            background-color: {p_color} !important;
            color: white !important;
            transform: translateY(-2px);
        }}
        </style>
    """, unsafe_allow_html=True)
    
    return settings

# On applique le design et on récupère les paramètres (logo, nom)
conf = apply_dynamic_design()

# ==========================================
# 4. SIDEBAR : LOGO ET PROFIL
# ==========================================
logo_path = "assets/logo.png"
logo_url = conf.get('logo_url', '')

# Priorité 1: L'URL du logo définie dans l'admin
if logo_url:
    st.sidebar.image(logo_url, use_container_width=True)
# Priorité 2: L'image locale dans le dossier assets
elif os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)
# Priorité 3: Emoji et Texte par défaut
else:
    app_name = conf.get('app_name', 'COMPASMG')
    st.sidebar.markdown(f"""
        <div style='text-align: center; padding: 10px; border: 2px dashed #2E7D32; border-radius: 10px;'>
            <span style='font-size: 50px;'>⛪</span>
            <p style='color: #2E7D32; font-weight: bold;'>{app_name}</p>
        </div>
    """, unsafe_allow_html=True)

st.sidebar.divider()

# Profil utilisateur
if st.session_state.logged_in:
    st.sidebar.success(f"Connecté : **{st.session_state.username}**")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear()
        st.rerun()
else:
    st.sidebar.info("Non connecté")

st.sidebar.divider()

# ==========================================
# 5. MENU DE NAVIGATION DYNAMIQUE (RBAC)
# ==========================================
menu = ["Accueil"]

if st.session_state.logged_in:
    # Tous les connectés voient leurs départements
    menu.append("Départements")
    
    # L'admin voit tout. Les autres voient selon leurs rôles/privilèges
    if st.session_state.role == "Admin" or "MEM_CRUD" in st.session_state.privileges:
        menu.append("Membres")
        
    if st.session_state.role in ["Admin", "Tresorier"]:
        menu.append("Finance")
        
    if st.session_state.role in ["Admin", "Secretaire"]:
        menu.append("Secrétariat")
        
    if st.session_state.role == "Admin":
        menu.append("Administration")

choice = st.sidebar.radio("📌 Navigation", menu)

# ==========================================
# 6. ROUTAGE DES PAGES
# ==========================================
if choice == "Accueil": 
    home.show_home()
elif choice == "Départements": 
    departement.show_departement()
elif choice == "Membres": 
    membres.show_members()
elif choice == "Finance": 
    finance.show_finance()
elif choice == "Secrétariat": 
    secretariat.show_secretariat()
elif choice == "Administration": 
    admin.show_admin_panel()

