import streamlit as st
import pandas as pd
from datetime import date
import json
from models.database import get_connection, add_log

def show_finance():
    st.title("💰 Trésorerie & Billetage")
    conn = get_connection()
    today = date.today()

    if 'daily_ops' not in st.session_state:
        st.session_state.daily_ops = []

    # --- SIDEBAR : TAUX ET CATÉGORIES ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        rate_db = conn.execute("SELECT rate FROM exchange_rates WHERE date_rate = ?", (today,)).fetchone()
        current_rate = rate_db[0] if rate_db else 2800.0
        new_rate = st.number_input("Taux (1$ = ? Fc)", value=float(current_rate), step=50.0)
        
        st.divider()
        st.subheader("📁 Gérer les Catégories")
        new_cat = st.text_input("Ajouter une catégorie")
        if st.button("➕ Ajouter"):
            if new_cat:
                conn.execute("INSERT OR IGNORE INTO finance_categories (name) VALUES (?)", (new_cat,))
                conn.commit()
                st.rerun()

    # Récupérer les catégories
    categories = pd.read_sql("SELECT name FROM finance_categories", conn)['name'].tolist()

    tab1, tab2 = st.tabs(["📝 Saisie", "📊 Historique"])

    with tab1:
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            t_type = c1.selectbox("Flux", ["Entrée", "Sortie"])
            t_cat = c2.selectbox("Catégorie", options=categories)
            t_date = c3.date_input("Date", value=today)
            t_label = st.text_input("Libellé de l'opération")

            use_billetage = st.toggle("🔢 Utiliser le comptage des billets (Billetage)", value=False)
            
            total_usd, total_cdf = 0.0, 0.0
            billetage_data = None

            if use_billetage:
                col_u, col_c = st.columns(2)
                with col_u:
                    st.write("**Billets USD ($)**")
                    df_u = pd.DataFrame({"Billet": [100, 50, 20, 10, 5, 1], "Nombre": [0]*6})
                    edit_u = st.data_editor(df_u, hide_index=True, key="usd_ed", use_container_width=True)
                    total_usd = float((edit_u["Billet"] * edit_u["Nombre"]).sum())
                    # AFFICHAGE DU MONTANT TOTAL USD
                    st.metric("Total USD", f"{total_usd:,.2f} $")

                with col_c:
                    st.write("**Billets CDF (Fc)**")
                    df_c = pd.DataFrame({"Billet": [20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50], "Nombre": [0]*9})
                    edit_c = st.data_editor(df_c, hide_index=True, key="cdf_ed", use_container_width=True)
                    total_cdf = float((edit_c["Billet"] * edit_c["Nombre"]).sum())
                    # AFFICHAGE DU MONTANT TOTAL CDF
                    st.metric("Total CDF", f"{total_cdf:,.2f} Fc")
                
                billetage_data = {"usd": edit_u.to_dict('records'), "cdf": edit_c.to_dict('records')}
            else:
                m1, m2 = st.columns(2)
                total_usd = m1.number_input("Montant USD ($)", min_value=0.0)
                total_cdf = m2.number_input("Montant CDF (Fc)", min_value=0.0)

            if st.button("➕ Ajouter à la liste du jour", use_container_width=True):
                if t_label:
                    st.session_state.daily_ops.append({
                        "Date": t_date.strftime("%Y-%m-%d"), "Type": t_type, "Catégorie": t_cat,
                        "Libellé": t_label, "USD": total_usd, "CDF": total_cdf, "Taux": new_rate,
                        "Billetage": json.dumps(billetage_data) if billetage_data else None
                    })
                    st.rerun()

        # --- LISTE TEMPORAIRE ---
        if st.session_state.daily_ops:
            st.subheader("📋 Opérations en attente de validation")
            st.table(pd.DataFrame(st.session_state.daily_ops)[["Type", "Catégorie", "Libellé", "USD", "CDF"]])
            
            if st.button("💾 Enregistrer tout en base de données", type="primary"):
                for op in st.session_state.daily_ops:
                    conn.execute("""
                        INSERT INTO finances (date_trans, type, category, label, total_usd, total_cdf, rate, billetage_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (op["Date"], op["Type"], op["Catégorie"], op["Libellé"], op["USD"], op["CDF"], op["Taux"], op["Billetage"]))
                conn.commit()
                st.session_state.daily_ops = []
                st.success("Opérations enregistrées !")
                st.rerun()
