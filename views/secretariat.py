import streamlit as st
import pandas as pd
import os
from datetime import date
from models.database import get_connection, add_log
from controllers.auth_controller import check_privilege

def show_secretariat():
    st.title("📝 Secrétariat & Communication")
    conn = get_connection()

    # Vérification du privilège pour publier
    can_publish = check_privilege("PUB_ANNONCE")

    # Ajout d'un 3ème onglet pour les documents
    tab1, tab2, tab3 = st.tabs(["📢 Publier une annonce", "🗂️ Gérer les annonces", "📄 Documents Administratifs"])

    # ==========================================
    # ONGLET 1 : PUBLIER UNE ANNONCE (AVEC IMAGE)
    # ==========================================
    with tab1:
        if not can_publish:
            st.error("🚫 Vous n'avez pas les privilèges nécessaires pour publier.")
        else:
            st.subheader("Nouvelle Publication")
            with st.form("publish_form", clear_on_submit=True):
                title = st.text_input("Titre de l'annonce *")
                content = st.text_area("Contenu du message *")
                
                # --- NOUVEAU : Champ pour l'image ---
                image_file = st.file_uploader("Joindre une image (Optionnel)", type=['png', 'jpg', 'jpeg'])

                c1, c2 = st.columns(2)
                v_type = c1.selectbox("Visibilité", ["Public", "Privé"])

                depts_df = pd.read_sql("SELECT name FROM departments", conn)
                depts = ["Tous"] + depts_df['name'].tolist()
                v_dept = c2.selectbox("Département ciblé", options=depts, help="Si Public, 'Tous' est recommandé.")

                if st.form_submit_button("🚀 Publier l'annonce"):
                    if title and content:
                        image_path = None
                        
                        # Traitement de l'image si elle est fournie
                        if image_file:
                            # Créer le dossier s'il n'existe pas
                            os.makedirs("assets/uploads", exist_ok=True)
                            image_path = os.path.join("assets/uploads", image_file.name)
                            # Sauvegarder le fichier physiquement
                            with open(image_path, "wb") as f:
                                f.write(image_file.getbuffer())

                        # Insertion dans la base de données avec le chemin de l'image
                        conn.execute("""
                            INSERT INTO announcements (title, content, type, department_name, date_pub, image_path)
                            VALUES (?, ?, ?, ?, DATE('now'), ?)
                        """, (title, content, v_type, v_dept, image_path))
                        
                        conn.commit()
                        add_log(st.session_state.username, f"Publication: {title}", st.session_state.role)
                        st.success("Annonce publiée avec succès !")
                        st.rerun()
                    else:
                        st.warning("Veuillez remplir le titre et le contenu.")

    # ==========================================
    # ONGLET 2 : GÉRER LES ANNONCES
    # ==========================================
    with tab2:
        st.subheader("Historique des publications")

        # Lecture des annonces (incluant l'image pour savoir si elle existe)
        df_ann = pd.read_sql("SELECT id, title as Titre, type as Type, department_name as Cible, date_pub as Date, image_path FROM announcements ORDER BY id DESC", conn)

        if df_ann.empty:
            st.info("Aucune annonce publiée pour le moment.")
        else:
            # On crée une colonne visuelle pour indiquer si une image est jointe
            df_ann['Image'] = df_ann['image_path'].apply(lambda x: "🖼️ Oui" if pd.notna(x) and x != "" else "Non")
            st.dataframe(df_ann[['id', 'Titre', 'Type', 'Cible', 'Date', 'Image']], use_container_width=True)

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

    # ==========================================
    # ONGLET 3 : DOCUMENTS ADMINISTRATIFS
    # ==========================================
    with tab3:
        st.subheader("Générateur de Documents Administratifs")
        
        # Choix du modèle de document
        doc_type = st.selectbox("Sélectionnez le type de document", [
            "Attestation de Baptême", 
            "Lettre de Recommandation",
            "Certificat de Mariage"
        ])

        st.divider()

        # Construction dynamique du formulaire selon le document
        col_form, col_preview = st.columns([1, 1.2])
        
        with col_form:
            st.write("📝 **Saisie des informations**")
            
            # --- Champs dynamiques ---
            if doc_type == "Attestation de Baptême":
                nom = st.text_input("Nom complet du fidèle")
                date_bap = st.date_input("Date du baptême")
                pasteur = st.text_input("Nom du Pasteur officiant", value="Pasteur Titulaire")
                lieu = st.text_input("Lieu du baptême", value="Kinshasa")
            
            elif doc_type == "Lettre de Recommandation":
                nom = st.text_input("Nom complet du membre")
                eglise_dest = st.text_input("Église de destination")
                motif = st.text_area("Motif de la recommandation (ex: Déménagement)")
            
            elif doc_type == "Certificat de Mariage":
                epoux = st.text_input("Nom de l'époux")
                epouse = st.text_input("Nom de l'épouse")
                date_mar = st.date_input("Date de la bénédiction nuptiale")
                pasteur = st.text_input("Pasteur officiant")

        # --- Génération de l'aperçu ---
        with col_preview:
            st.write("📄 **Aperçu du document**")
            
            # Encadré simulant une feuille A4
            with st.container(border=True):
                st.markdown("<h2 style='text-align: center;'>Église COMPASMG</h2>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: right;'>Fait le {date.today().strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)

                if doc_type == "Attestation de Baptême":
                    st.markdown(f"<h3 style='text-align: center;'>{doc_type.upper()}</h3>", unsafe_allow_html=True)
                    st.write(f"Nous soussignés, certifions par la présente que le/la bien-aimé(e) **{nom if nom else '[Nom]'}** "
                             f"a été baptisé(e) d'eau par immersion le **{date_bap.strftime('%d/%m/%Y')}** à **{lieu}**, "
                             f"conformément à l'ordonnance de notre Seigneur Jésus-Christ.")
                    st.write(f"Ce baptême a été officié par le **{pasteur}**.")
                
                elif doc_type == "Lettre de Recommandation":
                    st.markdown(f"<h3 style='text-align: center;'>{doc_type.upper()}</h3>", unsafe_allow_html=True)
                    st.write(f"À l'attention du pasteur de l'église **{eglise_dest if eglise_dest else '[Église destination]'}**.")
                    st.write(f"Nous vous recommandons notre frère/sœur **{nom if nom else '[Nom]'}**, qui a été un membre fidèle de notre assemblée.")
                    st.write(f"Motif : {motif if motif else '[Motif]'}")
                    st.write("Veuillez l'accueillir dans l'amour du Seigneur.")
                
                elif doc_type == "Certificat de Mariage":
                    st.markdown(f"<h3 style='text-align: center;'>BÉNÉDICTION NUPTIALE</h3>", unsafe_allow_html=True)
                    st.write(f"Il est certifié que **{epoux if epoux else '[Nom Époux]'}** et **{epouse if epouse else '[Nom Épouse]'}** "
                             f"ont reçu la bénédiction nuptiale le **{date_mar.strftime('%d/%m/%Y')}**.")
                    st.write(f"Cérémonie présidée par le **{pasteur if pasteur else '[Pasteur]'}**.")

                st.markdown("<br><br><br>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: right;'><b>La Direction / Le Secrétariat</b></p>", unsafe_allow_html=True)

        if st.button("🖨️ Préparer pour l'impression (Copier le texte)"):
            st.success("Vous pouvez maintenant sélectionner le texte dans l'aperçu ci-dessus, le copier et le coller dans Word ou l'imprimer directement !")
