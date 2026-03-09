# main.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import time
import json
import ssl
import websocket
import sys
import os
from datetime import date, datetime, timedelta
from src.ml_logic import MODEL_PATH, SCALER_PATH, extract_candlestick_features, WINDOW_SIZE
import os, joblib
from tensorflow.keras.models import load_model
import numpy as np
import csv

# Ajout du chemin pour les modules locaux
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from config import ASSETS, TIMEFRAMES, APP_ID, WS_URL
from src.data_fetcher import DataFetcher
from src.indicators import add_indicators
# On importe uniquement ce qui existe dans le nouveau ml_logic.py
from src.ml_logic import predict_live, train_gru_model



def save_trade_history(symbol, contract_type, stake, conf, count):
    """Enregistre le trade dans un fichier CSV"""
    file_path = "trade_history.csv"
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Création de l'en-tête si le fichier est nouveau
        if not file_exists:
            writer.writerow(["Date_Heure", "Actif", "Direction", "Mise_Totale", "Confiance", "Nb_Positions"])
        
        # Ajout de la ligne du trade
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_stake = stake * count
        writer.writerow([now, symbol, contract_type, total_stake, f"{conf}%", count])
        
        



def execute_multiple_trades(ws, symbol, event_class, stake=5.0, count=5):
    """
    Ouvre plusieurs positions en simultané en fonction de la classe prédite.
    Classes haussières (1, 3) -> CALL
    Classes baissières (2, 4) -> PUT
    """
    # 1. Déterminer la direction
    if event_class in [1, 3]:
        contract_type = "CALL"
    elif event_class in [2, 4]:
        contract_type = "PUT"
    else:
        return # Si c'est Neutre (0) ou inconnu, on ne fait rien
    
    st.toast(f"🤖 Envoi de {count} ordres {contract_type} sur {symbol}...", icon="🚀")
    
    # 2. Boucle pour ouvrir les N positions
    for i in range(count):
        trade_request = {
            "buy": 1,
            "price": stake, # Le prix que tu es prêt à payer max
            "parameters": {
                "amount": stake,
                "basis": "stake",
                "contract_type": contract_type,
                "currency": "USD",
                "duration": 5,        # Durée du trade (ex: 5)
                "duration_unit": "t", # 't' pour ticks, 'm' pour minutes
                "symbol": symbol
            }
        }
        ws.send(json.dumps(trade_request))
        # Petite pause vitale pour ne pas se faire bloquer par l'anti-spam du courtier
        time.sleep(0.2)




# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="OtmAnalytics AI", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 38px; font-weight: bold; color: #00FF7F; }
    .signal-card { padding: 20px; border-radius: 10px; text-align: center; color: white; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 OtmAnalytics - Price Action AI")

if 'fetcher' not in st.session_state or not hasattr(st.session_state.fetcher, 'get_stored_count'):
    st.session_state.fetcher = DataFetcher()

# --- SIDEBAR ---
st.sidebar.header("⚙️ Configuration")
category = st.sidebar.selectbox("Catégorie", list(ASSETS.keys()))
symbol = st.sidebar.selectbox("Actif", ASSETS[category])
tf_label = st.sidebar.selectbox("Timeframe", list(TIMEFRAMES.keys()))
tf_seconds = TIMEFRAMES[tf_label]

# À mettre dans la sidebar (main.py)
if os.path.exists("trade_history.csv"):
    with open("trade_history.csv", "rb") as f:
        st.sidebar.download_button(
            label="📥 Télécharger l'Historique des Trades",
            data=f,
            file_name="trade_history.csv",
            mime="text/csv"
        )


if st.sidebar.button("Tester Connexion Deriv"):
    if st.session_state.fetcher.connect_ws():
        st.sidebar.success("Connexion établie !")
    else:
        st.sidebar.error("Échec de connexion.")

def update_sidebar_stats(symbol, tf_seconds):
    count = st.session_state.fetcher.get_stored_count(symbol, tf_seconds)
    st.sidebar.info(f"📁 Bougies en base : {count}")

update_sidebar_stats()

tab1, tab2, tab3, tab4 = st.tabs(["📥 Données", "🧠 Entraînement", "🔴 Live", "🧪 Backtesting"])

# --- TAB 1: DONNÉES HISTORIQUES ---
with tab1:
    st.subheader("Récupération de l'Historique")
    c1, c2 = st.columns(2)
    start_d = c1.date_input("Date Début", date(2024, 1, 1))
    end_d = c2.date_input("Date Fin", date.today())
    
    if st.button("Lancer le téléchargement", type="primary"):
        start_dt = datetime.combine(start_d, datetime.min.time())
        end_dt = datetime.combine(end_d, datetime.max.time())
        prog_bar = st.progress(0, text="Téléchargement des données...")
        total = st.session_state.fetcher.fetch_history_stream(symbol, tf_seconds, start_dt, end_dt, prog_bar)
        if total > 0:
            st.success(f"✅ {total} nouvelles bougies enregistrées !")
            update_sidebar_stats()

    df = st.session_state.fetcher.load_data(symbol, tf_seconds)
    if not df.empty:
        df = add_indicators(df)
        fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='Prix')])
        
        if 'MA35' in df.columns:
            fig.add_trace(go.Scatter(x=df['date'], y=df['MA35'], line=dict(color='cyan', width=2), name='MA35 (Lente)'))
        if 'MA5' in df.columns:
            fig.add_trace(go.Scatter(x=df['date'], y=df['MA5'], line=dict(color='orange', width=1.5), name='MA5 (Rapide)'))
        
        fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: ENTRAINEMENT ---
