import streamlit as st
import pandas as pd
from datetime import date
import json
from models.database import get_connection, add_log

def format_fr(amount):
    """Affiche 1 250,50 au lieu de 1250.5"""
    if amount is None: amount = 0.0
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",").replace(" ", " ")

def show_finance():
    st.title("💰 Trésorerie & Opérations")
    conn = get_connection()
    today = date.today()

    # --- 1. CRUD DES CATÉGORIES (SIDEBAR) ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Gestion du Taux
        rate_db = conn.execute("SELECT rate FROM exchange_rates WHERE date_rate = ?", (today,)).fetchone()
        current_rate = rate_db[0] if rate_db else 2800.0
        new_rate = st.number_input("Taux (1$ = ? Fc)", value=float(current_rate), step=50.0)
        
        st.divider()
        st.subheader("📁 Catégories")
        
        # AJOUTER
        with st.form("add_cat_form", clear_on_submit=True):
            new_cat = st.text_input("Nom de la catégorie")
            if st.form_submit_button("➕ Ajouter"):
                if new_cat:
                    conn.execute("INSERT OR IGNORE INTO finance_categories (name) VALUES (?)", (new_cat,))
                    conn.commit()
                    st.rerun()

        st.divider()
        
        # LISTE ET SUPPRESSION SÉCURISÉE
        cats_df = pd.read_sql("SELECT * FROM finance_categories", conn)
        for _, row in cats_df.iterrows():
            # Calcul du solde actuel pour la sécurité
            res = conn.execute("""
                SELECT 
                    SUM(CASE WHEN type = 'Entrée' THEN total_usd ELSE -total_usd END) as s_usd,
                    SUM(CASE WHEN type = 'Entrée' THEN total_cdf ELSE -total_cdf END) as s_cdf
                FROM finances WHERE category = ?
            """, (row['name'],)).fetchone()
            
            s_usd, s_cdf = (res[0] or 0.0), (res[1] or 0.0)
            
            with st.container():
                st.write(f"**{row['name']}**")
                st.caption(f"Solde : {format_fr(s_usd)} $ | {format_fr(s_cdf)} Fc")
                
                c1, c2 = st.columns(2)
                # On ne peut supprimer que si le solde est strictement 0
                is_empty = (s_usd == 0 and s_cdf == 0)
                
                if c1.button("✏️", key=f"edit_{row['id']}", use_container_width=True):
                    st.toast("Fonction bientôt disponible")

                if c2.button("🗑️", key=f"del_{row['id']}", disabled=not is_empty, use_container_width=True, help="Le solde doit être nul pour supprimer"):
                    conn.execute("DELETE FROM finance_categories WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.rerun()
            st.divider()

    # --- 2. TRANSFERT ENTRE CATÉGORIES ---
    with st.expander("🔄 Transfert de solde (Catégorie à Catégorie)"):
        with st.form("transfer_form"):
            col1, col2 = st.columns(2)
            cat_source = col1.selectbox("Source (Sortie)", options=cats_df['name'].tolist())
            cat_dest = col2.selectbox("Destination (Entrée)", options=cats_df['name'].tolist())

            m1, m2 = st.columns(2)
            # CORRECTION : On assigne la valeur à une variable, pas à une fonction !
            amt_usd = m1.number_input("Montant USD à transférer", min_value=0.0) 
            amt_cdf = m2.number_input("Montant CDF à transférer", min_value=0.0)

            if st.form_submit_button("Confirmer le transfert"):
                if cat_source != cat_dest and (amt_usd > 0 or amt_cdf > 0):
                    # Sortie de la source
                    conn.execute("INSERT INTO finances (date_trans, type, category, label, total_usd, total_cdf) VALUES (?, 'Sortie', ?, ?, ?, ?)",
                                 (today, cat_source, f"Transfert vers {cat_dest}", amt_usd, amt_cdf))
                    # Entrée dans la destination
                    conn.execute("INSERT INTO finances (date_trans, type, category, label, total_usd, total_cdf) VALUES (?, 'Entrée', ?, ?, ?, ?)",
                                 (today, cat_dest, f"Reçu de {cat_source}", amt_usd, amt_cdf))
                    conn.commit()
                    st.success("Transfert effectué !")
                    st.rerun()
                else:
                    st.error("Vérifiez les catégories et les montants.")

    # --- 3. SAISIE DES OPÉRATIONS ---
    tab1, tab2 = st.tabs(["📝 Saisie", "📊 Rapports & Historique"])

    with tab1:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            t_type = c1.selectbox("Flux", ["Entrée", "Sortie"])
            t_cat = c2.selectbox("Appliquer à la catégorie", options=cats_df['name'].tolist())
            t_label = st.text_input("Libellé / Justification (Obligatoire pour les sorties)")

            # Simulation de montants (Ici vous mettriez votre bloc de billetage)
            col_m1, col_m2 = st.columns(2)
            total_usd = col_m1.number_input("Montant Total USD ($)", min_value=0.0, key="main_usd")
            total_cdf = col_m2.number_input("Montant Total CDF (Fc)", min_value=0.0, key="main_cdf")

            if st.button("✅ Valider l'opération"):
                if t_type == "Sortie" and not t_label:
                    st.error("Veuillez saisir un libellé pour justifier la dépense.")
                elif total_usd == 0 and total_cdf == 0:
                    st.warning("Veuillez saisir un montant.")
                else:
                    conn.execute("""
                        INSERT INTO finances (date_trans, type, category, label, total_usd, total_cdf, rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (today, t_type, t_cat, t_label, total_usd, total_cdf, new_rate))
                    conn.commit()
                    st.success(f"Opération enregistrée : {format_fr(total_usd)} $ | {format_fr(total_cdf)} Fc")
                    st.rerun()

            # Affichage formaté du montant en cours de saisie
            st.info(f"Montant saisi : **{format_fr(total_usd)} $** | **{format_fr(total_cdf)} Fc**")

    with tab2:
        st.subheader("Dernières transactions")
        history = pd.read_sql("SELECT date_trans, type, category, label, total_usd, total_cdf FROM finances ORDER BY id DESC LIMIT 20", conn)
        # Application du formatage sur les colonnes du tableau pour l'affichage
        history['total_usd'] = history['total_usd'].apply(format_fr)
        history['total_cdf'] = history['total_cdf'].apply(format_fr)
        st.dataframe(history, use_container_width=True)
