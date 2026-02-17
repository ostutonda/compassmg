import streamlit as st

def show_home():
    # Masquer la sidebar pour les visiteurs
    if st.session_state.get('role') == "Visiteur":
        st.markdown("<style>section[data-testid='stSidebar'] {display:none;}</style>", unsafe_allow_html=True)

    # Bannière
    st.image("https://images.unsplash.com/photo-1519491056120-10034a70a8d6?q=80&w=2070", 
             caption="COMPASMG - Gestion Intégrée", use_container_width=True)

    st.title("Bienvenue dans votre Communauté")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Actualités & Événements
        * **Culte Dominical** : Tous les dimanches à 09h00.
        * **Étude Biblique** : Mardi et Jeudi à 18h00.
        """)

    with col2:
        # Interface spécifique Visiteur
        if st.session_state.role == "Visiteur":
            st.subheader("📝 Participation")
            with st.form("participation_visiteur"):
                nom = st.text_input("Nom complet")
                if st.form_submit_button("Participer à l'événement"):
                    if nom:
                        st.success(f"Merci {nom}, votre présence est notée !")
                    else:
                        st.error("Veuillez saisir votre nom.")
        
        # Bouton pour passer à l'écran de connexion
        if not st.session_state.logged_in:
            st.divider()
            if st.button("🔓 Espace Membre / Admin"):
                st.session_state.role = "Login_In_Progress"
                st.rerun()