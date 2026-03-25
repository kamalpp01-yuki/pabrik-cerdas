import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import modul_gudang
import modul_keuangan

# --- 1. PENGATURAN HALAMAN & LOGIN ---
st.set_page_config(page_title="ERP Konveksi Topi", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_screen():
    st.title("🧢 ERP Konveksi Topi")
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
    st.sidebar.title("🧭 Navigasi ERP")
    menu = st.sidebar.radio("Pilih Modul:", ["🏭 Produksi (PPIC)", "📦 Gudang (Inventory)", "💰 Keuangan (Finance)"])
    st.sidebar.divider()
    st.sidebar.button("🚪 Logout", on_click=lambda: st.session_state.update(logged_in=False))

    conn = st.connection("gsheets", type=GSheetsConnection)

    # ==========================================
    # MODUL 1: PRODUKSI (TERINTEGRASI FULL)
    # ==========================================
    if menu == "🏭 Produksi (PPIC)":
        st.header("🏭 Modul Manajemen Produksi")
        kolom_prod = ["Model Topi", "Jumlah (Pcs)", "Kain (m2)", "Benang (Roll)", "Waktu (Jam)", "Waktu Input"]
        df_prod = get_data("Produksi", [0,1,2,3,4,5], kolom_prod)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Input Pesanan")
            with st.form("form_prod", clear_on_submit=True):
                model = st.selectbox("Model Topi", ["Topi Baseball", "Topi Rimba", "Topi Trucker"])
                jumlah = st.number_input("Jumlah (Pcs)", min_value=1, value=50)
                harga_jual = st.number_input("Harga Jual per Pcs (Rp)", min_value=10000, value=35000, step=5000)
                
                submit_produksi = st.form_submit_button("🚀 Produksi & Integrasikan!")
                
                if submit_produksi:
                    if model == "Topi Baseball":
                        k_kain, k_benang, k_waktu = (0.15 * jumlah, 0.05 * jumlah, 0.5 * jumlah)
                    elif model == "Topi Rimba":
                        k_kain, k_benang, k_waktu = (0.25 * jumlah, 0.08 * jumlah, 0.8 * jumlah)
                    else: 
                        k_kain, k_benang, k_waktu = (0.10 * jumlah, 0.04 * jumlah, 0.4 * jumlah)
                    
                    # A: CATAT PRODUKSI
                    data_baru = pd.DataFrame([{
                        "Model Topi": model, "Jumlah (Pcs)": jumlah, 
                        "Kain (m2)": k_kain, "Benang (Roll)": k_benang,
                        "Waktu (Jam)": k_waktu, "Waktu Input": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }])
                    df_update = pd.concat([df_prod, data_baru], ignore_index=True)
                    conn.update(worksheet="Produksi", data=df_update)

                    # B: POTONG GUDANG
                    df_gudang = get_data("Gudang", [0,1,2], ["Nama Barang", "Stok Tersedia", "Satuan"])
                    df_gudang['Stok Tersedia'] = pd.to_numeric(df_gudang['Stok Tersedia'], errors='coerce').fillna(0)
                    df_gudang.loc[df_gudang['Nama Barang'] == "Kain Kanvas (Bahan Utama)", 'Stok Tersedia'] -= k_kain
                    df_gudang.loc[df_gudang['Nama Barang'] == "Benang Jahit", 'Stok Tersedia'] -= k_benang
                    conn.update(worksheet="Gudang", data=df_gudang)

                    # C: TAMBAH UANG KE KEUANGAN
                    df_uang = get_data("Keuangan", [0,1,2,3], ["Tanggal", "Keterangan", "Pemasukan (Rp)", "Pengeluaran (Rp)"])
                    pendapatan_total = harga_jual * jumlah
                    data_uang_baru = pd.DataFrame([{
                        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                        "Keterangan": f"Penjualan {jumlah} Pcs {model}",
                        "Pemasukan (Rp)": pendapatan_total,
                        "Pengeluaran (Rp)": 0
                    }])
                    df_uang_update = pd.concat([df_uang, data_uang_baru], ignore_index=True)
                    conn.update(worksheet="Keuangan", data=df_uang_update)
                    
                    st.cache_data.clear()
                    st.success(f"✅ Sistem Terintegrasi! Produksi dicatat, Stok dipotong, Uang Rp {pendapatan_total:,.0f} masuk kas!")
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
        df_gudang = get_data("Gudang", [0,1,2], kolom_gudang)
        modul_gudang.jalankan(df_gudang, conn)

    # ==========================================
    # MODUL 3: KEUANGAN
    # ==========================================
    elif menu == "💰 Keuangan (Finance)":
        st.header("💰 Modul Arus Kas (Cashflow)")
        kolom_keuangan = ["Tanggal", "Keterangan", "Pemasukan (Rp)", "Pengeluaran (Rp)"]
        df_uang = get_data("Keuangan", [0,1,2,3], kolom_keuangan)
        modul_keuangan.jalankan(df_uang, conn)

# --- 4. SAKLAR UTAMA ---
if not st.session_state.logged_in:
    login_screen()
else:
    main_app()