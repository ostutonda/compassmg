import streamlit as st
import pandas as pd
from datetime import date
from models.database import get_connection, add_log

def show_members():
    st.title("👥 Gestion des Membres")
    conn = get_connection()

    # --- ONGLES : AJOUT / MODIFICATION / LISTE ---
    tab_list, tab_add, tab_edit = st.tabs(["📋 Liste des membres", "➕ Ajouter", "✏️ Modifier"])

    # --- 1. ONGLET LISTE ---
    with tab_list:
        st.subheader("Répertoire des membres")
        df_display = pd.read_sql("""
            SELECT id, nom, prenom, sexe, telephone, etat_civil, profession 
            FROM members ORDER BY nom ASC
        """, conn)
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # --- 2. ONGLET AJOUTER ---
    with tab_add:
        with st.form("form_add_member", clear_on_submit=True):
            render_member_form() # Utilisation d'une fonction interne pour éviter la répétition
            if st.form_submit_button("Enregistrer le nouveau membre"):
                save_member(conn, is_update=False)

    # --- 3. ONGLET MODIFIER ---
    with tab_edit:
        st.subheader("Modifier les informations d'un membre")
        
        # Sélection du membre
        members_list = pd.read_sql("SELECT id, nom || ' ' || prenom as full_name FROM members", conn)
        member_to_edit = st.selectbox("Choisir le membre à modifier", 
                                      options=members_list['id'].tolist(),
                                      format_func=lambda x: members_list.set_index('id').loc[x, 'full_name'])

        if member_to_edit:
            # Charger les données actuelles
            curr = conn.execute("SELECT * FROM members WHERE id = ?", (member_to_edit,)).fetchone()
            columns = [column[0] for column in conn.execute("SELECT * FROM members LIMIT 1").description]
            data = dict(zip(columns, curr))

            with st.form("form_edit_member"):
                # On pré-remplit les champs avec 'data'
                updated_data = render_member_form(data)
                
                if st.form_submit_button("💾 Enregistrer les modifications"):
                    save_member(conn, is_update=True, member_id=member_to_edit, data=updated_data)

def render_member_form(default_data=None):
    """Affiche les champs du formulaire, pré-remplis si default_data est fourni."""
    if default_data is None: default_data = {}

    st.subheader("🆔 Identité")
    c1, c2, c3 = st.columns(3)
    nom = c1.text_input("Nom", value=default_data.get('nom', ''))
    prenom = c2.text_input("Prénom", value=default_data.get('prenom', ''))
    postnom = c3.text_input("Postnom", value=default_data.get('postnom', ''))
    
    c4, c5, c6 = st.columns(3)
    sexe_idx = 0 if default_data.get('sexe') == "Masculin" else 1
    sexe = c4.selectbox("Sexe", ["Masculin", "Féminin"], index=sexe_idx)
    lieu_naiss = c5.text_input("Lieu de naissance", value=default_data.get('lieu_naissance', ''))
    
    # Gestion des dates (pour éviter les erreurs si la date est vide)
    try:
        d_naiss = pd.to_datetime(default_data.get('date_naissance')).date()
    except:
        d_naiss = None
    date_naiss = c6.date_input("Date de naissance", value=d_naiss)

    st.subheader("📞 État Civil & Contact")
    c7, c8, c9 = st.columns(3)
    etats = ["Célibataire", "Marié(e)", "Veuf(ve)", "Divorcé(e)"]
    etat_idx = etats.index(default_data.get('etat_civil')) if default_data.get('etat_civil') in etats else 0
    etat_civil = c7.selectbox("État Civil", etats, index=etat_idx)
    telephone = c8.text_input("Téléphone", value=default_data.get('telephone', ''))
    email = c9.text_input("Adresse Mail", value=default_data.get('email', ''))
    adresse = st.text_area("Adresse physique", value=default_data.get('adresse', ''), height=70)

    st.subheader("⛪ Vie Spirituelle & Profession")
    c10, c11 = st.columns(2)
    try:
        d_bapt = pd.to_datetime(default_data.get('date_bapteme')).date()
    except:
        d_bapt = None
    date_bapteme = c10.date_input("Date de baptême", value=d_bapt)
    profession = c11.text_input("Profession", value=default_data.get('profession', ''))

    st.subheader("🚨 Contact en cas d'urgence")
    c12, c13, c14 = st.columns(3)
    u_nom = c12.text_input("Nom & Prénom (Urgence)", value=default_data.get('contact_urgence_nom', ''))
    u_lien = c13.text_input("Lien (ex: Époux...)", value=default_data.get('contact_urgence_lien', ''))
    u_tel = c14.text_input("Tél (Urgence)", value=default_data.get('contact_urgence_tel', ''))

    return locals() # Retourne toutes les variables saisies sous forme de dictionnaire

def save_member(conn, is_update=False, member_id=None, data=None):
    """Gère l'insertion ou la mise à jour en base de données."""
    # Note : 'data' contient les variables du formulaire
    d = data if data else st.session_state # Simplification pour l'exemple
    
    try:
        if is_update:
            sql = """
                UPDATE members SET 
                nom=?, prenom=?, postnom=?, sexe=?, lieu_naissance=?, date_naissance=?,
                etat_civil=?, adresse=?, telephone=?, email=?, date_bapteme=?, profession=?,
                contact_urgence_nom=?, contact_urgence_lien=?, contact_urgence_tel=?
                WHERE id=?
            """
            params = (d['nom'], d['prenom'], d['postnom'], d['sexe'], d['lieu_naiss'], d['date_naiss'],
                      d['etat_civil'], d['adresse'], d['telephone'], d['email'], d['date_bapteme'], d['profession'],
                      d['u_nom'], d['u_lien'], d['u_tel'], member_id)
            msg = "Informations mises à jour !"
        else:
            sql = """
                INSERT INTO members (nom, prenom, postnom, sexe, lieu_naissance, date_naissance,
                etat_civil, adresse, telephone, email, date_bapteme, profession,
                contact_urgence_nom, contact_urgence_lien, contact_urgence_tel)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (d['nom'], d['prenom'], d['postnom'], d['sexe'], d['lieu_naiss'], d['date_naiss'],
                      d['etat_civil'], d['adresse'], d['telephone'], d['email'], d['date_bapteme'], d['profession'],
                      d['u_nom'], d['u_lien'], d['u_tel'])
            msg = "Membre créé avec succès !"

        conn.execute(sql, params)
        conn.commit()
        st.success(msg)
        st.rerun()
    except Exception as e:
        st.error(f"Erreur : {e}")
