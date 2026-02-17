import streamlit as st
from models.database import get_connection
from controllers.backup_controller import backup_database
import pandas as pd

def show_admin_panel():
    st.title("🛠️ Administration Centrale")
    conn = get_connection()

    tab1, tab2, tab3 = st.tabs(["📁 Départements", "🔐 Rôles", "💾 Sauvegarde"])

    with tab1:
        st.subheader("Nouveau Département")
        # Récupération de la liste des membres pour le choix du président
        members_df = pd.read_sql("SELECT id, nom, prenom, postnom FROM members", conn)
        
        with st.form("dept_form"):
            name = st.text_input("Nom du Département")
            date_c = st.date_input("Date de création")
            
            # On prépare une liste de choix "Nom Prénom Postnom"
            if not members_df.empty:
                member_options = {f"{r['nom']} {r['prenom']} {r['postnom']}": r['id'] for _, r in members_df.iterrows()}
                president_label = st.selectbox("Choisir le Président", options=list(member_options.keys()))
            else:
                st.warning("Veuillez d'abord ajouter des membres pour nommer un président.")
                president_label = None

            if st.form_submit_button("Créer le département"):
                if name and president_label:
                    pres_id = member_options[president_label]
                    conn.execute("INSERT INTO departments (name, created_at, president_id) VALUES (?, ?, ?)",
                                 (name, date_c, pres_id))
                    conn.commit()
                    st.success(f"Département '{name}' créé avec succès !")
                else:
                    st.error("Le nom et le président sont obligatoires.")

    with tab3:
        st.subheader("Gestion des Backups")
        if st.button("📦 Créer une sauvegarde manuelle"):
            file_path = backup_database()
            if file_path:
                st.success(f"Sauvegarde réussie : {file_path}")
            else:
                st.error("Échec de la sauvegarde (Base de données introuvable).")