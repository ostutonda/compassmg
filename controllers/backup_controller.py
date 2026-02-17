import shutil
import os
from datetime import datetime
import streamlit as st

def backup_database():
    source = "compasmg.db"
    if not os.path.exists("backups"):
        os.makedirs("backups")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = f"backups/compasmg_backup_{timestamp}.db"
    
    if os.path.exists(source):
        shutil.copy2(source, destination)
        return destination
    return None