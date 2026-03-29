import streamlit as st
import pandas as pd
import hashlib
import os
from models.database import get_connection

def show_home():
    st.title("🏠 Accueil COMPASSION MONT-NGAFULA /HABITAT ")
    conn = get_connection()
    

    from fpdf import FPDF
    import io

    # --- 0. MIGRATION & SÉCURITÉ BASE DE DONNÉES ---
    try:
        conn.execute("ALTER TABLE finances ADD COLUMN billetage_cdf TEXT DEFAULT '{}'")
        conn.execute("ALTER TABLE finances ADD COLUMN billetage_usd TEXT DEFAULT '{}'")
        conn.commit()
    except:
        pass

    # Création de la table Eglise
    conn.execute("""
        CREATE TABLE IF NOT EXISTS eglise (
            id INTEGER PRIMARY KEY CHECK (id = 1), -- On force une seule ligne
            denomination TEXT,
            extensionDe TEXT,
            dateOuverture DATE,
            date1culte DATE,
            adresse TEXT,
            rccm TEXT,
            idnat TEXT,
            telephone TEXT,
            Responsable TEXT
        )
    """)
    # Insertion par défaut si la table est vide
    conn.execute("""
        INSERT OR IGNORE INTO eglise (id, denomination) 
        VALUES (1, 'LA COMPASSION MONT-NGAFULA/HABITAT')
    """)
    conn.commit()

  


    

    # Récupération des infos de l'église pour le PDF
    info_eglise = conn.execute("SELECT * FROM eglise WHERE id = 1").fetchone()
    # On convertit le résultat en dictionnaire pour un accès facile
    cols = ['id', 'denomination', 'extensionDe', 'dateOuverture', 'date1culte', 'adresse', 'rccm', 'idnat', 'telephone', 'Responsable']
    eglise_dict = dict(zip(cols, info_eglise)) if info_eglise else {}

    class PDFReport(FPDF):
        def header(self):
            # En-tête : LA COMPASSION MONT-NGAFULA/HABITAT
            self.set_font('Arial', 'B', 14)
            denomination = eglise_dict.get('denomination', 'LA COMPASSION MONT-NGAFULA/HABITAT')
            self.cell(0, 10, denomination, 0, 1, 'C')
            self.ln(5)

        def footer(self):
            # Positionnement à 1.5 cm du bas
            self.set_y(-15)
            
            # 1. La fine ligne bleu ciel (RGB: 135, 206, 235)
            self.set_draw_color(135, 206, 235)
            self.set_line_width(0.5)
            self.line(10, self.get_y(), 200, self.get_y())
            
            # 2. Les informations de l'entreprise
            self.set_font('Arial', 'I', 8)
            self.set_text_color(100, 100, 100) # Gris foncé
            
            # Construction du texte du bas de page
            t_denom = eglise_dict.get('denomination', '')
            t_date = f"1er culte: {eglise_dict.get('date1culte', '')}"
            t_adr = eglise_dict.get('adresse', '')
            t_rccm = f"RCCM: {eglise_dict.get('rccm', '')}"
            t_idnat = f"IDNAT: {eglise_dict.get('idnat', '')}"
            t_tel = f"Tél: {eglise_dict.get('telephone', '')}"
            
            footer_text = f"{t_denom} | {t_date} | {t_adr} | {t_rccm} | {t_idnat} | {t_tel}"
            
            # Affichage centré
            self.set_y(-12)
            self.cell(0, 10, footer_text, 0, 0, 'C')

    def generer_pdf(df_rapport, date_debut, date_fin):
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Rapport Financier : du {date_debut} au {date_fin}", 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font("Arial", size=10)
        # Logique simplifiée pour écrire le contenu du dataframe dans le PDF
        for label in df_rapport['label'].unique():
            df_label = df_rapport[df_rapport['label'] == label]
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, f"{label}", 0, 1, 'L')
            
            for _, row in df_label.iterrows():
                pdf.set_font("Arial", '', 10)
                txt = f"  - {row['category']} ({row['type']}) : {format_fr(row['total_cdf'])} FC | {format_fr(row['total_usd'])} $"
                pdf.cell(0, 6, txt, 0, 1, 'L')
            pdf.ln(3)
            
        return pdf.output(dest='S').encode('latin-1') # Retourne le PDF en bytes




    # --- LOGIQUE DE CONNEXION ---
    if not st.session_state.get('logged_in'):
        st.write("### Identifiez-vous")
        username_input = st.text_input("Nom d'utilisateur")
        
        if username_input:
            user_data = conn.execute("SELECT id, isUser, password, role, privileges FROM members WHERE nom = ?", (username_input,)).fetchone()
            
            if user_data:
                member_id, is_user, pwd_hash, role, privs = user_data
                if is_user == 1 and pwd_hash:
                    pwd_input = st.text_input("Mot de passe", type="password")
                    if st.button("Se connecter"):
                        if hashlib.sha256(pwd_input.encode()).hexdigest() == pwd_hash:
                            st.session_state.update({"logged_in": True, "username": username_input, "user_id": member_id, "role": role, "privileges": privs.split(",")})
                            st.rerun()
                        else:
                            st.error("Mot de passe incorrect.")
                else:
                    if st.button("Accéder"):
                        st.session_state.update({"logged_in": True, "username": username_input, "user_id": member_id, "role": "Membre", "privileges": []})
                        st.rerun()
            else:
                st.warning("Utilisateur non trouvé.")
        st.divider()

    # --- ANNONCES PUBLIQUES ---
    st.subheader("📢 Annonces Publiques")
    df = pd.read_sql("SELECT title, content, date_pub, image_path FROM announcements WHERE type='Public' ORDER BY date_pub DESC", conn)
    
    if df.empty:
        st.info("Aucune annonce pour le moment.")
    else:
        for _, row in df.iterrows():
            with st.container():
                st.markdown(f"### {row['title']}")
                st.caption(f"Publié le {row['date_pub']}")
                
                # --- AFFICHAGE DE L'IMAGE SI ELLE EXISTE ---
                if pd.notna(row['image_path']) and row['image_path'] != "":
                    if os.path.exists(row['image_path']):
                        st.image(row['image_path'], use_container_width=True)
                
                st.write(row['content'])
                st.divider()
