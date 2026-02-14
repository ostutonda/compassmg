import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
from fpdf import FPDF
import plotly.express as px
import io

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="COMPASMG - Gestion Eclésiastique", layout="wide", page_icon="⛪")

# --- GESTION DE LA BASE DE DONNÉES (SQLITE) ---
DB_NAME = "compasmg.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Table Utilisateurs
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE,
                 password TEXT,
                 role TEXT)''')
    
    # Table Membres
    c.execute('''CREATE TABLE IF NOT EXISTS members (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nom TEXT,
                 prenom TEXT,
                 email TEXT,
                 telephone TEXT,
                 date_naissance DATE,
                 departement TEXT,
                 date_adhesion DATE)''')
    
    # Table Finances
    c.execute('''CREATE TABLE IF NOT EXISTS finance (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 type TEXT, -- Entrée/Sortie
                 categorie TEXT, -- Dîme, Offrande, Achat...
                 montant REAL,
                 date DATE,
                 description TEXT)''')

    # Table Modèles de Lettres (Secrétariat)
    c.execute('''CREATE TABLE IF NOT EXISTS templates (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 titre TEXT,
                 contenu TEXT)''') # Contenu avec placeholders {nom}, {date}

    # Création Admin par défaut (si vide)
    c.execute("SELECT count(*) FROM users")
    if c.fetchone()[0] == 0:
        # Mdp: admin123 (hashé basiquement pour démo)
        pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  ("admin", pwd_hash, "Administrateur"))
        conn.commit()

    conn.commit()
    conn.close()

# Appel initial de la DB
init_db()

# --- FONCTIONS UTILITAIRES & CACHE ---

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@st.cache_data(ttl=60) # Cache pour éviter de taper la DB à chaque refresh
def get_data(query, params=None):
    conn = sqlite3.connect(DB_NAME)
    if params:
        df = pd.read_sql_query(query, conn, params=params)
    else:
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def run_query(query, params):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()
    st.cache_data.clear() # Invalider le cache après modification

# --- AUTHENTIFICATION & RBAC ---

def login():
    st.markdown("## 🔐 Connexion COMPASMG")
    username = st.text_input("Utilisateur")
    password = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        hashed = hash_password(password)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, hashed))
        user = c.fetchone()
        conn.close()
        
        if user:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.session_state['role'] = user[0]
            st.rerun()
        else:
            st.error("Identifiants incorrects.")

def check_access(allowed_roles):
    if st.session_state.get('role') not in allowed_roles:
        st.error("⛔ Accès refusé. Vos privilèges sont insuffisants pour cette section.")
        return False
    return True

# --- MODULES FONCTIONNELS ---

def module_admin():
    st.title("🛠️ Panneau Administrateur")
    
    tab1, tab2 = st.tabs(["Gestion Utilisateurs", "Configuration"])
    
    with tab1:
        st.subheader("Créer un nouvel utilisateur")
        new_user = st.text_input("Nouvel Identifiant")
        new_pass = st.text_input("Nouveau Mot de passe", type="password")
        new_role = st.selectbox("Rôle", ["Administrateur", "Secrétariat", "Trésorerie", "Chef de Département"])
        
        if st.button("Ajouter Utilisateur"):
            run_query("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                      (new_user, hash_password(new_pass), new_role))
            st.success(f"Utilisateur {new_user} créé.")
        
        st.divider()
        st.subheader("Liste des utilisateurs")
        df_users = get_data("SELECT id, username, role FROM users")
        st.dataframe(df_users, use_container_width=True)

def module_membres():
    st.title("👥 Gestion des Membres")
    
    # Logique conditionnelle selon rôle
    is_admin = st.session_state['role'] in ["Administrateur", "Secrétariat"]
    
    if is_admin:
        with st.expander("➕ Ajouter un membre"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nom")
            prenom = c2.text_input("Prénom")
            email = c1.text_input("Email")
            tel = c2.text_input("Téléphone")
            dept = st.selectbox("Département", ["Aucun", "Chorale", "Protocole", "Jeunesse", "Hommes", "Femmes"])
            date_n = st.date_input("Date de Naissance")
            
            if st.button("Enregistrer Membre"):
                run_query('''INSERT INTO members (nom, prenom, email, telephone, date_naissance, departement, date_adhesion)
                             VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                             (nom, prenom, email, tel, date_n, dept, datetime.now()))
                st.success("Membre ajouté !")

    # Affichage / Recherche
    search = st.text_input("🔍 Rechercher un membre (Nom)")
    query = "SELECT * FROM members"
    params = None
    if search:
        query += " WHERE nom LIKE ?"
        params = ('%' + search + '%',)
    
    df_membres = get_data(query, params)
    
    # Filtrage pour Chef de Département
    if st.session_state['role'] == "Chef de Département":
        dept_filter = st.text_input("Entrez votre département pour filtrer", "Jeunesse")
        df_membres = df_membres[df_membres['departement'] == dept_filter]

    st.dataframe(df_membres, use_container_width=True)

