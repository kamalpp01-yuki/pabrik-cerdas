import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import modul_gudang

# --- 1. PENGATURAN HALAMAN & LOGIN ---
st.set_page_config(page_title="ERP Konveksi Sepatu", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_screen():
    st.title("👟 ERP Konveksi Sepatu")
    st.write("Sistem Perencanaan Sumber Daya Perusahaan (Enterprise Resource Planning)")
    
    with st.form("login_form"):
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        submit = st.form_submit_button("Masuk Sistem")
        
        if submit:
            if user == "admin" and pw == "kamal123":
                st.session_state.logged_in = True
                st.success("Akses Diterima!")
                st.rerun()
            else:
                st.error("Username atau Password Salah!")

# --- 2. FUNGSI BACA DATABASE (Pencegah Error) ---
@st.cache_data(ttl=5) # Refresh data setiap 5 detik
def get_data(tab_name, cols, col_names):
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df = conn.read(worksheet=tab_name, usecols=cols)
        df = df.dropna(how="all")
        df.columns = col_names
        return df, conn
    except Exception as e:
        return pd.DataFrame(columns=col_names), conn

# --- 3. MODUL ERP UTAMA ---
def main_app():
    # MENU NAVIGASI DI SIDEBAR
    st.sidebar.title("🧭 Navigasi ERP")
    menu = st.sidebar.radio("Pilih Modul:", ["🏭 Produksi (PPIC)", "📦 Gudang (Inventory)", "💰 Keuangan (Finance)"])
    st.sidebar.divider()
    st.sidebar.button("🚪 Logout", on_click=lambda: st.session_state.update(logged_in=False))

    # ==========================================
    # MODUL 1: PRODUKSI
    # ==========================================
    if menu == "🏭 Produksi (PPIC)":
        st.header("🏭 Modul Manajemen Produksi")
        kolom_prod = ["Model Sepatu", "Jumlah (Pasang)", "Bahan Kulit (m2)", "Sol Sepatu (Pasang)", "Waktu (Jam)", "Waktu Input"]
        df_prod, conn = get_data("Produksi", [0,1,2,3,4,5], kolom_prod)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Input Pesanan")
            with st.form("form_prod", clear_on_submit=True):
                model = st.selectbox("Model Sepatu", ["Sneakers Kasual", "Sepatu Pantofel", "Sepatu Boots Safety"])
                jumlah = st.number_input("Jumlah (Pasang)", min_value=1, value=20)
                if st.form_submit_button("Catat Produksi"):
                    # Rumus BOM (Bill of Materials)
                    k_kulit = 0.5 * jumlah if model == "Sneakers Kasual" else (0.8 * jumlah if model == "Sepatu Pantofel" else 1.2 * jumlah)
                    k_waktu = 1.5 * jumlah if model == "Sneakers Kasual" else (2.5 * jumlah if model == "Sepatu Pantofel" else 4.0 * jumlah)
                    
                    data_baru = pd.DataFrame([{
                        "Model Sepatu": model, "Jumlah (Pasang)": jumlah, 
                        "Bahan Kulit (m2)": k_kulit, "Sol Sepatu (Pasang)": jumlah,
                        "Waktu (Jam)": k_waktu, "Waktu Input": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }])
                    df_update = pd.concat([df_prod, data_baru], ignore_index=True)
                    conn.update(worksheet="Produksi", data=df_update)
                    st.success("Pesanan dicatat!")
                    st.rerun()
                    
        with col2:
            st.subheader("Riwayat Produksi")
            st.dataframe(df_prod, use_container_width=True)

    # ==========================================
    # MODUL 2: GUDANG
    # ==========================================
    elif menu == "📦 Gudang (Inventory)":
        st.header("📦 Modul Stok Gudang")
        kolom_gudang = ["Nama Barang", "Stok Tersedia", "Satuan"]
        df_gudang, conn = get_data("Gudang", [0,1,2], kolom_gudang)
        
        # LEMPAR TUGASNYA KE FILE SEBELAH!
        modul_gudang.jalankan(df_gudang, conn)

    # ==========================================
    # MODUL 3: KEUANGAN
    # ==========================================
    elif menu == "💰 Keuangan (Finance)":
        st.header("💰 Modul Arus Kas (Cashflow)")
        kolom_keuangan = ["Tanggal", "Keterangan", "Pemasukan (Rp)", "Pengeluaran (Rp)"]
        df_uang, conn = get_data("Keuangan", [0,1,2,3], kolom_keuangan)
        
        st.dataframe(df_uang, use_container_width=True)
        st.info("💡 Fitur input nota dan hitung profit akan kita bangun di tahap selanjutnya!")

# --- 4. SAKLAR UTAMA ---
if not st.session_state.logged_in:
    login_screen()
else:
    main_app()