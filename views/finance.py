import streamlit as st
import pandas as pd
from datetime import date
import json
from models.database import get_connection, add_log

def show_finance():
    st.title("💰 Trésorerie & Opérations du jour")
    conn = get_connection()
    today = date.today()

    # --- INITIALISATION DU BROUILLON ---
    if 'temp_transactions' not in st.session_state:
        st.session_state.temp_transactions = []

    # --- SIDEBAR : TAUX DE CHANGE ---
    st.sidebar.subheader("💱 Taux de change")
    rate_db = conn.execute("SELECT rate FROM exchange_rates WHERE date_rate = ?", (today,)).fetchone()
    current_rate = rate_db[0] if rate_db else 2800.0
    new_rate = st.sidebar.number_input("1 $ USD = ? CDF", value=float(current_rate), step=50.0)
    
    if st.sidebar.button("💾 Fixer le taux"):
        conn.execute("INSERT OR REPLACE INTO exchange_rates (date_rate, rate) VALUES (?, ?)", (today, new_rate))
        conn.commit()
        st.sidebar.success("Taux enregistré !")

    tab1, tab2 = st.tabs(["📝 Saisie des opérations", "📜 Historique Global"])

    # --- ONGLET 1 : SAISIE ET LISTE DU JOUR ---
    with tab1:
        col_form, col_list = st.columns([1, 1.2])

        with col_form:
            st.subheader("➕ Ajouter une ligne")
            with st.container(border=True):
                trans_type = st.selectbox("Type", ["Entrée", "Sortie"])
                trans_label = st.text_input("Libellé / Motif")
                
                c1, c2 = st.columns(2)
                t_usd = c1.number_input("Montant USD ($)", min_value=0.0, step=1.0)
                t_cdf = c2.number_input("Montant CDF (Fc)", min_value=0, step=500)

                # --- BILLETAGE OPTIONNEL ---
                activate_billetage = st.checkbox("Effectuer le billetage ?")
                billetage_data = None
                
                if activate_billetage:
                    st.info("Saisie du billetage")
                    # On affiche les éditeurs de données mais simplifiés
                    b_usd = st.data_editor(pd.DataFrame({"Billet": [100, 50, 20, 10, 5, 1], "Nbr": [0]*6}), hide_index=True)
                    b_cdf = st.data_editor(pd.DataFrame({"Billet": [20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50], "Nbr": [0]*9}), hide_index=True)
                    
                    # Recalcul des montants basés sur le billetage pour éviter les erreurs
                    t_usd = (b_usd["Billet"] * b_usd["Nbr"]).sum()
                    t_cdf = (b_cdf["Billet"] * b_cdf["Nbr"]).sum()
                    st.write(f"Total calculé : {t_usd}$ / {t_cdf}Fc")
                    
                    billetage_data = {"usd": b_usd.to_dict('records'), "cdf": b_cdf.to_dict('records')}

                if st.button("➕ Ajouter à la liste"):
                    if trans_label:
                        new_op = {
                            "date": today,
                            "type": trans_type,
                            "label": trans_label,
                            "usd": float(t_usd),
                            "cdf": float(t_cdf),
                            "rate": new_rate,
                            "billetage": json.dumps(billetage_data) if billetage_data else None
                        }
                        st.session_state.temp_transactions.append(new_op)
                        st.toast("Opération ajoutée au brouillon")
                    else:
                        st.error("Le libellé est requis")

        with col_list:
            st.subheader("📋 Opérations en attente")
            if st.session_state.temp_transactions:
                df_temp = pd.DataFrame(st.session_state.temp_transactions)
                st.dataframe(df_temp[['type', 'label', 'usd', 'cdf']], use_container_width=True)
                
                total_day_usd = df_temp[df_temp['type'] == 'Entrée']['usd'].sum() - df_temp[df_temp['type'] == 'Sortie']['usd'].sum()
                total_day_cdf = df_temp[df_temp['type'] == 'Entrée']['cdf'].sum() - df_temp[df_temp['type'] == 'Sortie']['cdf'].sum()
                
                st.metric("Solde des opérations saisies", f"{total_day_usd}$ / {total_day_cdf}Fc")

                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.button("🗑️ Tout effacer", type="secondary"):
                    st.session_state.temp_transactions = []
                    st.rerun()

                if col_btn2.button("💾 Enregistrer tout en base", type="primary"):
                    for op in st.session_state.temp_transactions:
                        conn.execute("""
                            INSERT INTO finances (date_trans, type, label, total_usd, total_cdf, rate, billetage_json)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (op['date'], op['type'], op['label'], op['usd'], op['cdf'], op['rate'], op['billetage']))
                    
                    conn.commit()
                    add_log(st.session_state.username, f"Validation lot de {len(st.session_state.temp_transactions)} opérations", st.session_state.role)
                    st.session_state.temp_transactions = []
                    st.success("Toutes les opérations ont été enregistrées !")
                    st.rerun()
            else:
                st.info("Aucune opération en attente. Utilisez le formulaire à gauche.")

    # --- ONGLET 2 : HISTORIQUE GLOBAL ---
    with tab2:
        st.subheader("Archives des transactions")
        df_hist = pd.read_sql("SELECT date_trans, type, label, total_usd, total_cdf, rate FROM finances ORDER BY id DESC", conn)
        st.dataframe(df_hist, use_container_width=True)