def module_finance():
    st.title("💰 Finances & Trésorerie")
    
    tab1, tab2 = st.tabs(["Saisie Transaction", "Tableau de Bord"])
    
    with tab1:
        c1, c2, c3 = st.columns(3)
        type_trans = c1.selectbox("Type", ["Entrée", "Sortie"])
        cat_trans = c2.selectbox("Catégorie", ["Dîme", "Offrande", "Don", "Loyer", "Électricité", "Autre"])
        montant = c3.number_input("Montant", min_value=0.0, step=10.0)
        desc = st.text_area("Description")
        
        if st.button("Enregistrer Transaction"):
            run_query("INSERT INTO finance (type, categorie, montant, date, description) VALUES (?, ?, ?, ?, ?)",
                      (type_trans, cat_trans, montant, datetime.now(), desc))
            st.success("Transaction enregistrée.")

    with tab2:
        df_fin = get_data("SELECT * FROM finance")
        if not df_fin.empty:
            df_fin['date'] = pd.to_datetime(df_fin['date'])
            
            # KPI
            total_entree = df_fin[df_fin['type'] == "Entrée"]['montant'].sum()
            total_sortie = df_fin[df_fin['type'] == "Sortie"]['montant'].sum()
            solde = total_entree - total_sortie
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Entrées Totales", f"{total_entree:,.2f} $")
            k2.metric("Sorties Totales", f"{total_sortie:,.2f} $")
            k3.metric("Solde Actuel", f"{solde:,.2f} $", delta_color="normal")
            
            # Charts
            c_chart1, c_chart2 = st.columns(2)
            with c_chart1:
                fig_pie = px.pie(df_fin[df_fin['type'] == "Entrée"], values='montant', names='categorie', title="Répartition des Entrées")
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with c_chart2:
                # Group by date
                df_grouped = df_fin.groupby([df_fin['date'].dt.date, 'type'])['montant'].sum().reset_index()
                fig_bar = px.bar(df_grouped, x='date', y='montant', color='type', title="Évolution Temporelle", barmode='group')
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Aucune donnée financière.")

