import streamlit as st
from controllers.auth_controller import login_user
from models.database import get_connection
from models.database import get_connection

def show_home():
    st.title("🏠 Accueil COMPASMG")
    conn = get_connection()
    
    # Récupération du rôle et du département en session
    role = st.session_state.get('role', 'Visiteur')
    user_dept = st.session_state.get('dept', None)

    st.subheader("📢 Annonces & Informations")

    # Construction de la requête SQL dynamique
    if role == "Visiteur":
        # Le visiteur ne voit QUE le public
        query = "SELECT * FROM announcements WHERE type = 'Public' ORDER BY date_pub DESC"
        params = ()
    elif role == "Admin":
        # L'admin voit TOUT
        query = "SELECT * FROM announcements ORDER BY date_pub DESC"
        params = ()
    else:
        # Les membres/staff voient le public + le privé de LEUR département
        query = "SELECT * FROM announcements WHERE type = 'Public' OR (type = 'Privé' AND department_name = ?) ORDER BY date_pub DESC"
        params = (user_dept,)

    annonces_df = pd.read_sql(query, conn, params=params)

    if annonces_df.empty:
        st.write("Aucune annonce pour le moment.")
    else:
        for _, row in annonces_df.iterrows():
            # Style visuel différent selon le type
            icon = "🌐" if row['type'] == 'Public' else "🔒"
            color = "blue" if row['type'] == 'Public' else "orange"
            
            with st.expander(f"{icon} {row['title']} - {row['date_pub']}"):
                st.markdown(f"**Type:** :{color}[{row['type']}]")
                if row['department_name'] != 'Tous':
                    st.markdown(f"**Département:** {row['department_name']}")
                st.write(row['content'])
                
                
                
                