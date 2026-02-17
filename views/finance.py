import streamlit as st
from models.database import get_connection
import pandas as pd
import plotly.express as px
from datetime import datetime

def show_finance():
    st.title("💰 Gestion de la Trésorerie")
    conn = get_connection()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Saisie d'opération")
        with st.form("finance_form"):
            t_type = st.selectbox("Type", ["Entrée", "Sortie"])
            cat = st.selectbox("Catégorie", ["Dîme", "Offrande", "Don", "Loyer", "Action Sociale", "Frais Fixes"])
            montant = st.number_input("Montant ($)", min_value=0.0)
            desc = st.text_input("Commentaire")
            
            if st.form_submit_button("Enregistrer"):
                conn.execute("INSERT INTO finance (type, categorie, montant, date, description) VALUES (?,?,?,?,?)",
                             (t_type, cat, montant, datetime.now().date(), desc))
                conn.commit()
                st.success("Transaction validée !")

    with col2:
        st.subheader("Rapports Visuels")
        df = pd.read_sql("SELECT * FROM finance", conn)
        if not df.empty:
            fig = px.bar(df, x='categorie', y='montant', color='type', title="Répartition par catégorie")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df, use_container_width=True)