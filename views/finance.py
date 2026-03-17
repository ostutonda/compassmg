import streamlit as st
import pandas as pd
from datetime import date
import json
from models.database import get_connection, add_log


def format_money(amount):
    # Formatage : Espace pour les milliers, virgule pour les décimales
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",").replace(" ", " ")


def show_finance():
    st.title("💰 Trésorerie & Opérations")
    conn = get_connection()
    
    # --- FONCTION DE CALCUL DU SOLDE PAR CATÉGORIE ---
    def get_category_balance(cat_name):
        res = conn.execute("""
            SELECT 
                SUM(CASE WHEN type = 'Entrée' THEN total_usd ELSE -total_usd END) as solde_usd,
                SUM(CASE WHEN type = 'Entrée' THEN total_cdf ELSE -total_cdf END) as solde_cdf
            FROM finances WHERE category = ?
        """, (cat_name,)).fetchone()
        return (res[0] or 0.0, res[1] or 0.0)

    # --- 1. CRUD DES CATÉGORIES (SIDEBAR) ---
    with st.sidebar:
        st.subheader("📁 Gérer les Catégories")
        
        # AJOUT
        new_cat = st.text_input("Nouvelle catégorie")
        if st.button("➕ Ajouter"):
            if new_cat:
                conn.execute("INSERT OR IGNORE INTO finance_categories (name) VALUES (?)", (new_cat,))
                conn.commit()
                st.rerun()

        st.divider()
        
        # LISTE ET SUPPRESSION SÉCURISÉE
        cats_df = pd.read_sql("SELECT * FROM finance_categories", conn)
        for _, row in cats_df.iterrows():
            c1, c2 = st.columns([7, 2])
            usd, cdf = get_category_balance(row['name'])
            
            c1.text(f"{row['name']}")
            c1.caption(f"Solde: {format_money(usd)} $ | {format_money(cdf)} Fc")
            
            # Condition de suppression : Solde doit être 0
            if usd == 0 and cdf == 0:
                if c2.button("🗑️", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM finance_categories WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.rerun()
            else:
                c2.disabled = True # Désactivé si solde > 0

    # --- 2. TRANSFERT ENTRE CATÉGORIES ---
    with st.expander("🔄 Transfert de solde (Catégorie à Catégorie)"):
        with st.form("transfer_form"):
            col1, col2 = st.columns(2)
            cat_source = col1.selectbox("Source (Sortie)", options=cats_df['name'].tolist())
            cat_dest = col2.selectbox("Destination (Entrée)", options=cats_df['name'].tolist())
            
            m1, m2 = st.columns(2)
            format_money(amt_usd) = m1.number_input("Montant USD to Transfer", min_value=0.0) 
            format_money(amt_cdf) = m2.number_input("Montant CDF to Transfer", min_value=0.0)
            
            if st.form_submit_button("Confirmer le transfert"):
                if cat_source != cat_dest and (amt_usd > 0 or amt_cdf > 0):
                    # 1. Sortie de la source
                    conn.execute("INSERT INTO finances (date_trans, type, category, label, total_usd, total_cdf) VALUES (DATE('now'), 'Sortie', ?, ?, ?, ?)",
                                 (cat_source, f"Transfert vers {cat_dest}", amt_usd, amt_cdf))
                    # 2. Entrée dans la destination
                    conn.execute("INSERT INTO finances (date_trans, type, category, label, total_usd, total_cdf) VALUES (DATE('now'), 'Entrée', ?, ?, ?, ?)",
                                 (cat_dest, f"Reçu de {cat_source}", amt_usd, amt_cdf))
                    conn.commit()
                    st.success("Transfert effectué !")
                    st.rerun()

    # --- 3. SAISIE DES OPÉRATIONS (DÉPENSES PAR CATÉGORIE) ---
    # Ici, modifier la logique : même pour une 'Sortie', on propose la catégorie
    tab1, tab2 = st.tabs(["📝 Saisie", "📊 Rapports"])
    
    with tab1:
        with st.container(border=True):
            t_type = st.selectbox("Flux", ["Entrée", "Sortie"])
            t_cat = st.selectbox("Appliquer à la catégorie", options=cats_df['name'].tolist())
            t_label = st.text_input("Libellé / Justification")
            
            # ... (votre code de billetage ici) ...
            # Lors de l'affichage du total final dans la page :
            st.info(f"Montant saisi : **{format_money(total_usd)} $** | **{format_money(total_cdf)} Fc**")
