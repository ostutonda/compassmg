import streamlit as st
import pandas as pd
from datetime import date
import json
from models.database import get_connection, add_log

def show_finance():
    st.title("💰 Trésorerie & Billetage")
    conn = get_connection()
    today = date.today()

    # --- 1. GESTION DU TAUX DE CHANGE ---
    st.sidebar.subheader("💱 Taux de change du jour")
    
    # Récupérer le taux du jour s'il existe
    rate_db = conn.execute("SELECT rate FROM exchange_rates WHERE date_rate = ?", (today,)).fetchone()
    current_rate = rate_db[0] if rate_db else 2800.0  # Valeur par défaut si non défini

    new_rate = st.sidebar.number_input("1 $ USD = ? CDF", value=float(current_rate), step=50.0)
    
    if st.sidebar.button("💾 Enregistrer le taux"):
        conn.execute("INSERT OR REPLACE INTO exchange_rates (date_rate, rate) VALUES (?, ?)", (today, new_rate))
        conn.commit()
        add_log(st.session_state.username, f"Mise à jour taux: 1$ = {new_rate} CDF", st.session_state.role)
        st.sidebar.success("Taux mis à jour !")
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["💵 Saisie d'Opération (Billetage)", "📊 Historique", "📈 Rapport Global"])

    # --- ONGLET 1 : SAISIE AVEC BILLETAGE ---
    with tab1:
        st.subheader("Nouvelle transaction")
        
        col_date, col_type, col_lib = st.columns([1, 1, 2])
        trans_date = col_date.date_input("Date de l'opération", value=today)
        trans_type = col_type.selectbox("Type", ["Entrée", "Sortie"])
        trans_label = col_lib.text_input("Libellé (ex: Offrandes du culte, Achat chaises)")

        st.markdown("### 🧮 Billetage")
        col_usd, col_cdf = st.columns(2)

        # -- TABLEAU USD --
        with col_usd:
            st.write("🇺🇸 **Caisse USD ($)**")
            df_usd = pd.DataFrame({"Billet": [100, 50, 20, 10, 5, 1], "Nombre": [0, 0, 0, 0, 0, 0]})
            edited_usd = st.data_editor(df_usd, hide_index=True, use_container_width=True)
            total_usd = (edited_usd["Billet"] * edited_usd["Nombre"]).sum()
            st.success(f"**Total USD : {total_usd:,.2f} $**")

        # -- TABLEAU CDF --
        with col_cdf:
            st.write("🇨🇩 **Caisse CDF (Francs)**")
            df_cdf = pd.DataFrame({"Billet": [20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50], "Nombre": [0, 0, 0, 0, 0, 0, 0, 0, 0]})
            edited_cdf = st.data_editor(df_cdf, hide_index=True, use_container_width=True)
            total_cdf = (edited_cdf["Billet"] * edited_cdf["Nombre"]).sum()
            st.info(f"**Total CDF : {total_cdf:,.2f} Fc**")

        st.divider()
        
        # Résultat de l'opération
        grand_total_cdf = total_cdf + (total_usd * new_rate)
        st.markdown(f"#### 🏷️ Valeur totale de l'opération : **{grand_total_cdf:,.2f} CDF** *(Taux: {new_rate})*")

        if st.button("✅ Valider l'opération", type="primary"):
            if trans_label:
                # Sauvegarde du billetage en format texte (JSON) pour archive
                billetage_data = {
                    "usd": edited_usd.to_dict('records'),
                    "cdf": edited_cdf.to_dict('records')
                }
                
                conn.execute("""
                    INSERT INTO finances (date_trans, type, label, total_usd, total_cdf, rate, billetage_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (trans_date, trans_type, trans_label, float(total_usd), float(total_cdf), new_rate, json.dumps(billetage_data)))
                conn.commit()
                add_log(st.session_state.username, f"Finance {trans_type}: {trans_label}", st.session_state.role)
                st.success("Opération enregistrée avec succès !")
                st.rerun()
            else:
                st.error("Le libellé de l'opération est obligatoire.")

    # --- ONGLET 2 : HISTORIQUE ---
    with tab2:
        st.subheader("Historique des transactions")
        df_fin = pd.read_sql("SELECT id, date_trans as Date, type as Type, label as Libellé, total_usd as 'Total ($)', total_cdf as 'Total (Fc)', rate as Taux FROM finances ORDER BY date_trans DESC, id DESC", conn)
        
        if not df_fin.empty:
            # Coloration conditionnelle basique
            def color_type(val):
                color = '#e6ffe6' if val == 'Entrée' else '#ffe6e6'
                return f'background-color: {color}'
            
            st.dataframe(df_fin.style.map(color_type, subset=['Type']), use_container_width=True)
        else:
            st.info("Aucune transaction enregistrée.")

    # --- ONGLET 3 : RAPPORTS (À DÉVELOPPER) ---
    with tab3:
        st.subheader("Synthèse des Caisses")
        if not df_fin.empty:
            entrees_usd = df_fin[df_fin['Type'] == 'Entrée']['Total ($)'].sum()
            sorties_usd = df_fin[df_fin['Type'] == 'Sortie']['Total ($)'].sum()
            solde_usd = entrees_usd - sorties_usd
            
            entrees_cdf = df_fin[df_fin['Type'] == 'Entrée']['Total (Fc)'].sum()
            sorties_cdf = df_fin[df_fin['Type'] == 'Sortie']['Total (Fc)'].sum()
            solde_cdf = entrees_cdf - sorties_cdf
            
            col1, col2 = st.columns(2)
            col1.metric("Solde Caisse USD", f"{solde_usd:,.2f} $", f"+{entrees_usd} / -{sorties_usd}")
            col2.metric("Solde Caisse CDF", f"{solde_cdf:,.2f} Fc", f"+{entrees_cdf} / -{sorties_cdf}")
        else:
            st.write("En attente de données...")
