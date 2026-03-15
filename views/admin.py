import streamlit as st
import pandas as pd
import hashlib
from models.database import get_connection, add_log

def show_admin_panel():
    st.title("⚙️ Administration")
    conn = get_connection()
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Membres", "🏢 Départements", "⚙️ Paramètres", "📜 Logs"]) 
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
       st.subheader("🎨 Personnalisation du Thème")
        
        # Récupération des paramètres actuels depuis la DB
        settings_df = pd.read_sql("SELECT * FROM settings", conn)
        settings_dict = dict(zip(settings_df['key'], settings_df['value']))

        with st.form("theme_form"):
            col1, col2 = st.columns(2)
            
            # --- Couleurs ---
            primary_color = col1.color_picker("Couleur Principale (Boutons, En-têtes)", 
                                             value=settings_dict.get('primary_color', '#2E7D32'))
            bg_color = col2.color_picker("Couleur d'Arrière-plan", 
                                         value=settings_dict.get('bg_color', '#F5F7F9'))
            text_color = col1.color_picker("Couleur du Texte", 
                                          value=settings_dict.get('text_color', '#1A1A1A'))
            
            # --- Textes ---
            app_name = col2.text_input("Nom de l'Église / Application", 
                                      value=settings_dict.get('app_name', 'COMPASMG'))
            
            st.divider()
            
            # --- Style des Boutons ---
            btn_radius = st.slider("Arrondi des boutons (pixels)", 0, 25, 
                                  int(settings_dict.get('btn_radius', '8')))

            if st.form_submit_button("💾 Appliquer le nouveau thème"):
                # Sauvegarde massive dans la table settings
                new_settings = [
                    ('primary_color', primary_color),
                    ('bg_color', bg_color),
                    ('text_color', text_color),
                    ('app_name', app_name),
                    ('btn_radius', str(btn_radius))
                ]
                
                for key, val in new_settings:
                    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, val))
                
                conn.commit()
                st.success("✨ Thème mis à jour ! Rechargez la page pour voir les changements.")
                st.rerun()


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