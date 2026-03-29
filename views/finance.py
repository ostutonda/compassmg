#finance.py
import streamlit as st
import pandas as pd
import uuid
import json
from datetime import date
from models.database import get_connection

def show_finance():
    st.title("💰 Gestion des Finances")
    conn = get_connection()
    today = date.today()

    # --- 0. MIGRATION & SÉCURITÉ BASE DE DONNÉES ---
    try:
        conn.execute("ALTER TABLE finances ADD COLUMN billetage_cdf TEXT DEFAULT '{}'")
        conn.execute("ALTER TABLE finances ADD COLUMN billetage_usd TEXT DEFAULT '{}'")
        conn.commit()
    except:
        pass

    # --- 1. FONCTIONS ET INITIALISATION ---
    def format_fr(amount):
        return f"{amount:,.2f}".replace(",", " ").replace(".", ",").replace(" ", " ")

    def reset_inputs():
        st.session_state.main_label = ""
        st.session_state.man_usd = 0.0
        st.session_state.man_cdf = 0.0
        # Reset des dataframes de billetage
        st.session_state.df_cdf["Nombre"] = 0
        st.session_state.df_cdf["Total (=)"] = 0
        st.session_state.df_usd["Nombre"] = 0
        st.session_state.df_usd["Total (=)"] = 0

    if "daily_ops" not in st.session_state:
        st.session_state.daily_ops = []

    if "df_cdf" not in st.session_state:
        st.session_state.df_cdf = pd.DataFrame({
            "Coupure": [20000, 10000, 5000, 1000, 500, 200, 100, 50],
            "Nombre": [0] * 8, "Total (=)": [0] * 8
        })

    if "df_usd" not in st.session_state:
        st.session_state.df_usd = pd.DataFrame({
            "Coupure": [100, 50, 20, 10, 5, 1],
            "Nombre": [0] * 6, "Total (=)": [0] * 6
        })

    tab1, tab2, tab3 = st.tabs(["📝 Saisie", "📊 Rapports & Historique", "⚙️ Configuration"])

    # --- TAB 1 : SAISIE DES OPÉRATIONS ---
    with tab1:
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            t_type = c1.selectbox("Flux", ["Entrée", "Sortie"], key="main_type")
            
            try:
                cats_df = pd.read_sql("SELECT name FROM finance_categories", conn)
                cat_options = cats_df['name'].tolist() if not cats_df.empty else ["Général"]
            except:
                cat_options = ["Général"]
            
            t_cat = c2.selectbox("Catégorie", options=cat_options, key="main_cat")
            t_date = c3.date_input("Date", value=today, key="main_date")
            t_label = st.text_input("Libellé / Justification", key="main_label")

            t_montant1, t_montant2 = st.tabs(["💵 Billetage", "⌨️ Manuel"])
            
            with t_montant1:
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    st.caption("Francs Congolais (CDF)")
                    res_cdf = st.data_editor(st.session_state.df_cdf, hide_index=True, key="ed_cdf",
                                             column_config={"Coupure": st.column_config.NumberColumn(disabled=True),
                                                            "Total (=)": st.column_config.NumberColumn(disabled=True, format="%d FC")})
                    res_cdf["Total (=)"] = res_cdf["Coupure"] * res_cdf["Nombre"]
                    total_cdf_billet = res_cdf["Total (=)"].sum()
                    st.write(f"Total : **{format_fr(total_cdf_billet)} FC**")
                
                with col_b2:
                    st.caption("Dollars (USD)")
                    res_usd = st.data_editor(st.session_state.df_usd, hide_index=True, key="ed_usd",
                                             column_config={"Coupure": st.column_config.NumberColumn(disabled=True),
                                                            "Total (=)": st.column_config.NumberColumn(disabled=True, format="$ %d")})
                    res_usd["Total (=)"] = res_usd["Coupure"] * res_usd["Nombre"]
                    total_usd_billet = res_usd["Total (=)"].sum()
                    st.write(f"Total : **{format_fr(total_usd_billet)} $**")

            with t_montant2:
                m_usd = st.number_input("Montant USD", min_value=0.0, key="man_usd")
                m_cdf = st.number_input("Montant CDF", min_value=0.0, key="man_cdf")

        if st.button("➕ Ajouter à la liste du jour", type="primary", use_container_width=True):
            f_usd = total_usd_billet if total_usd_billet > 0 else m_usd
            f_cdf = total_cdf_billet if total_cdf_billet > 0 else m_cdf

            if t_type == "Sortie" and not t_label:
                st.error("Le libellé est obligatoire pour une sortie.")
            elif f_usd == 0 and f_cdf == 0:
                st.warning("Veuillez saisir un montant.")
            else:
                b_cdf = res_cdf[res_cdf["Nombre"] > 0].set_index("Coupure")["Nombre"].to_dict()
                b_usd = res_usd[res_usd["Nombre"] > 0].set_index("Coupure")["Nombre"].to_dict()

                st.session_state.daily_ops.append({
                    "id": str(uuid.uuid4()), "date": t_date, "type": t_type, "category": t_cat,
                    "label": t_label, "usd": f_usd, "cdf": f_cdf,
                    "b_cdf": b_cdf, "b_usd": b_usd, "is_billet": (total_usd_billet > 0 or total_cdf_billet > 0)
                })
                reset_inputs()
                st.rerun()

        if st.session_state.daily_ops:
            st.subheader("📋 Opérations en attente")
            for i, op in enumerate(st.session_state.daily_ops):
                with st.container(border=True):
                    c_inf, c_ed, c_de = st.columns([5, 1, 1])
                    c_inf.write(f"**{op['type']}** | {op['category']} | {format_fr(op['usd'])}$ - {format_fr(op['cdf'])}Fc")
                    c_inf.caption(f"{op['label']} {'(Billetage)' if op['is_billet'] else ''}")
                    
                    if c_de.button("🗑️", key=f"del_{op['id']}"):
                        st.session_state.daily_ops.pop(i)
                        st.rerun()
                    if c_ed.button("✏️", key=f"edit_{op['id']}"):
                        data = st.session_state.daily_ops.pop(i)
                        st.session_state.main_type = data['type']
                        st.session_state.main_cat = data['category']
                        st.session_state.main_label = data['label']
                        if not data['is_billet']:
                            st.session_state.man_usd, st.session_state.man_cdf = data['usd'], data['cdf']
                        st.rerun()

            if st.button("💾 Enregistrer toutes les écritures", type="primary", use_container_width=True):
                for op in st.session_state.daily_ops:
                    conn.execute("INSERT INTO finances (date_trans, type, category, label, total_usd, total_cdf, billetage_cdf, billetage_usd) VALUES (?,?,?,?,?,?,?,?)",
                                 (op['date'], op['type'], op['category'], op['label'], op['usd'], op['cdf'], json.dumps(op['b_cdf']), json.dumps(op['b_usd'])))
                conn.commit()
                st.session_state.daily_ops = []
                st.success("Données enregistrées avec succès !")
                st.rerun()



        # --- TAB 2 : RAPPORTS & HISTORIQUE (Version Détaillée) ---

    with tab2:
        st.subheader("📊 Rapport Chronologique Détaillé")
        cs, ce = st.columns(2)
        d_s = cs.date_input("Du", today.replace(day=1), key="rep_start")
        d_e = ce.date_input("Au", today, key="rep_end")

        # Extraction des données
        df_r = pd.read_sql("SELECT * FROM finances WHERE date_trans BETWEEN ? AND ? ORDER BY date_trans DESC", 
                           conn, params=(d_s, d_e))
        
        if not df_r.empty:
            # On regroupe par Libellé (l'événement)
            for label in df_r['label'].unique():
                df_label = df_r[df_r['label'] == label]
                
                # Affichage du titre de l'événement
                st.markdown(f"### 📑 {label}")
                
                # Pour chaque opération sous ce libellé (souvent une ou plusieurs catégories)
                for idx, row in df_label.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{row['category']}** ({row['type']})")
                        
                        col_cdf, col_usd = st.columns(2)
                        
                        # --- DÉTAIL CDF ---
                        with col_cdf:
                            st.caption("Détail Francs Congolais")
                            try:
                                b_cdf = json.loads(row['billetage_cdf']) if row['billetage_cdf'] else {}
                                if b_cdf:
                                    for coupure, nombre in sorted(b_cdf.items(), key=lambda x: int(x[0]), reverse=True):
                                        total_ligne = int(coupure) * int(nombre)
                                        st.write(f" {format_fr(int(coupure))} fc x {nombre} = {format_fr(total_ligne)} fc")
                                else:
                                    st.write(f"Montant direct : {format_fr(row['total_cdf'])} fc")
                            except:
                                st.write(f"Montant : {format_fr(row['total_cdf'])} fc")
                        
                        # --- DÉTAIL USD ---
                        with col_usd:
                            st.caption("Détail Dollars")
                            try:
                                b_usd = json.loads(row['billetage_usd']) if row['billetage_usd'] else {}
                                if b_usd:
                                    for coupure, nombre in sorted(b_usd.items(), key=lambda x: int(x[0]), reverse=True):
                                        total_ligne = int(coupure) * int(nombre)
                                        st.write(f" {coupure} $ x {nombre} = {format_fr(total_ligne)} $")
                                else:
                                    st.write(f"Montant direct : {format_fr(row['total_usd'])} $")
                            except:
                                st.write(f"Montant : {format_fr(row['total_usd'])} $")
                        
                        # --- TOTAL DE LA CATÉGORIE ---
                        st.divider()
                        st.markdown(f"**Total {row['category']} :** `{format_fr(row['total_cdf'])} FC` et `{format_fr(row['total_usd'])} $`")
                
                st.write(" ") # Espace entre les événements
        else:
            st.info("Aucune donnée enregistrée pour cette période.")





    # --- TAB 3 : CONFIGURATION (CRUD) ---
    with tab3:
        st.header("⚙️ Paramètres")
        
        # CRUD TAUX
        st.subheader("💱 Taux de Change")
        with st.container(border=True):
            r_db = conn.execute("SELECT rate, date_rate FROM exchange_rates ORDER BY date_rate DESC LIMIT 1").fetchone()
            curr_r = r_db[0] if r_db else 2800.0
            c_r1, c_r2 = st.columns([2,1])
            n_r = c_r1.number_input(f"Taux (Actuel: {curr_r})", value=float(curr_r))
            if c_r2.button("💾 Maj Taux", use_container_width=True):
                conn.execute("INSERT OR REPLACE INTO exchange_rates (date_rate, rate) VALUES (?,?)", (today, n_r))
                conn.commit()
                st.rerun()

        # CRUD CATÉGORIES
        st.divider()
        st.subheader("📁 Catégories")
        with st.form("add_cat", clear_on_submit=True):
            n_c = st.text_input("Nom nouvelle catégorie")
            if st.form_submit_button("➕ Ajouter"):
                if n_c:
                    conn.execute("INSERT OR IGNORE INTO finance_categories (name) VALUES (?)", (n_c.strip(),))
                    conn.commit()
                    st.rerun()

        cats = pd.read_sql("SELECT * FROM finance_categories ORDER BY name", conn)
        for _, r in cats.iterrows():
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{r['name']}**")
            usage = conn.execute("SELECT COUNT(*) FROM finances WHERE category = ?", (r['name'],)).fetchone()[0]
            if col2.button("🗑️", key=f"dc_{r['id']}", disabled=usage > 0, help="Suppression impossible si utilisée"):
                conn.execute("DELETE FROM finance_categories WHERE id = ?", (r['id'],))
                conn.commit()
                st.rerun()
