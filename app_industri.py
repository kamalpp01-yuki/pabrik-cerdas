import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# IMPORT MODUL
import modul_pemasaran
# Nanti kita import modul_keuangan, modul_produksi, dan modul_gudang yang baru di sini

# --- 1. PENGATURAN HALAMAN & LOGIN ---
st.set_page_config(page_title="ERP Konveksi Topi", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_screen():
    st.title("🧢 ERP Konveksi Topi")
    st.write("Sistem Perencanaan Sumber Daya Perusahaan (Level Pro)")
    with st.form("login_form"):
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.form_submit_button("Masuk Sistem"):
            if user == "admin" and pw == "kamal123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Username/Password Salah!")

# --- 2. FUNGSI BACA DATABASE ---
@st.cache_data(ttl=5) 
def get_data(tab_name, cols, col_names):
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df = conn.read(worksheet=tab_name, usecols=cols)
        df = df.dropna(how="all")
        df.columns = col_names
        return df
    except Exception as e:
        return pd.DataFrame(columns=col_names)

# --- 3. MODUL ERP UTAMA ---
def main_app():
    st.sidebar.title("🧭 Navigasi ERP Topi")
    # MENU BARU YANG LEBIH RAPI
    menu = st.sidebar.radio("Pilih Modul:", [
        "🤝 Pemasaran (Sales)", 
        "💰 Keuangan (Validator)",
        "🏭 Produksi (PPIC & QC)", 
        "📦 Gudang (Inventory)"
    ])
    st.sidebar.divider()
    st.sidebar.button("🚪 Logout", on_click=lambda: st.session_state.update(logged_in=False))

    conn = st.connection("gsheets", type=GSheetsConnection)

    # ==========================================
    # MODUL 1: PEMASARAN
    # ==========================================
    if menu == "🤝 Pemasaran (Sales)":
        st.header("🤝 Modul Pemasaran & Order")
        kolom_pemasaran = ["ID Order", "Tanggal", "Nama Klien", "Model Topi", "Jumlah (Pcs)", "Total Harga", "File Desain", "Status Validasi"]
        df_pemasaran = get_data("Pemasaran", [0,1,2,3,4,5,6,7], kolom_pemasaran)
        modul_pemasaran.jalankan(df_pemasaran, conn)

    # ==========================================
    # MODUL SEMENTARA (Under Construction)
    # ==========================================
    elif menu == "💰 Keuangan (Validator)":
        st.warning("🚧 Modul Keuangan sedang dirombak untuk fitur Validasi Lunas!")
    elif menu == "🏭 Produksi (PPIC & QC)":
        st.warning("🚧 Modul Produksi sedang dirombak untuk menampilkan Desain!")
    elif menu == "📦 Gudang (Inventory)":
        st.warning("🚧 Modul Gudang sedang dirombak untuk memisahkan Bahan Baku dan Barang Jadi!")

# --- 4. SAKLAR UTAMA ---
if not st.session_state.logged_in:
    login_screen()
else:
    main_app()