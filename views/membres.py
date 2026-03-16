import streamlit as st
import pandas as pd
from datetime import date
from models.database import get_connection, add_log


def show_members():
    st.title("👥 Gestion des Membres")
    conn = get_connection()

    with st.expander("➕ Ajouter un nouveau membre", expanded=False):
        with st.form("form_membre", clear_on_submit=True):
            # --- Identité ---
            st.subheader("🆔 Identité")
            col1, col2, col3 = st.columns(3)
            nom = col1.text_input("Nom")
            prenom = col2.text_input("Prénom")
            postnom = col3.text_input("Postnom")
            
            col4, col5, col6 = st.columns(3)
            sexe = col4.selectbox("Sexe", ["Masculin", "Féminin"])
            lieu_naiss = col5.text_input("Lieu de naissance")
            
            # On définit les limites
            min_date = date(1920, 1, 1)  # Permet de remonter à plus de 100 ans
            max_date = date.today()       # Empêche de naître dans le futur
            date_naiss = col6.date_input("Date de naissance",
            value=date(2000, 1, 1), # Valeur par défaut (ex: l'an 2000)
            min_value=min_date,
            max_value=max_date
            )

            # --- État Civil et Contact ---
            st.subheader("📞 État Civil & Contact")
            col7, col8, col9 = st.columns(3)
            etat_civil = col7.selectbox("État Civil", ["Célibataire", "Marié(e)", "Veuf(ve)", "Divorcé(e)"])
            telephone = col8.text_input("Téléphone")
            email = col9.text_input("Adresse Mail")
            
            adresse = st.text_area("Adresse physique", height=70)

            # --- Vie Spirituelle et Pro ---
            st.subheader("⛪ Vie Spirituelle & Profession")
            col10, col11 = st.columns(2)
            
            #min_date = date(1920, 1, 1)  # Permet de remonter à plus de 100 ans
            #max_date = date.today()       # Empêche de naître dans le futur
            date_bapteme = col10.date_input("Date de baptême")
            value=date(2000, 1, 1), # Valeur par défaut (ex: l'an 2000)
            min_value=min_date,
            max_value=max_date
            )
            
            profession = col11.text_input("Profession")

            # --- Urgence ---
            st.subheader("🚨 Contact en cas d'urgence")
            col12, col13, col14 = st.columns(3)
            u_nom = col12.text_input("Nom & Prénom (Urgence)")
            u_lien = col13.text_input("Lien (ex: Époux, Père...)")
            u_tel = col14.text_input("Téléphone (Urgence)")

            if st.form_submit_button("Enregistrer le membre"):
                if nom and prenom:
                    try:
                        conn.execute("""
                            INSERT INTO members (
                                nom, prenom, postnom, sexe, lieu_naissance, date_naissance,
                                etat_civil, adresse, telephone, email, date_bapteme, profession,
                                contact_urgence_nom, contact_urgence_lien, contact_urgence_tel
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (nom, prenom, postnom, sexe, lieu_naiss, date_naiss, 
                              etat_civil, adresse, telephone, email, date_bapteme, profession,
                              u_nom, u_lien, u_tel))
                        conn.commit()
                        add_log(st.session_state.username, f"Ajout membre: {nom} {prenom}", st.session_state.role)
                        st.success("Membre enregistré avec succès !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")
                else:
                    st.warning("Le Nom et le Prénom sont obligatoires.")

    # --- AFFICHAGE DE LA LISTE ---
    st.subheader("📋 Liste des membres")
    df = pd.read_sql("SELECT nom, prenom, sexe, telephone, etat_civil, profession FROM members", conn)
    st.dataframe(df, use_container_width=True)
