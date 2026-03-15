import streamlit as st
import pandas as pd
from datetime import date
import json
from models.database import get_connection, add_log

def show_finance():
    st.title("💰 Trésorerie & Opérations")
    conn = get_connection()
    today = date.today()

    # --- 1. INITIALISATION DE LA LISTE TEMPORAIRE ---
    if 'daily_ops' not in st.session_state:
        st.session_state.daily_ops = []

    # --- 2. GESTION DU TAUX ---
    rate_db = conn.execute("SELECT rate FROM exchange_rates WHERE date_rate = ?", (today,)).fetchone()
    current_rate = rate_db[0] if rate_db else 2800.0
    
    with st.sidebar:
        st.subheader("💱 Configuration")
        new_rate = st.number_input("Taux (1$ = ? Fc)", value=float(current_rate), step=50.0)
        if st.button("Enregistrer le Taux"):
            conn.execute("INSERT OR REPLACE INTO exchange_rates (date_rate, rate) VALUES (?, ?)", (today, new_rate))
            conn.commit()
            st.success("Taux mis à jour !")

    tab1, tab2 = st.tabs(["📝 Saisie des opérations", "📊 Historique & Rapports"])

    with tab1:
        # --- FORMULAIRE DE SAISIE ---
        st.subheader("Nouvelle ligne d'opération")
        
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 1, 2])
            t_type = col1.selectbox("Flux", ["Entrée", "Sortie"])
            t_date = col2.date_input("Date", value=today)
            t_label = col3.text_input("Libellé / Motif")

            # --- OPTION BILLETAGE ---
            use_billetage = st.toggle("Activer le comptage des billets (Billetage)", value=False)
            
            total_usd = 0.0
            total_cdf = 0.0
            billetage_data = None

            if use_billetage:
                st.info("💡 Saisissez uniquement le **nombre** de billets.")
                c_usd, c_cdf = st.columns(2)
                
                with c_usd:
                    st.write("**Billets USD ($)**")
                    df_u = pd.DataFrame({"Billet": [100, 50, 20, 10, 5, 1], "Nombre": [0]*6})
                    edit_u = st.data_editor(df_u, hide_index=True, key="usd_ed")
                    total_usd = float((edit_u["Billet"] * edit_u["Nombre"]).sum())
                    st.caption(f"Sous-total : {total_usd}$")

                with c_cdf:
                    st.write("**Billets CDF (Fc)**")
                    df_c = pd.DataFrame({"Billet": [20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50], "Nombre": [0]*9})
                    edit_c = st.data_editor(df_c, hide_index=True, key="cdf_ed")
                    total_cdf = float((edit_c["Billet"] * edit_c["Nombre"]).sum())
                    st.caption(f"Sous-total : {total_cdf} Fc")
                
                billetage_data = {"usd": edit_u.to_dict('records'), "cdf": edit_c.to_dict('records')}
            
            else:
                # --- SAISIE MANUELLE ---
                st.write("✍️ **Saisie directe des montants**")
                m_usd, m_cdf = st.columns(2)
                total_usd = m_usd.number_input("Montant total en USD ($)", min_value=0.0, format="%.2f")
                total_cdf = m_cdf.number_input("Montant total en CDF (Fc)", min_value=0.0, format="%.2f")

            if st.button("➕ Ajouter à la liste du jour", use_container_width=True):
                if t_label:
                    new_op = {
                        "Date": t_date.strftime("%Y-%m-%d"),
                        "Type": t_type,
                        "Libellé": t_label,
                        "USD": total_usd,
                        "CDF": total_cdf,
                        "Taux": new_rate,
                        "Billetage": json.dumps(billetage_data) if billetage_data else None
                    }
                    st.session_state.daily_ops.append(new_op)
                    st.toast("Opération ajoutée à la liste !")
                else:
                    st.error("Veuillez saisir un libellé.")

        # --- AFFICHAGE DE LA LISTE TEMPORAIRE ---
        if st.session_state.daily_ops:
            st.divider()
            st.subheader("📋 Opérations prêtes à être enregistrées")
            temp_df = pd.DataFrame(st.session_state.daily_ops)
            st.table(temp_df[["Date", "Type", "Libellé", "USD", "CDF"]])

            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("🗑️ Vider la liste", type="secondary"):
                st.session_state.daily_ops = []
                st.rerun()

            if col_btn2.button("💾 Enregistrer tout définitivement", type="primary"):
                for op in st.session_state.daily_ops:
                    conn.execute("""
                        INSERT INTO finances (date_trans, type, label, total_usd, total_cdf, rate, billetage_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (op["Date"], op["Type"], op["Libellé"], op["USD"], op["CDF"], op["Taux"], op["Billetage"]))
                
                conn.commit()
                add_log(st.session_state.username, f"Enregistrement de {len(st.session_state.daily_ops)} opérations", st.session_state.role)
                st.session_state.daily_ops = []
                st.success("Toutes les opérations ont été sauvegardées en base de données !")
                st.rerun()

    with tab2:
        # --- HISTORIQUE CLASSIQUE ---
        st.subheader("Historique des transactions validées")
        hist_df = pd.read_sql("SELECT date_trans as Date, type as Type, label as Libellé, total_usd as USD, total_cdf as CDF FROM finances ORDER BY id DESC", conn)
        st.dataframe(hist_df, use_container_width=True)
