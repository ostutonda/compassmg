import streamlit as st

def has_permission(module, action):
    """
    Vérifie si le rôle actuel possède les droits.
    action: 'view' ou 'edit' (inclut Create/Update/Delete)
    """
    if st.session_state.role == "Administrateur":
        return True
    
    # Simulation de vérification en base (à lier à la table roles)
    permissions = st.session_state.get('permissions', {})
    return permissions.get(f"can_{action}_{module}", False)