with tab2:
    st.header("Apprentissage des Patterns")
    df_raw = st.session_state.fetcher.load_data(symbol, tf_seconds)
    
    if not df_raw.empty:
        df_ind = add_indicators(df_raw)
        st.write(f"📊 {len(df_ind)} bougies chargées pour l'analyse.")
        
        if st.button("Lancer l'entraînement Price Action", type="primary"):
            with st.spinner("L'IA analyse les croisements et les rebonds..."):
                # On met le résultat dans une seule variable pour éviter le plantage
                resultat = train_gru_model(df_ind, symbol, tf_label)
                
                # Déballage sécurisé : on vérifie qu'on a bien reçu 3 éléments
                if isinstance(resultat, tuple) and len(resultat) == 3:
                    msg, loss_history, df_results = resultat
                    
                    if "❌" in msg:
                        st.error(msg)
                    else:
                        st.success(msg)
                        col_g1, col_g2 = st.columns(2)
                        with col_g1:
                            st.subheader("📉 Convergence (Loss)")
                            if loss_history:
                                st.line_chart(loss_history)
                        with col_g2:
                            st.subheader("🎯 Classes (Prédit vs Réel)")
                            if not df_results.empty:
                                st.dataframe(df_results.tail(15), use_container_width=True)
                                accuracy = (df_results['Réel'] == df_results['Prédit']).mean()
                                st.metric("Précision Globale", f"{accuracy:.1%}")
                else:
                    st.error("Erreur de retour : la fonction d'entraînement n'a pas renvoyé les bonnes données.")
    else:
        st.warning("⚠️ Aucune donnée en base. Téléchargez l'historique dans l'onglet 'Données' d'abord.")

