import streamlit as st
import pandas as pd
from datetime import date
from models.database import get_connection, add_log

def show_members():
    st.title("👥 Gestion des Membres")
    conn = get_connection()

    with st.expander("➕ Ajouter un nouveau membre", expanded=True):
        with st.form("new_member_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            nom = col1.text_input("Nom *")
            prenom = col2.text_input("Prénom")
            postnom = col3.text_input("Post-nom")
            
            col4, col5 = st.columns(2)
            # --- DATE DE NAISSANCE DÉBLOQUÉE ---
            dnaiss = col4.date_input("Date de naissance", 
                                     value=date(1990, 1, 1), 
                                     min_value=date(1920, 1, 1), 
                                     max_value=date.today())
            profession = col5.text_input("Profession")
            
            col6, col7 = st.columns(2)
            tel = col6.text_input("Téléphone")
            adresse = col7.text_area("Adresse physique")
            
            if st.form_submit_button("Enregistrer le membre"):
                if nom:
                    try:
                        conn.execute("""
                            INSERT INTO members (nom, prenom, postnom, telephone, adresse, profession, date_naissance)
                            VALUES (?,?,?,?,?,?,?)
                        """, (nom, prenom, postnom, tel, adresse, profession, dnaiss))
                        conn.commit()
                        add_log(st.session_state.username, f"Ajout membre: {nom}", st.session_state.role)
                        st.success(f"Membre {nom} ajouté avec succès !")
                        st.rerun()
                    except:
                        st.error("Ce nom existe déjà dans la base.")
                else:
                    st.error("Le champ 'Nom' est obligatoire.")

    st.subheader("Liste des membres")
    df = pd.read_sql("SELECT id, nom, prenom, date_naissance, profession, telephone FROM members", conn)
    st.dataframe(df, use_container_width=True)
