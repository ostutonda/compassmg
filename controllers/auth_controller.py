import streamlit as st

def logout():
    """Réinitialise la session et redirige vers l'accueil visiteur"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.role = "Visiteur"
    st.session_state.logged_in = False
    st.rerun()

def has_permission(module, action):
    """
    Vérifie les droits. 
    L'admin a TOUS les droits (True).
    Les autres dépendent de la configuration choisie.
    """
    if st.session_state.get('role') == "Administrateur":
        return True
    
    # Vérification des permissions granulaires stockées en session
    perms = st.session_state.get('permissions', {})
    permission_key = f"{module}_{action}"
    return perms.get(permission_key, False)