# --- TAB 3: TRADING LIVE ---
with tab3:
    st.subheader("🔴 Détection & Trading Automatique")
    col_l1, col_l2 = st.columns([1, 2])
    
    with col_l1:
        # NOUVEAU : Champ pour le Token API Deriv
        api_token = st.text_input("Deriv API Token (Trade Scope)", type="password", help="Utilise le token de ton compte DÉMO pour tester.")
        live_active = st.checkbox("Activer l'analyse Live et l'Auto-Trading", value=False)
        auto_trade = st.toggle("Activer les prises de position (DANGER)", value=False)
        min_conf = st.slider("Confiance minimum pour trader (%)", 60, 99, 85)
        
        price_placeholder = st.empty()
        signal_placeholder = st.empty()
        
    with col_l2:
        chart_placeholder = st.empty()

    if live_active:
        if auto_trade and not api_token:
            st.error("⚠️ Tu dois entrer ton API Token pour trader automatiquement.")
        else:
            try:
                ws = websocket.create_connection(f"{WS_URL}?app_id={APP_ID}", sslopt={"cert_reqs": ssl.CERT_NONE})
                
                # 1. Authentification obligatoire pour trader
                if auto_trade:
                    ws.send(json.dumps({"authorize": api_token}))
                    auth_response = json.loads(ws.recv())
                    if "error" in auth_response:
                        st.error(f"Erreur d'authentification : {auth_response['error']['message']}")
                        st.stop()
                    else:
                        st.success("✅ Compte connecté. Prêt à trader.")

                # 2. Abonnement au flux de prix
                ws.send(json.dumps({"ticks": symbol}))
                last_p, tick_h = 0.0, []
                
                # Drapeau pour éviter de rouvrir 5 positions chaque seconde sur le même signal
                last_trade_time = datetime.now() - timedelta(minutes=5)
                
                while live_active:
                    data = json.loads(ws.recv())
                    
                    # Ignorer les confirmations d'achat pour ne pas casser la boucle des prix
                    if 'buy' in data:
                        st.success(f"✅ Position ouverte avec succès ! ID: {data['buy']['contract_id']}")
                        continue
                        
                    if 'tick' in data:
                        price = float(data['tick']['quote'])
                        price_placeholder.metric(f"PRIX {symbol}", f"{price:.2f}", f"{price-last_p:.2f}")
                        last_p = price
                        
                        df_live = st.session_state.fetcher.load_data(symbol, tf_seconds)
                        if len(df_live) > 40:
                            df_live = add_indicators(df_live)
                            event_class, conf = predict_live(df_live.tail(30))
                            
                            signals = {
                                0: ("RECHERCHE...", "#333333"),
                                1: ("🚀 CROISEMENT HAUSSIER", "#00FF7F"),
                                2: ("💀 CROISEMENT BAISSIER", "#FF4B4B"),
                                3: ("📈 REBOND (Continuation)", "#00BFFF"),
                                4: ("📉 REJET (Continuation)", "#FF8C00")
                            }
                            
                            label, color = signals.get(event_class, ("INCONNU", "gray"))
                            
                            signal_placeholder.markdown(f"""
                                <div class="signal-card" style="background-color:{color};">
                                    <h2 style="margin:0;">{label}</h2>
                                    <p style="margin:5px 0 0 0;">Confiance IA : {conf}%</p>
                                </div>
                            """, unsafe_allow_html=True)

                            # --- NOUVEAU : LOGIQUE D'EXÉCUTION ---
                            # On vérifie : mode auto activé + signal valide + confiance suffisante + temps de refroidissement (cooldown de 1 min minimum)
                            now = datetime.now()
                            if auto_trade and event_class in [1, 2, 3, 4] and conf >= min_conf:
                                if (now - last_trade_time).seconds > 60: # Évite le spam sur la même bougie
                                    execute_multiple_trades(ws, symbol, event_class, stake=5.0, count=5)
                                    last_trade_time = now # On réinitialise le chronomètre

                        tick_h.append(price)
                        if len(tick_h) > 50: tick_h.pop(0)
                        fig_t = px.line(y=tick_h, title="Flux Ticks").update_layout(template="plotly_dark", height=400)
                        chart_placeholder.plotly_chart(fig_t, use_container_width=True)
                        
                    time.sleep(0.1)
            except Exception as e:
                st.error(f"Erreur de connexion : {e}")

# --- NOUVEAU : LOGIQUE D'EXÉCUTION ET DE SAUVEGARDE ---
now = datetime.now()
if auto_trade and event_class in [1, 2, 3, 4] and conf >= min_conf:
    if (now - last_trade_time).seconds > 60:
        
        # 1. On détermine la direction pour le log
        direction = "CALL (Achat)" if event_class in [1, 3] else "PUT (Vente)"
        
        # 2. On exécute le trade
        execute_multiple_trades(ws, symbol, event_class, stake=5.0, count=5)
        
        # 3. On sauvegarde dans l'historique
        save_trade_history(symbol, direction, 5.0, conf, 5)
        
        st.toast(f"✅ Trade {direction} loggé avec succès !")
        last_trade_time = now

