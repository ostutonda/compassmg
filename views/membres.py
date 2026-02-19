from datetime import date
import streamlit as st
import pandas as pd
from models.database import get_connection, add_log
from controllers.auth_controller import check_privilege

def show_members():
    st.title("👥 Gestion des Membres")
    conn = get_connection()

    # --- FORMULAIRE D'AJOUT (Si privilège présent) ---
    if check_privilege("MOD_MEMBRE"):
        with st.expander("➕ Ajouter un nouveau membre"):
            # On récupère seulement le NOM des départements
            depts_df = pd.read_sql("SELECT name FROM departments", conn)
            dept_list = depts_df['name'].tolist()

            if not dept_list:
                st.warning("⚠️ Créez d'abord un département dans l'Administration.")
            else:
                with st.form("new_member_form"):
                    col1, col2, col3 = st.columns(3)
                    nom = col1.text_input("Nom")
                    prenom = col2.text_input("Prénom")
                    postnom = col3.text_input("Post-nom")
                    
                    col4, col5 = st.columns(2)
                    # On définit les limites
                    min_date = date(1920, 1, 1)  # Permet de remonter à plus de 100 ans
                    max_date = date.today()       # Empêche de naître dans le futur
                    dnaiss = col4.date_input("Date de naissance",
                    value=date(2000, 1, 1), # Valeur par défaut (ex: l'an 2000)
                    min_value=min_date,
                    max_value=max_date
                    )
                    
                    job = col5.text_input("Qualification / Métier")
                    
                    email = st.text_input("Email")
                    tel = st.text_input("Téléphone")
                    adresse = st.text_area("Adresse")
                    
                    # On utilise directement le nom choisi
                    dept_choisi = st.selectbox("Département", options=dept_list)
                    
                    if st.form_submit_button("Enregistrer le membre"):
                        if nom and prenom:
                            conn.execute("""
                                INSERT INTO members (nom, prenom, postnom, date_naissance, adresse, qualification, email, telephone, department_name)
                                VALUES (?,?,?,?,?,?,?,?,?)
                            """, (nom, prenom, postnom, dnaiss, adresse, job, email, tel, dept_choisi))
                            conn.commit()
                            add_log(st.session_state.username, f"Ajout membre: {nom} {prenom}", st.session_state.role)
                            st.success(f"Membre {nom} ajouté avec succès !")
                            st.rerun()
                        else:
                            st.error("Le nom et le prénom sont obligatoires.")

    st.divider()

    # --- AFFICHAGE DE LA LISTE ---
    st.subheader("Liste des membres enregistrés")
    
    # Jointure simple sur le nom du département
    query = """
        SELECT nom, prenom, postnom, qualification, department_name as Département, telephone 
        FROM members
    """
    df_members = pd.read_sql(query, conn)
    
    if df_members.empty:
        st.info("Aucun membre dans la base de données.")
    else:
        # Barre de recherche simple
        search = st.text_input("🔍 Rechercher un membre (par nom ou département)")
        if search:
            df_members = df_members[
                df_members['nom'].str.contains(search, case=False) | 
                df_members['Département'].str.contains(search, case=False)
            ]
        
        st.dataframe(df_members, use_container_width=True)