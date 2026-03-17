import streamlit as st
import pandas as pd
from datetime import date
import json
from models.database import get_connection, add_log


    # --- 1. FONCTION DE FORMATAGE (À mettre tout en haut du fichier) ---
    def format_fr(amount):
        return f"{amount:,.2f}".replace(",", " ").replace(".", ",").replace(" ", " ")

    # --- 2. CRUD DES CATÉGORIES (SIDEBAR) ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Gestion du Taux
        rate_db = conn.execute("SELECT rate FROM exchange_rates WHERE date_rate = ?", (today,)).fetchone()
        current_rate = rate_db[0] if rate_db else 2800.0
        new_rate = st.number_input("Taux (1$ = ? Fc)", value=float(current_rate), step=50.0)
        
        st.divider()
        st.subheader("📁 Catégories (Entrées/Dépenses)")
        
        # AJOUTER
        with st.form("add_cat_form", clear_on_submit=True):
            new_cat = st.text_input("Nom de la catégorie")
            if st.form_submit_button("➕ Ajouter"):
                if new_cat:
                    conn.execute("INSERT OR IGNORE INTO finance_categories (name) VALUES (?)", (new_cat,))
                    conn.commit()
                    st.rerun()

        st.divider()
        
        # LISTE, MODIFICATION ET SUPPRESSION SÉCURISÉE
        cats_df = pd.read_sql("SELECT * FROM finance_categories", conn)
        
        for _, row in cats_df.iterrows():
            with st.container():
                # Calcul du solde pour cette catégorie
                res = conn.execute("""
                    SELECT 
                        SUM(CASE WHEN type = 'Entrée' THEN total_usd ELSE -total_usd END) as s_usd,
                        SUM(CASE WHEN type = 'Entrée' THEN total_cdf ELSE -total_cdf END) as s_cdf
                    FROM finances WHERE category = ?
                """, (row['name'],)).fetchone()
                
                solde_usd = res[0] or 0.0
                solde_cdf = res[1] or 0.0
                
                # Affichage du nom et du solde
                st.write(f"**{row['name']}**")
                st.caption(f"Solde : {format_fr(solde_usd)} $ | {format_fr(solde_cdf)} Fc")
                
                c1, c2 = st.columns(2)
                
                # Bouton de modification (toujours actif)
                if c1.button("✏️", key=f"edit_{row['id']}", use_container_width=True):
                    st.info("Fonction de renommage à venir...")

                # BOUTON SUPPRIMER : On vérifie si le solde est à ZÉRO
                est_vide = (solde_usd == 0 and solde_cdf == 0)
                
                # On passe l'état "disabled" directement dans le bouton
                if c2.button("🗑️", key=f"del_{row['id']}", 
                             disabled=not est_vide, 
                             help="Impossible de supprimer une catégorie avec un solde actif",
                             use_container_width=True):
                    conn.execute("DELETE FROM finance_categories WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.success(f"{row['name']} supprimée")
                    st.rerun()
                st.divider()


    # --- 3. TRANSFERT ENTRE CATÉGORIES ---
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

    # --- 4. SAISIE DES OPÉRATIONS (DÉPENSES PAR CATÉGORIE) ---
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
