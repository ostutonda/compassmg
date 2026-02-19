import streamlit as st
import pandas as pd
from models.database import get_connection, add_log
from controllers.auth_controller import check_privilege

def show_secretariat():
    st.title("📝 Secrétariat & Communication")
    conn = get_connection()
    
    # Vérification du privilège pour publier
    can_publish = check_privilege("PUB_ANNONCE")

    tab1, tab2 = st.tabs(["📢 Publier une annonce", "🗂️ Gérer les annonces existantes"])

    with tab1:
        if not can_publish:
            st.error("🚫 Vous n'avez pas les privilèges nécessaires pour publier.")
        else:
            st.subheader("Nouvelle Publication")
            with st.form("publish_form", clear_on_submit=True):
                title = st.text_input("Titre de l'annonce")
                content = st.text_area("Contenu du message")
                
                c1, c2 = st.columns(2)
                v_type = c1.selectbox("Visibilité", ["Public", "Privé"])
                
                # Récupération des départements pour le ciblage
                depts_df = pd.read_sql("SELECT name FROM departments", conn)
                depts = ["Tous"] + depts_df['name'].tolist()
                
                # Le choix du département n'est pertinent que si c'est "Privé"
                v_dept = c2.selectbox("Département ciblé", options=depts, 
                                     help="Si Public, 'Tous' est recommandé.")

                if st.form_submit_button("🚀 Publier l'annonce"):
                    if title and content:
                        conn.execute("""
                            INSERT INTO announcements (title, content, type, department_name, date_pub)
                            VALUES (?, ?, ?, ?, DATE('now'))
                        """, (title, content, v_type, v_dept))
                        conn.commit()
                        add_log(st.session_state.username, f"Publication: {title}", st.session_state.role)
                        st.success("Annonce publiée avec succès !")
                        st.rerun()
                    else:
                        st.warning("Veuillez remplir le titre et le contenu.")

    with tab2:
        st.subheader("Historique des publications")
        
        # Lecture des annonces
        df_ann = pd.read_sql("SELECT id, title as Titre, type as Type, department_name as Cible, date_pub as Date FROM announcements ORDER BY id DESC", conn)
        
        if df_ann.empty:
            st.info("Aucune annonce publiée pour le moment.")
        else:
            st.dataframe(df_ann, use_container_width=True)
            
            # --- CRUD : Suppression ---
            if can_publish:
                st.divider()
                st.markdown("#### 🗑️ Supprimer une annonce")
                ann_to_delete = st.selectbox("Choisir l'annonce à retirer", 
                                             options=df_ann['id'], 
                                             format_func=lambda x: f"ID {x} - {df_ann[df_ann['id']==x]['Titre'].values[0]}")
                
                if st.button("Confirmer la suppression", type="primary"):
                    conn.execute("DELETE FROM announcements WHERE id = ?", (ann_to_delete,))
                    conn.commit()
                    add_log(st.session_state.username, f"Suppression annonce ID {ann_to_delete}", st.session_state.role)
                    st.success("Annonce supprimée.")
                    st.rerun()