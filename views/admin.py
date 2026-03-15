import streamlit as st
import pandas as pd
import hashlib
from models.database import get_connection, add_log

def show_admin_panel():
    st.title("⚙️ Administration")
    conn = get_connection()
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Users", "📁 Dépts", "📜 Logs", "🎨 Design"])

    with tab1:
        st.subheader("Affecter un rôle à un membre")
        members_df = pd.read_sql("SELECT id, nom, prenom FROM members", conn)
        member_opts = {f"{r['nom']} {r['prenom']}": r['id'] for _, r in members_df.iterrows()}
        
        if not member_opts:
            st.warning("⚠️ Aucun membre trouvé. Créez d'abord des membres dans le menu dédié.")
        else:
            with st.form("user_assignment"):
                m_name = st.selectbox("Sélectionner le membre", options=list(member_opts.keys()))
                u_name = st.text_input("Identifiant de connexion")
                u_pass = st.text_input("Mot de passe", type="password")
                u_role = st.selectbox("Rôle", ["Admin", "Secretaire", "Tresorier"])
                
                # Gestion des privilèges (Boutons/Actions)
                all_privs = ["MOD_MEMBRE", "SUP_MEMBRE", "PUB_ANNONCE", "GEN_FINANCE"]
                u_privs = st.multiselect("Privilèges additionnels", all_privs)

                if st.form_submit_button("Créer le compte"):
                    if u_name and u_pass:
                        pwd_h = hashlib.sha256(u_pass.encode()).hexdigest()
                        priv_str = ",".join(u_privs)
                        try:
                            conn.execute("INSERT INTO users (member_id, username, password, role, privileges) VALUES (?,?,?,?,?)",
                                         (member_opts[m_name], u_name, pwd_h, u_role, priv_str))
                            conn.commit()
                            add_log(st.session_state.username, f"Création user {u_name}", st.session_state.role)
                            st.success("Utilisateur créé avec succès !")
                        except: st.error("L'identifiant existe déjà.")

# --- TAB 2 : CRUD DÉPARTEMENTS ---
    with tab2:
        st.subheader("Liste des Départements")
        
        # 1. LECTURE (Read)
        df_depts = pd.read_sql("SELECT name as Nom, created_at as 'Date Création' FROM departments", conn)
        
        if df_depts.empty:
            st.info("Aucun département enregistré.")
        else:
            st.dataframe(df_depts, use_container_width=True)

        st.divider()
        
        col_create, col_edit = st.columns(2)

        # 2. CRÉATION (Create)
        with col_create:
            st.markdown("#### ✨ Nouveau Département")
            with st.form("form_add_dept"):
                new_name = st.text_input("Nom du département")
                new_date = st.date_input("Date de fondation")
                if st.form_submit_button("Ajouter"):
                    if new_name:
                        try:
                            conn.execute("INSERT INTO departments (name, created_at) VALUES (?,?)", (new_name, new_date))
                            conn.commit()
                            add_log(st.session_state.username, f"Création dépt: {new_name}", st.session_state.role)
                            st.success(f"Département '{new_name}' créé !")
                            st.rerun()
                        except:
                            st.error("Ce nom existe déjà.")
                    else:
                        st.error("Le nom est obligatoire.")

        # 3. MODIFICATION & SUPPRESSION (Update & Delete)
        with col_edit:
            st.markdown("#### ✏️ Modifier / Supprimer")
            if not df_depts.empty:
                selected_dept = st.selectbox("Choisir un département", df_depts['Nom'])
                
                # Récupérer les données actuelles
                current_date = df_depts[df_depts['Nom'] == selected_dept]['Date Création'].values[0]
                
                edit_name = st.text_input("Renommer en", value=selected_dept)
                edit_date = st.date_input("Modifier la date", value=pd.to_datetime(current_date))

                c1, c2 = st.columns(2)
                
                # UPDATE
                if c1.button("💾 Enregistrer"):
                    # On met à jour le département ET les membres liés (ON UPDATE CASCADE manuel)
                    conn.execute("UPDATE members SET department_name = ? WHERE department_name = ?", (edit_name, selected_dept))
                    conn.execute("UPDATE announcements SET department_name = ? WHERE department_name = ?", (edit_name, selected_dept))
                    conn.execute("UPDATE departments SET name = ?, created_at = ? WHERE name = ?", (edit_name, edit_date, selected_dept))
                    conn.commit()
                    st.success("Mise à jour effectuée !")
                    st.rerun()

                # DELETE
                if c2.button("🗑️ Supprimer", type="secondary"):
                    # Vérifier s'il y a des membres
                    check_members = conn.execute("SELECT COUNT(*) FROM members WHERE department_name = ?", (selected_dept,)).fetchone()[0]
                    if check_members > 0:
                        st.error(f"Impossible de supprimer : {check_members} membres y sont rattachés.")
                    else:
                        conn.execute("DELETE FROM departments WHERE name = ?", (selected_dept,))
                        conn.commit()
                        st.warning(f"Département '{selected_dept}' supprimé.")
                        st.rerun()
            else:
                st.write("Rien à modifier.")



    with tabs[3]:
        st.subheader("📜 Historique des actions (Logs)")
    
    # On utilise 'user' (le nom en base) et on peut le renommer en 'username' pour l'affichage
    query = "SELECT timestamp, user as username, role, action FROM logs ORDER BY timestamp DESC LIMIT 100"
    
    try:
        logs_df = pd.read_sql(query, conn)
        st.dataframe(logs_df, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur lors de la lecture des logs : {e}")
        
    with tab4:
        st.subheader("Personnalisation de l'interface")
        
        # Récupération des réglages actuels
        settings = dict(conn.execute("SELECT key, value FROM settings").fetchall())
        
        with st.form("design_settings"):
            new_name = st.text_input("Nom de l'application", value=settings.get('app_name'))
            new_primary = st.color_picker("Couleur principale (Boutons, Titres)", value=settings.get('primary_color'))
            new_bg = st.color_picker("Couleur de fond", value=settings.get('bg_color'))
            new_logo = st.text_input("URL du logo (Lien vers une image en ligne)", value=settings.get('logo_url'))
            
            if st.form_submit_button("Appliquer les changements"):
                conn.execute("UPDATE settings SET value = ? WHERE key = 'app_name'", (new_name,))
                conn.execute("UPDATE settings SET value = ? WHERE key = 'primary_color'", (new_primary,))
                conn.execute("UPDATE settings SET value = ? WHERE key = 'bg_color'", (new_bg,))
                conn.execute("UPDATE settings SET value = ? WHERE key = 'logo_url'", (new_logo,))
                conn.commit()
                st.success("Design mis à jour ! Rechargez la page pour appliquer.")
                st.rerun()