def module_secretariat():
    st.title("🖨️ Secrétariat & Génération de Documents")
    
    st.info("Ce module permet de générer des lettres à partir de modèles.")
    
    # 1. Gestion des modèles
    with st.expander("📝 Gérer les Modèles de Lettres"):
        titre_tpl = st.text_input("Titre du modèle (ex: Attestation de Baptême)")
        content_tpl = st.text_area("Contenu (Utilisez {nom}, {prenom}, {date} comme variables)", height=150)
        if st.button("Sauvegarder Modèle"):
            run_query("INSERT INTO templates (titre, contenu) VALUES (?, ?)", (titre_tpl, content_tpl))
            st.success("Modèle sauvegardé.")

    st.divider()
    
    # 2. Génération
    st.subheader("Générer un document")
    
    # Sélection du membre
    membres = get_data("SELECT id, nom, prenom FROM members")
    if not membres.empty:
        membre_dict = {f"{row['nom']} {row['prenom']}": row for _, row in membres.iterrows()}
        selected_membre_name = st.selectbox("Choisir un membre", list(membre_dict.keys()))
        selected_membre_data = membre_dict[selected_membre_name]
        
        # Sélection du modèle
        templates = get_data("SELECT * FROM templates")
        if not templates.empty:
            tpl_dict = {row['titre']: row['contenu'] for _, row in templates.iterrows()}
            selected_tpl_name = st.selectbox("Choisir un modèle", list(tpl_dict.keys()))
            raw_text = tpl_dict[selected_tpl_name]
            
            # Prévisualisation et remplacement
            st.caption("Prévisualisation du texte brut :")
            st.text(raw_text)
            
            # Fusion des données
            try:
                final_text = raw_text.format(
                    nom=selected_membre_data['nom'],
                    prenom=selected_membre_data['prenom'],
                    date=datetime.now().strftime("%d/%m/%Y")
                )
                
                st.markdown("### Résultat :")
                st.write(final_text)
                
                if st.button("📄 Télécharger en PDF"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.cell(200, 10, txt=f"COMPASMG - {datetime.now().strftime('%d/%m/%Y')}", ln=1, align='C')
                    pdf.ln(20)
                    pdf.multi_cell(0, 10, txt=final_text)
                    
                    pdf_output = pdf.output(dest='S').encode('latin-1', 'replace') # Output to string buffer
                    
                    st.download_button(
                        label="📥 Télécharger le PDF",
                        data=pdf_output,
                        file_name=f"{selected_tpl_name}_{selected_membre_data['nom']}.pdf",
                        mime="application/pdf"
                    )

            except KeyError as e:
                st.error(f"Erreur de formatage : La variable {e} est manquante dans les données du membre.")
        else:
            st.warning("Aucun modèle disponible.")
    else:
        st.warning("Aucun membre dans la base.")

# --- NAVIGATION PRINCIPALE ---

def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['role'] = None

    if not st.session_state['logged_in']:
        login()
    else:
        # Sidebar Navigation
        st.sidebar.title(f"👤 {st.session_state['username']}")
        st.sidebar.caption(f"Rôle : {st.session_state['role']}")
        
        menu_options = ["Accueil"]
        role = st.session_state['role']
        
        # Logique d'affichage dynamique des menus selon le Cahier des Charges
        if role == "Administrateur":
            menu_options.extend(["Membres", "Finances", "Secrétariat", "Admin"])
        elif role == "Secrétariat":
            menu_options.extend(["Membres", "Secrétariat"])
        elif role == "Trésorerie":
            menu_options.extend(["Membres", "Finances"]) # Membres en lecture seule géré dans le module
        elif role == "Chef de Département":
            menu_options.extend(["Membres"])

        choice = st.sidebar.radio("Navigation", menu_options)
        
        if st.sidebar.button("Déconnexion"):
            st.session_state['logged_in'] = False
            st.rerun()

        # Routing
        if choice == "Accueil":
            st.markdown("## Bienvenue sur COMPASMG")
            st.info("Sélectionnez un module dans le menu latéral.")
            
            
            
        elif choice == "Membres":
            if check_access(["Administrateur", "Secrétariat", "Trésorerie", "Chef de Département"]):
                module_membres()
        elif choice == "Finances":
            if check_access(["Administrateur", "Trésorerie"]):
                module_finance()
        elif choice == "Secrétariat":
            if check_access(["Administrateur", "Secrétariat"]):
                module_secretariat()
        elif choice == "Admin":
            if check_access(["Administrateur"]):
                module_admin()

if __name__ == '__main__':
    main()
