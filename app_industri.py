import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. PENGATURAN HALAMAN & MEMORI LOGIN ---
st.set_page_config(page_title="Konveksi Topi Cerdas", layout="wide")

# Mengingat status login agar tidak disuruh login terus saat refresh
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 2. HALAMAN PINTU GERBANG (LOGIN) ---
def login_screen():
    st.title("🧢 Portal Konveksi Topi")
    st.write("Silakan login untuk mengakses sistem manajemen produksi.")
    
    with st.form("login_form"):
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        submit = st.form_submit_button("Masuk")
        
        if submit:
            # Username dan Password sederhana
            if user == "admin" and pw == "kamal123":
                st.session_state.logged_in = True
                st.success("Login Berhasil! Memuat sistem...")
                st.rerun() # Memuat ulang web agar pindah ke halaman dalam
            else:
                st.error("Username atau Password Salah!")

# --- 3. HALAMAN DALAM (DASHBOARD PRODUKSI) ---
def main_app():
    # Tombol Keluar di Sidebar
    st.sidebar.button("🚪 Keluar (Logout)", on_click=lambda: st.session_state.update(logged_in=False))
    st.sidebar.divider()
    
    st.title("🏭 Dashboard Konveksi Topi")
    
    # Koneksi ke Database Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Tarik data (Ambil 6 kolom A sampai F)
    try:
        df_lama = conn.read(ttl=0, usecols=[0, 1, 2, 3, 4, 5])
        df_lama = df_lama.dropna(how="all") # Bersihkan baris kosong
    except Exception as e:
        # Jika error saat baca awal, buat dataframe kosong
        df_lama = pd.DataFrame(columns=["Model Topi", "Jumlah (Pcs)", "Kain (m2)", "Benang (Roll)", "Waktu (Jam)", "Waktu Input"])

    # Sidebar: Form Input Order
    st.sidebar.header("📥 Input Order Baru")
    with st.sidebar.form("form_produksi", clear_on_submit=True):
        model = st.selectbox("Pilih Model Topi", ["Topi Baseball", "Topi Rimba", "Topi Trucker (Jaring)"])
        jumlah = st.number_input("Jumlah Pesanan (Pcs)", min_value=1, value=50)
        submit_button = st.form_submit_button("🚀 Simpan ke Cloud")

    # Rumus Hitungan Kebutuhan per 1 Pcs Topi
    def hitung_kebutuhan(m, j):
        # Format Data: "Nama Topi": (Kain m2, Benang roll, Waktu jam)
        data_bahan = {
            "Topi Baseball": (0.15, 0.05, 0.5),
            "Topi Rimba": (0.25, 0.08, 0.8),
            "Topi Trucker (Jaring)": (0.10, 0.04, 0.4) 
        }
        kain = data_bahan[m][0] * j
        benang = data_bahan[m][1] * j
        waktu = data_bahan[m][2] * j
        return kain, benang, waktu

    # Proses Simpan Data
    if submit_button:
        k_kain, k_benang, k_waktu = hitung_kebutuhan(model, jumlah)
        waktu_skrg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Buat Data Baru
        data_baru = pd.DataFrame([{
            "Model Topi": model, 
            "Jumlah (Pcs)": jumlah, 
            "Kain (m2)": k_kain, 
            "Benang (Roll)": k_benang,
            "Waktu (Jam)": k_waktu, 
            "Waktu Input": waktu_skrg
        }])
        
        # Gabung dan Update ke Google Sheets
        df_update = pd.concat([df_lama, data_baru], ignore_index=True)
        conn.update(data=df_update)
        
        st.sidebar.success("✅ Order berhasil dicatat!")
        st.rerun()

    # Tampilan Tabel dan Angka Penting
    if not df_lama.empty:
        st.subheader("📋 Log Produksi Berjalan")
        st.dataframe(df_lama, use_container_width=True)
        
        st.divider()
        st.subheader("📊 Akumulasi Kebutuhan Pabrik")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Batch", len(df_lama))
        col2.metric("🧵 Kebutuhan Kain", f"{df_lama['Kain (m2)'].sum():.1f} m²")
        col3.metric("🧶 Kebutuhan Benang", f"{df_lama['Benang (Roll)'].sum():.1f} Roll")
        col4.metric("⏱️ Beban Waktu", f"{df_lama['Waktu (Jam)'].sum():.1f} Jam")
    else:
        st.info("Database kosong. Silakan input order pertama dari sebelah kiri.")

# --- 4. SAKLAR UTAMA (MENENTUKAN HALAMAN MANA YANG MUNCUL) ---
if not st.session_state.logged_in:
    login_screen()
else:
    main_app()