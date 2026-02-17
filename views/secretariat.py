import streamlit as st
from models.database import get_connection
from fpdf import FPDF
import pandas as pd
from datetime import datetime

def show_secretariat():
    st.title("📝 Secrétariat & Courriers")
    conn = get_connection()
    
    # Récupérer les membres pour la fusion de documents
    members_df = pd.read_sql("SELECT * FROM members", conn)
    
    if members_df.empty:
        st.warning("⚠️ Aucun membre enregistré. Veuillez d'abord ajouter des membres.")
        return

    st.subheader("Générer une Attestation / Lettre")
    
    # Sélection du membre avec ses 3 noms
    member_list = {f"{r['nom']} {r['prenom']} {r['postnom']}": r for _, r in members_df.iterrows()}
    selected_member_name = st.selectbox("Choisir le membre", options=list(member_list.keys()))
    m = member_list[selected_member_name]

    # Éditeur de texte dynamique
    default_text = f"""OBJET : ATTESTATION DE MEMBRE

Je soussigné, Secrétaire de l'organisation COMPASMG, certifie que :
Monsieur/Madame {m['nom']} {m['prenom']} {m['postnom']}, 
exerçant la profession de {m['qualification']} et résidant au {m['adresse']},
est un membre actif de notre communauté.

Fait à Kinshasa, le {datetime.now().strftime('%d/%m/%Y')}."""

    letter_content = st.text_area("Texte de la lettre", value=default_text, height=300)

    if st.button("📄 Générer le PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "COMPASMG - SECRÉTARIAT GÉNÉRAL", ln=1, align='C')
        pdf.ln(20)
        
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=letter_content.encode('latin-1', 'replace').decode('latin-1'))
        
        pdf_bytes = pdf.output(dest='S')
        st.download_button(
            label="📥 Télécharger le document",
            data=pdf_bytes,
            file_name=f"lettre_{m['nom']}.pdf",
            mime="application/pdf"
        )