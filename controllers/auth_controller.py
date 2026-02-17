import streamlit as st
import hashlib

# Simulation de base de données de permissions (à terme, lire depuis la table roles)
# Format : 'role': {'module': [actions]}
DEFAULT_PERMISSIONS = {
    "Administrateur": "ALL",
    "Secrétariat": {
        "membres": ["create", "read", "update"],
        "secretariat": ["create", "read", "update", "delete"]
    },
    "Trésorerie": {
        "membres": ["read"],
        "finance": ["create", "read"]
    },
    "Visiteur": {
        "home": ["read", "participate"]
    }
}
def has_permission(module, action):
    # PLEIN POUVOIR ADMIN
    if st.session_state.get('role') == "Administrateur":
        return True
    
    # Pour les autres rôles, on vérifie les permissions stockées en session
    permissions = st.session_state.get('permissions', {})
    return permissions.get(f"{module}_{action}", False)

def check_password(username, password):
    # Pour le test, admin/admin123
    if username == "admin" and password == "admin123":
        return "Administrateur"
    # Ajoutez ici la logique SQL pour vérifier les utilisateurs réels
    return None

def login():
    st.sidebar.title("Connexion")
    user = st.sidebar.text_input("Utilisateur")
    pwd = st.sidebar.text_input("Mot de passe", type="password")
    
    if st.sidebar.button("Se connecter"):
        role = check_password(user, pwd)
        if role:
            st.session_state.logged_in = True
            st.session_state.username = user
            st.session_state.role = role
            # On charge les permissions du rôle en session
            st.session_state.permissions = DEFAULT_PERMISSIONS.get(role, {})
            st.rerun()
        else:
            st.sidebar.error("Identifiants invalides")

def logout():
    st.session_state.logged_in = False
    st.session_state.role = "Visiteur"
    st.session_state.permissions = DEFAULT_PERMISSIONS["Visiteur"]
    st.rerun()

def has_permission(module, action):
    """Vérifie si l'utilisateur a le droit (create, read, update, delete)"""
    if st.session_state.get('role') == "Administrateur":
        return True
    perms = st.session_state.get('permissions', {})
    if module in perms:
        return action in perms[module]
    return False