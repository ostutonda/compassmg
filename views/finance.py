import streamlit as st
import pandas as pd
from datetime import date
import json
from models.database import get_connection, add_log

def show_finance():
    st.title("💰 Trésorerie & Opérations")
    conn = get_connection()
    today = date.today()

    if 'daily_ops' not in st.session_state:
        st.session_state.daily_ops = []

    # --- 1. CRUD DES CATÉGORIES (SIDEBAR) ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Gestion du Taux
        rate_db = conn.execute("SELECT rate FROM exchange_rates WHERE date_rate = ?", (today,)).fetchone()
        current_rate = rate_db[0] if rate_db else 2800.0
        new_rate = st.number_input("Taux (1$ = ? Fc)", value=float(current_rate), step=50.0)
        
        st.divider()
        st.subheader("📁 Gérer les Catégories")
        
        # CREATE (Ajouter)
        with st.form("add_cat_form", clear_on_submit=True):
            new_cat = st.text_input("Nouvelle catégorie (Entrées)")
            if st.form_submit_button("➕ Ajouter"):
                if new_cat:
                    conn.execute("INSERT OR IGNORE INTO finance_categories (name) VALUES (?)", (new_cat,))
                    conn.commit()
                    st.rerun()

        # READ, UPDATE, DELETE (Modifier / Supprimer)
        cats_df = pd.read_sql("SELECT * FROM finance_categories", conn)
        with st.expander("✏️ Modifier / Supprimer des catégories"):
            for idx, row in cats_df.iterrows():
                c_name, c_upd, c_del = st.columns([5, 2, 2])
                # UPDATE
                new_name = c_name.text_input("Nom", value=row['name'], key=f"name_{row['id']}", label_visibility="collapsed")
                if c_upd.button("💾", key=f"upd_{row['id']}", help="Enregistrer la modification"):
                    conn.execute("UPDATE finance_categories SET name = ? WHERE id = ?", (new_name, row['id']))
                    conn.commit()
                    st.rerun()
                # DELETE
                if c_del.button("🗑️", key=f"del_{row['id']}", help="Supprimer"):
                    conn.execute("DELETE FROM finance_categories WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.rerun()

    # Récupérer la liste à jour des catégories
    categories = pd.read_sql("SELECT name FROM finance_categories", conn)['name'].tolist()

    tab1, tab2 = st.tabs(["📝 Saisie des opérations", "📊 Historique & Rapports"])

    with tab1:
        with st.container(border=True):
            # --- 2. LOGIQUE CONDITIONNELLE FLUX (ENTRÉE/SORTIE) ---
            c1, c2, c3 = st.columns(3)
            t_type = c1.selectbox("Flux", ["Entrée", "Sortie"])
            t_date = c3.date_input("Date", value=today)

            if t_type == "Entrée":
                t_cat = c2.selectbox("Catégorie", options=categories)
                t_label = st.text_input("Détails supplémentaires (Optionnel)")
            else:
                # Si c'est une sortie, la catégorie disparaît et est remplacée par le libellé
                t_cat = "Dépense / Sortie"
                t_label = c2.text_input("Libellé de l'opération (Obligatoire)")

            st.divider()
            use_billetage = st.toggle("🔢 Utiliser le comptage des billets (Billetage)", value=False)
            
            total_usd, total_cdf = 0.0, 0.0
            billetage_data = None

            # --- 3. BILLETAGE AVEC CALCUL DYNAMIQUE PAR LIGNE ---
            if use_billetage:
                # Initialisation des tableaux virtuels dans la session
                if "df_usd" not in st.session_state:
                    st.session_state.df_usd = pd.DataFrame({"Billet": [100, 50, 20, 10, 5, 1], "Nombre": [0]*6, "Total (=)": [0]*6})
                if "df_cdf" not in st.session_state:
                    st.session_state.df_cdf = pd.DataFrame({"Billet": [20000, 10000, 5000, 1000, 500, 200, 100, 50], "Nombre": [0]*8, "Total (=)": [0]*8})

                col_u, col_c = st.columns(2)
                
                with col_u:
                    st.write("**🇺🇸 Billets USD ($)**")
                    edited_usd = st.data_editor(
                        st.session_state.df_usd, 
                        disabled=["Billet", "Total (=)"], # On bloque la modif du billet et du total
                        hide_index=True, 
                        use_container_width=True, 
                        key="usd_ed"
                    )
                    # Calcul du total par ligne
                    edited_usd["Total (=)"] = edited_usd["Billet"] * edited_usd["Nombre"]
                    
                    # Mise à jour en temps réel si modification
                    if not edited_usd.equals(st.session_state.df_usd):
                        st.session_state.df_usd = edited_usd
                        st.rerun()
                        
                    # Total global USD
                    total_usd = float(edited_usd["Total (=)"].sum())
                    st.metric("Total Global USD", f"{total_usd:,.2f} $")

                with col_c:
                    st.write("**🇨🇩 Billets CDF (Fc)**")
                    edited_cdf = st.data_editor(
                        st.session_state.df_cdf, 
                        disabled=["Billet", "Total (=)"], 
                        hide_index=True, 
                        use_container_width=True, 
                        key="cdf_ed"
                    )
                    # Calcul du total par ligne
                    edited_cdf["Total (=)"] = edited_cdf["Billet"] * edited_cdf["Nombre"]
                    
                    # Mise à jour en temps réel si modification
                    if not edited_cdf.equals(st.session_state.df_cdf):
                        st.session_state.df_cdf = edited_cdf
                        st.rerun()
                        
                    # Total global CDF
                    total_cdf = float(edited_cdf["Total (=)"].sum())
                    st.metric("Total Global CDF", f"{total_cdf:,.2f} Fc")
                
                billetage_data = {"usd": edited_usd.to_dict('records'), "cdf": edited_cdf.to_dict('records')}
            
            else:
                # Saisie manuelle classique
                m1, m2 = st.columns(2)
                total_usd = m1.number_input("Montant USD ($)", min_value=0.0)
                total_cdf = m2.number_input("Montant CDF (Fc)", min_value=0.0)

            # --- AJOUT À LA LISTE ---
            if st.button("➕ Ajouter à la liste du jour", use_container_width=True):
                if t_type == "Sortie" and not t_label:
                    st.error("Le libellé est obligatoire pour justifier une sortie.")
                else:
                    st.session_state.daily_ops.append({
                        "Date": t_date.strftime("%Y-%m-%d"), 
                        "Type": t_type, 
                        "Catégorie": t_cat if t_type == "Entrée" else "N/A",
                        "Libellé": t_label, 
                        "USD": total_usd, 
                        "CDF": total_cdf, 
                        "Taux": new_rate,
                        "Billetage": json.dumps(billetage_data) if billetage_data else None
                    })
                    # On réinitialise les tableaux de billetage après ajout
                    if "df_usd" in st.session_state: del st.session_state.df_usd
                    if "df_cdf" in st.session_state: del st.session_state.df_cdf
                    st.rerun()

        # --- LISTE TEMPORAIRE AVANT ENREGISTREMENT ---
        if st.session_state.daily_ops:
            st.subheader("📋 Opérations en attente de validation")
            st.table(pd.DataFrame(st.session_state.daily_ops)[["Type", "Catégorie", "Libellé", "USD", "CDF"]])
            
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("🗑️ Vider la liste"):
                st.session_state.daily_ops = []
                st.rerun()

            if c_btn2.button("💾 Enregistrer tout en base de données", type="primary"):
                for op in st.session_state.daily_ops:
                    conn.execute("""
                        INSERT INTO finances (date_trans, type, category, label, total_usd, total_cdf, rate, billetage_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (op["Date"], op["Type"], op["Catégorie"], op["Libellé"], op["USD"], op["CDF"], op["Taux"], op["Billetage"]))
                conn.commit()
                st.session_state.daily_ops = []
                st.success("Toutes les opérations ont été validées avec succès !")
                st.rerun()

    with tab2:
        st.subheader("Historique des transactions validées")
        hist_df = pd.read_sql("SELECT date_trans as Date, type as Type, category as Catégorie, label as Libellé, total_usd as USD, total_cdf as CDF FROM finances ORDER BY id DESC", conn)
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
