import streamlit as st
from models.database import get_connection
import pandas as pd

def show_members_page():
    st.title("👥 Gestion des Membres")
    conn = get_connection()

    with st.expander("➕ Enregistrer un nouveau membre"):
        # Liste des départements pour l'assignation
        depts_df = pd.read_sql("SELECT id, name FROM departments", conn)
        dept_options = {r['name']: r['id'] for _, r in depts_df.iterrows()}

        with st.form("member_full_form"):
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Nom")
            prenom = c2.text_input("Prénom")
            postnom = c3.text_input("Post-nom")

            c4, c5 = st.columns(2)
            d_naiss = c4.date_input("Date de naissance")
            metier = c5.text_input("Qualification (Métier)")

            adresse = st.text_area("Adresse (Résidence)")

            c6, c7 = st.columns(2)
            email = c6.text_input("E-mail")
            tel = c7.text_input("Téléphone")

            dept_choice = st.selectbox("Assigner à un Département", options=list(dept_options.keys()))

            if st.form_submit_button("Valider l'inscription"):
                if nom and prenom:
                    conn.execute("""INSERT INTO members 
                        (nom, prenom, postnom, date_naissance, adresse, qualification, email, telephone, department_id) 
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                        (nom, prenom, postnom, d_naiss, adresse, metier, email, tel, dept_options[dept_choice]))
                    conn.commit()
                    st.success(f"Membre {prenom} {nom} enregistré !")
                else:
                    st.error("Le nom et le prénom sont obligatoires.")

    # Affichage de la liste
    st.subheader("Répertoire Complet")
    all_members = pd.read_sql("""
        SELECT m.nom, m.prenom, m.postnom, m.qualification, m.telephone, d.name as departement 
        FROM members m 
        LEFT JOIN departments d ON m.department_id = d.id
    """, conn)
    st.dataframe(all_members, use_container_width=True)

    # Affichage de la liste avec sécurité
    st.subheader("Répertoire Complet")
    try:
        all_members = pd.read_sql("""
            SELECT m.nom, m.prenom, m.postnom, m.qualification, m.telephone, d.name as departement 
            FROM members m 
            LEFT JOIN departments d ON m.department_id = d.id
        """, conn)
        
        if not all_members.empty:
            st.dataframe(all_members, use_container_width=True)
        else:
            st.info("Aucun membre enregistré pour le moment.")
            
    except Exception as e:
        st.warning("⚠️ La base de données doit être synchronisée. Créez d'abord un département dans l'onglet Administration.")
