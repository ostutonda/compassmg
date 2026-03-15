import streamlit as st
import pandas as pd
from datetime import date
import json
from models.database import get_connection, add_log

def show_finance():
    st.title("💰 Trésorerie & Catégories")
    conn = get_connection()
    today = date.today()

    if 'daily_ops' not in st.session_state:
        st.session_state.daily_ops = []

    # --- 1. GESTION DES CATÉGORIES (CRUD) DANS LE SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Paramètres")
        
        # Gestion du Taux
        rate_db = conn.execute("SELECT rate FROM exchange_rates WHERE date_rate = ?", (today,)).fetchone()
        current_rate = rate_db[0] if rate_db else 2800.0
        new_rate = st.number_input("Taux (1$ = ? Fc)", value=float(current_rate), step=50.0)
        if st.button("Enregistrer le Taux"):
            conn.execute("INSERT OR REPLACE INTO exchange_rates (date_rate, rate) VALUES (?, ?)", (today, new_rate))
            conn.commit()
            st.success("Taux mis à jour !")

        st.divider()
        
        # CRUD Catégories
        st.subheader("📁 Catégories")
        with st.expander("Gérer les catégories"):
            new_cat = st.text_input("Nouvelle catégorie")
            if st.button("Ajouter"):
                if new_cat:
                    conn.execute("INSERT OR IGNORE INTO finance_categories (name) VALUES (?)", (new_cat,))
                    conn.commit()
                    st.rerun()
            
            cats_df = pd.read_sql("SELECT * FROM finance_categories", conn)
            for idx, row in cats_df.iterrows():
                col_c1, col_c2 = st.columns([3, 1])
                col_c1.write(row['name'])
                if col_c2.button("🗑️", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM finance_categories WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.rerun()

    # Récupération des catégories pour le formulaire
    categories = pd.read_sql("SELECT name FROM finance_categories", conn)['name'].tolist()

    tab1, tab2 = st.tabs(["📝 Saisie des opérations", "📊 Historique & Rapports"])

    with tab1:
        st.subheader("Nouvelle ligne d'opération")
        
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 1, 1])
            t_type = col1.selectbox("Flux", ["Entrée", "Sortie"])
            t_cat = col2.selectbox("Catégorie", options=categories) # <-- Liste déroulante des catégories
            t_date = col3.date_input("Date", value=today)
            
            t_label = st.text_input("Libellé / Détails de l'opération")

            use_billetage = st.toggle("Activer le billetage (comptage des billets)", value=False)
            
            total_usd = 0.0
            total_cdf = 0.0
            billetage_data = None

            if use_billetage:
                st.markdown("---")
                c_usd, c_cdf = st.columns(2)
                
                with c_usd:
                    st.subheader("🇺🇸 Billetage USD")
                    df_u = pd.DataFrame({"Billet": [100, 50, 20, 10, 5, 1], "Nombre": [0]*6})
                    edit_u = st.data_editor(df_u, hide_index=True, key="usd_ed", use_container_width=True)
                    total_usd = float((edit_u["Billet"] * edit_u["Nombre"]).sum())
                    # AFFICHAGE DU TOTAL USD
                    st.metric("Total USD ($)", f"{total_usd:,.2f} $")

                with c_cdf:
                    st.subheader("🇨🇩 Billetage CDF")
                    df_c = pd.DataFrame({"Billet": [20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50], "Nombre": [0]*9})
                    edit_c = st.data_editor(df_c, hide_index=True, key="cdf_ed", use_container_width=True)
                    total_cdf = float((edit_c["Billet"] * edit_c["Nombre"]).sum())
                    # AFFICHAGE DU TOTAL CDF
                    st.metric("Total CDF (Fc)", f"{total_cdf:,.2f} Fc")
                
                billetage_data = {"usd": edit_u.to_dict('records'), "cdf": edit_c.to_dict('records')}
                st.markdown("---")
            
            else:
                m_usd, m_cdf = st.columns(2)
                total_usd = m_usd.number_input("Montant total en USD ($)", min_value=0.0, format="%.2f")
                total_cdf = m_cdf.number_input("Montant total en CDF (Fc)", min_value=0.0, format="%.2f")

            if st.button("➕ Ajouter à la liste du jour", use_container_width=True, type="secondary"):
                if t_label:
                    st.session_state.daily_ops.append({
                        "Date": t_date.strftime("%Y-%m-%d"),
                        "Type": t_type,
                        "Catégorie": t_cat,
                        "Libellé": t_label,
                        "USD": total_usd,
                        "CDF": total_cdf,
                        "Taux": new_rate,
                        "Billetage": json.dumps(billetage_data) if billetage_data else None
                    })
                else:
                    st.error("Le libellé est obligatoire.")

        # --- AFFICHAGE DE LA LISTE TEMPORAIRE ---
        if st.session_state.daily_ops:
            st.divider()
            st.subheader("📋 Opérations prêtes à être validées")
            temp_df = pd.DataFrame(st.session_state.daily_ops)
            st.dataframe(temp_df[["Date", "Type", "Catégorie", "Libellé", "USD", "CDF"]], use_container_width=True)

            c_b1, c_b2 = st.columns(2)
            if c_b1.button("🗑️ Annuler tout"):
                st.session_state.daily_ops = []
                st.rerun()

            if c_b2.button("💾 Enregistrer les opérations définitivement", type="primary"):
                for op in st.session_state.daily_ops:
                    # Note : il faudra ajouter la colonne 'category' à votre table finances si ce n'est pas fait
                    conn.execute("""
                        INSERT INTO finances (date_trans, type, label, total_usd, total_cdf, rate, billetage_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (op["Date"], f"{op['Type']} ({op['Catégorie']})", op["Libellé"], op["USD"], op["CDF"], op["Taux"], op["Billetage"]))
                
                conn.commit()
                st.session_state.daily_ops = []
                st.success("Transactions enregistrées !")
                st.rerun()

    with tab2:
        st.subheader("Historique des transactions validées")
        hist_df = pd.read_sql("SELECT date_trans as Date, type as Type, label as Libellé, total_usd as USD, total_cdf as CDF FROM finances ORDER BY id DESC", conn)
        st.dataframe(hist_df, use_container_width=True)