# --- TAB 4: BACKTESTING ---
with tab4:
    st.header("🧪 Simulateur de Stratégie (Backtesting)")
    st.info("L'IA va rejouer le passé récent et simuler des trades sur ses propres signaux.")
    
    # Paramètres du simulateur
    c1, c2, c3 = st.columns(3)
    initial_capital = c1.number_input("Capital Initial ($)", value=1000)
    trade_amount = c2.number_input("Mise par Trade ($)", value=50)
    bt_candles = c3.number_input("Historique à tester (Bougies)", value=1000, max_value=5000)
    
    if st.button("🚀 Lancer le Backtest", type="primary"):
        df_all = st.session_state.fetcher.load_data(symbol, tf_seconds)
        
       
        
        if len(df_all) > bt_candles + WINDOW_SIZE:
            with st.spinner("L'IA scanne l'historique et simule les trades..."):
                if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
                    model = load_model(MODEL_PATH)
                    scaler = joblib.load(SCALER_PATH)
                    
                    # 1. Préparation des données du passé
                    df_bt = add_indicators(df_all.tail(int(bt_candles) + WINDOW_SIZE)).copy()
                    df_feat = extract_candlestick_features(df_bt)
                    feature_cols = ['body', 'upper_wick', 'lower_wick', 'MA_Dist_pct', 'MA5_Slope', 'RSI14', 'ATR14']
                    
                    data = df_feat[feature_cols].values
                    data_scaled = scaler.transform(data)
                    
                    # 2. Création des fenêtres pour l'IA
                    X_bt = []
                    for i in range(WINDOW_SIZE, len(data_scaled)):
                        X_bt.append(data_scaled[i-WINDOW_SIZE:i])
                    X_bt = np.array(X_bt)
                    
                    # 3. L'IA prédit tout d'un coup (Batch)
                    predictions = model.predict(X_bt, verbose=0)
                    classes_pred = np.argmax(predictions, axis=1)
                    
                    # 4. Simulation du portefeuille
                    capital = initial_capital
                    capital_history = [capital]
                    trades_won, trades_lost = 0, 0
                    trade_log = []
                    
                    prices = df_bt['close'].values[WINDOW_SIZE:]
                    dates = df_bt['date'].values[WINDOW_SIZE:]
                    
                    # Règles de trade : On sort de position 5 bougies après le signal
                    HOLD_PERIOD = 5
                    LEVIER = 50 # Levier simulé pour rendre les profits réalistes
                    
                    for i in range(len(classes_pred) - HOLD_PERIOD):
                        signal = classes_pred[i]
                        
                        if signal in [1, 2, 3, 4]: # Si un vrai signal est détecté
                            entry_price = prices[i]
                            exit_price = prices[i + HOLD_PERIOD]
                            
                            # Calcul de la variation en pourcentage
                            if signal in [1, 3]: # LONG (Achat)
                                pnl_pct = (exit_price - entry_price) / entry_price
                                trade_type = "LONG 📈"
                            else: # SHORT (Vente)
                                pnl_pct = (entry_price - exit_price) / entry_price
                                trade_type = "SHORT 📉"
                                
                            # Calcul du profit en dollars
                            profit = trade_amount * pnl_pct * LEVIER
                            capital += profit
                            
                            if profit > 0:
                                trades_won += 1
                            else:
                                trades_lost += 1
                                
                            trade_log.append({
                                # Correction ICI :
                                "Date": pd.to_datetime(dates[i]).strftime("%Y-%m-%d %H:%M"),
                                "Type": trade_type,
                                "Signal": signal,
                                "Prix Entrée": round(entry_price, 5),
                                "Prix Sortie": round(exit_price, 5),
                                "Profit ($)": round(profit, 2),
                                "Capital ($)": round(capital, 2)
                            })
                            
                        # Historique de la courbe de capital
                        capital_history.append(capital)
                        
                    # --- AFFICHAGE DES RÉSULTATS ---
                    total_trades = trades_won + trades_lost
                    win_rate = (trades_won / total_trades * 100) if total_trades > 0 else 0
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Capital Final", f"{capital:.2f} $", f"{capital - initial_capital:.2f} $")
                    col2.metric("Trades Exécutés", total_trades)
                    col3.metric("Taux de Réussite", f"{win_rate:.1f} %")
                    col4.metric("Profit Net", f"{capital - initial_capital:.2f} $")
                    
                    # Tracé de la courbe
                    fig_eq = px.line(y=capital_history, title="Croissance du Capital (Equity Curve)")
                    fig_eq.update_layout(template="plotly_dark", yaxis_title="Capital ($)", xaxis_title="Évolution dans le temps")
                    fig_eq.update_traces(line_color='#00FF7F')
                    st.plotly_chart(fig_eq, use_container_width=True)
                    
                    if trade_log:
                        st.subheader("📝 Journal d'ordres (Trade Log)")
                        st.dataframe(pd.DataFrame(trade_log), use_container_width=True)
                else:
                    st.error("⚠️ L'IA n'est pas entraînée. Allez dans l'onglet 'Entraînement' d'abord.")
        else:
            st.warning("⚠️ Pas assez de données pour le backtest. Téléchargez plus de bougies dans l'onglet 1.")
