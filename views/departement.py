import streamlit as st
import pandas as pd
from datetime import datetime
from models.database import get_connection, add_log

def show_departement():
    st.title("📂 Gestion des Départements")
    conn = get_connection()
    
    # Récupération des infos utilisateur
    user_id = st.session_state.get('user_id')
    role = st.session_state.get('role')
    privs = st.session_state.get('privileges', [])
    is_admin = (role == "Admin")

    # --- 1. LOGIQUE DE SÉLECTION DU DÉPARTEMENT ---
    if is_admin:
        # L'admin voit TOUT et peut CRÉER
        all_depts_df = pd.read_sql("SELECT * FROM departments", conn)
        dept_list = all_depts_df['name'].tolist()
        
        with st.sidebar.expander("🛠️ Administration Dept"):
            new_d = st.text_input("Nouveau Département")
            if st.button("Créer"):
                if new_d:
                    conn.execute("INSERT OR IGNORE INTO departments (name, created_at) VALUES (?,?)", 
                                 (new_d, datetime.now().date()))
                    conn.commit()
                    st.rerun()
    else:
        # L'utilisateur voit seulement ses départements rattachés
        query = """
            SELECT department_name FROM member_departments 
            WHERE member_id = ?
        """
        my_depts_df = pd.read_sql(query, conn, params=(user_id,))
        dept_list = my_depts_df['department_name'].tolist()

    if not dept_list:
        st.warning("Vous n'avez accès à aucun département. Contactez l'administrateur.")
        return

    # Liste déroulante (Visible si Admin ou si membre de plusieurs depts)
    if len(dept_list) > 1 or is_admin:
        selected_dept = st.selectbox("Choisir le département à gérer", options=dept_list)
    else:
        selected_dept = dept_list[0]
        st.info(f"📍 Espace : **{selected_dept}**")

    st.divider()

    # --- 2. LES ONGLETS DE GESTION ---
    t1, t2, t3, t4, t5 = st.tabs(["👥 Membres", "📅 Activités", "✅ Présences", "📜 Programme", "📢 Annonces"])

    # --- ONGLET 1 : MEMBRES DU DEPT ---
    with t1:
        st.subheader(f"Membres de : {selected_dept}")
        
        # Affichage de la liste
        query_m = """
            SELECT m.id, m.nom, m.prenom, m.telephone, md.is_leader
            FROM members m
            JOIN member_departments md ON m.id = md.member_id
            WHERE md.department_name = ?
        """
        df_members = pd.read_sql(query_m, conn, params=(selected_dept,))
        st.dataframe(df_members[['nom', 'prenom', 'telephone', 'is_leader']], use_container_width=True)

        # Affectation (Pour Admin ou Responsable "crédité")
        if is_admin or "MEM_AFFECT" in privs:
            with st.expander("➕ Affecter un membre à ce département"):
                all_m = pd.read_sql("SELECT id, nom, prenom FROM members", conn)
                all_m['full_name'] = all_m['nom'] + " " + all_m['prenom']
                m_choice = st.selectbox("Sélectionner le membre", options=all_m['id'], 
                                        format_func=lambda x: all_m[all_m['id']==x]['full_name'].values[0])
                is_l = st.checkbox("Nommer comme Responsable ?")
                
                if st.button("Confirmer l'affectation"):
                    conn.execute("""
                        INSERT OR REPLACE INTO member_departments (member_id, department_name, is_leader) 
                        VALUES (?,?,?)
                    """, (m_choice, selected_dept, 1 if is_l else 0))
                    conn.commit()
                    st.success("Membre ajouté au département !")
                    st.rerun()

    # --- ONGLET 2 : ACTIVITÉS ---
    with t2:
        st.subheader("Calendrier des activités")
        if st.button("➕ Planifier une activité"):
            # Ici on pourrait ouvrir un formulaire d'ajout
            st.info("Module de planification en cours...")
        
        act_df = pd.read_sql("SELECT * FROM activities WHERE dept_name = ?", conn, params=(selected_dept,))
        st.table(act_df)

    # --- ONGLET 3 : PRÉSENCES ---
    with t3:
        st.subheader("Pointage des présences")
        st.write("Sélectionnez une activité pour marquer les présences.")
        # Logique de sélection d'activité -> Liste des membres -> Checkbox

    # --- ONGLET 4 : PROGRAMMES ---
    with t4:
        st.subheader("Ordre du jour / Programme")
        prog = pd.read_sql("SELECT content FROM programs WHERE dept_name = ? ORDER BY id DESC LIMIT 1", 
                           conn, params=(selected_dept,))
        if not prog.empty:
            st.markdown(prog['content'].values[0])
        else:
            st.write("Aucun programme enregistré.")

    # --- ONGLET 5 : ANNONCES DU DEPT ---
    with t5:
        st.subheader("Annonces internes")
        ann_df = pd.read_sql("SELECT title, content, date_pub FROM announcements WHERE department_name = ?", 
                             conn, params=(selected_dept,))
        for _, ann in ann_df.iterrows():
            st.chat_message("announcement").write(f"**{ann['title']}** : {ann['content']}")

