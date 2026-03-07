import streamlit as st
import pandas as pd
from models.database import get_connection

def show_departement():
    st.title("📂 Espace Départements")
    conn = get_connection()
    role = st.session_state.get('role', 'Membre')
    user_id = st.session_state.get('user_id')
    privileges = st.session_state.get('privileges', [])

    # 1. DÉTERMINER LES DÉPARTEMENTS ACCESSIBLES
    if role == "Admin" or "DEPT_VIEW_ALL" in privileges:
        depts_df = pd.read_sql("SELECT name FROM departments", conn)
        my_depts = depts_df['name'].tolist()
    else:
        depts_df = pd.read_sql("SELECT department_name FROM member_departments WHERE member_id = ?", conn, params=(user_id,))
        my_depts = depts_df['department_name'].tolist()

    if not my_depts:
        st.warning("Vous n'êtes affecté à aucun département.")
        return

    # 2. SÉLECTION DU DÉPARTEMENT (Masqué si 1 seul choix et non-admin)
    if len(my_depts) > 1 or role == "Admin":
        selected_dept = st.selectbox("Sélectionnez le département", options=my_depts)
    else:
        selected_dept = my_depts[0]
        st.subheader(f"Département : {selected_dept}")

    st.divider()

    # 3. CONTENU DU DÉPARTEMENT (TABS)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Membres", "📅 Activités", "✅ Présences", "📋 Programmes", "📢 Annonces"])

    with tab1:
        st.markdown(f"**Membres affectés à {selected_dept}**")
        # Afficher les membres de ce département
        query = """
            SELECT m.nom, m.prenom, md.is_leader 
            FROM members m 
            JOIN member_departments md ON m.id = md.member_id 
            WHERE md.department_name = ?
        """
        df_m = pd.read_sql(query, conn, params=(selected_dept,))
        st.dataframe(df_m, use_container_width=True)
        
        # Affectation (Si privilège)
        if role == "Admin" or "MEM_AFFECT" in privileges:
            st.write("➕ Affecter un membre existant à ce département")
            all_m = pd.read_sql("SELECT id, nom FROM members", conn)
            m_dict = dict(zip(all_m['nom'], all_m['id']))
            new_m = st.selectbox("Choisir un membre", options=list(m_dict.keys()), key="aff_mem")
            if st.button("Affecter"):
                conn.execute("INSERT OR IGNORE INTO member_departments (member_id, department_name) VALUES (?, ?)", (m_dict[new_m], selected_dept))
                conn.commit()
                st.success("Membre affecté !")
                st.rerun()

    with tab2:
        st.write("Gestion des Activités (CRUD à implémenter ici)")
        # ... Logique Activités ...
    
    with tab3:
        st.write("Feuille de présence (Liaison avec Activités)")
        # ... Logique Présences ...

    # Vous pouvez développer tab4 et tab5 sur le même modèle
