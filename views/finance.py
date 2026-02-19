import streamlit as st
import pandas as pd
from models.database import get_connection, add_log
from controllers.auth_controller import check_privilege

# Exemple pour la Finance
col1, col2, col3 = st.columns(3)
col1.metric("Recettes du mois", "4,500 $", "+12%")
col2.metric("Dépenses", "1,200 $", "-5%")
col3.metric("Solde Net", "3,300 $", delta_color="normal")




def show_finance():
    st.title("💰 Trésorerie & Rapports")
    conn = get_connection()
    
    # Configuration du taux (très important en RDC)
    st.sidebar.subheader("Configuration Change")
    taux_du_jour = st.sidebar.number_input("Taux (1$ = ? FC)", value=2800, step=10)

    tab1, tab2 = st.tabs(["📊 Transactions", "📈 Rapports Financiers"])

    with tab1:
        col_a, col_b = st.columns([1, 2])
        
        with col_a:
            st.subheader("Nouvelle Opération")
            with st.form("fin_form", clear_on_submit=True):
                # Catégories dynamiques
                cats = pd.read_sql("SELECT name FROM finance_categories", conn)['name'].tolist()
                
                amount = st.number_input("Montant", min_value=0.0)
                devise = st.selectbox("Monnaie", ["USD ($)", "CDF (Fc)"])
                category = st.selectbox("Catégorie", options=cats if cats else ["Général"])
                m_type = st.radio("Type", ["Entrée", "Sortie"])
                desc = st.text_input("Description / Motif")
                
                if st.form_submit_button("Enregistrer"):
                    curr = "USD" if "USD" in devise else "CDF"
                    conn.execute("""
                        INSERT INTO finance_transactions (category, amount, currency, rate, date, type, description)
                        VALUES (?, ?, ?, ?, DATE('now'), ?, ?)
                    """, (category, amount, curr, taux_du_jour, m_type, desc))
                    conn.commit()
                    st.success("Transaction enregistrée !")
                    st.rerun()

        with col_b:
            st.subheader("Gestion des Catégories")
            new_cat = st.text_input("Nom de la catégorie (ex: Offrandes, Loyer)")
            if st.button("Ajouter Catégorie"):
                conn.execute("INSERT OR IGNORE INTO finance_categories VALUES (?)", (new_cat,))
                conn.commit()
                st.rerun()

    with tab2:
        st.subheader("Rapports Multi-Devises")
        df = pd.read_sql("SELECT * FROM finance_transactions ORDER BY date DESC", conn)
        
        if df.empty:
            st.info("Aucune transaction enregistrée.")
        else:
            # Choix de l'affichage du rapport
            mode = st.radio("Afficher les montants en :", ["Devise d'origine", "Tout en USD ($)", "Tout en CDF (Fc)"], horizontal=True)
            
            # Calcul des colonnes pour le rapport
            if mode == "Tout en USD ($)":
                df['Montant Rapport'] = df.apply(lambda r: r['amount'] if r['currency'] == 'USD' else r['amount'] / r['rate'], axis=1)
                df['Devise'] = "USD"
            elif mode == "Tout en CDF (Fc)":
                df['Montant Rapport'] = df.apply(lambda r: r['amount'] if r['currency'] == 'CDF' else r['amount'] * r['rate'], axis=1)
                df['Devise'] = "CDF"
            else:
                df['Montant Rapport'] = df['amount']
                df['Devise'] = df['currency']

            # Tri du rapport
            sort_by = st.selectbox("Trier par", ["date", "category", "amount"])
            df = df.sort_values(by=sort_by, ascending=False)
            
            st.dataframe(df[['date', 'category', 'type', 'Montant Rapport', 'Devise', 'description']], use_container_width=True)
            
            # Résumé rapide
            total_in = df[df['type'] == 'Entrée']['Montant Rapport'].sum()
            total_out = df[df['type'] == 'Sortie']['Montant Rapport'].sum()
            st.metric("Solde Net (selon mode choisi)", f"{total_in - total_out:,.2f} {df['Devise'].iloc[0] if not df.empty else ''}")