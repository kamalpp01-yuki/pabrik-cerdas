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
        "📊 Dashboard Executive",
        "🤝 Pemasaran (Sales)", 
        "💰 Keuangan (Validator)",
        "🏭 Produksi (PPIC & QC)", 
        "📦 Gudang (Inventory)"
    ])
    st.sidebar.divider()
    st.sidebar.button("🚪 Logout", on_click=lambda: st.session_state.update(logged_in=False))

    conn = st.connection("gsheets", type=GSheetsConnection)

    # ==========================================
    # MODUL 0: DASHBOARD EXECUTIVE (LEVEL 2 UI)
    # ==========================================
    if menu == "📊 Dashboard Executive":
        st.header("📊 Executive Dashboard")
        st.markdown("Ringkasan performa pabrik topi secara *real-time*.")
        
        try:
            # 1. Sedot semua data dari seluruh divisi
            df_pem = conn.read(worksheet="Pemasaran").dropna(how="all")
            df_uang = conn.read(worksheet="Keuangan").dropna(how="all")
            df_prod = conn.read(worksheet="Produksi").dropna(how="all")
            df_jadi = conn.read(worksheet="Barang_Jadi").dropna(how="all")
            
            # 2. Rumus Hitung-hitungan Cepat ala Manajer
            total_order = len(df_pem)
            
            df_uang['Pemasukan (Rp)'] = pd.to_numeric(df_uang['Pemasukan (Rp)'], errors='coerce').fillna(0)
            total_pendapatan = df_uang['Pemasukan (Rp)'].sum()
            
            df_wip = df_prod[df_prod['Status Produksi'] == 'Sedang Diproduksi']
            sedang_dijahit = len(df_wip)
            
            df_jadi['Stok'] = pd.to_numeric(df_jadi['Stok'], errors='coerce').fillna(0)
            total_gudang = df_jadi['Stok'].sum()
            
            # 3. TAMPILKAN PAPAN SKOR (METRICS)
            st.markdown("### 📈 Skor Performa Hari Ini")
            
            # Bagi layar jadi 4 kolom sejajar
            c1, c2, c3, c4 = st.columns(4)
            
            # Tampilkan kartu metrik yang keren
            c1.metric(label="🛒 Total Pesanan Masuk", value=f"{total_order} Order")
            c2.metric(label="💰 Total Pendapatan", value=f"Rp {total_pendapatan:,.0f}".replace(",", "."))
            c3.metric(label="⚙️ Sedang Dijahit", value=f"{sedang_dijahit} Batch")
            c4.metric(label="📦 Stok Barang Jadi", value=f"{total_gudang} Pcs")
            
            st.divider()
            st.info("💡 Selamat datang di Sistem ERP Cerdas. Silakan navigasi ke modul lain di sebelah kiri untuk melihat detail operasional masing-masing divisi.")
            
        except Exception as e:
            st.warning("Sedang memuat data atau data masih kosong. Silakan isi pesanan pertama Anda!")
            
    # ==========================================
    # MODUL 1: PEMASARAN
    # ==========================================
    elif menu == "🤝 Pemasaran (Sales)":
        st.header("🤝 Modul Pemasaran & Order")
        kolom_pemasaran = ["ID Order", "Tanggal", "Nama Klien", "Model Topi", "Jumlah (Pcs)", "Total Harga", "File Desain", "Status Validasi"]
        df_pemasaran = get_data("Pemasaran", [0,1,2,3,4,5,6,7], kolom_pemasaran)
        modul_pemasaran.jalankan(df_pemasaran, conn)

    # ==========================================
    # MODUL 2: KEUANGAN (VALIDATOR)
    # ==========================================
    elif menu == "💰 Keuangan (Validator)":
        st.header("💰 Modul Keuangan & Validasi")
        
        # Ambil data dari 2 Tab berbeda (Keuangan & Pemasaran)
        kolom_uang = ["Tanggal", "Keterangan", "Pemasukan (Rp)", "Pengeluaran (Rp)"]
        df_uang = get_data("Keuangan", [0,1,2,3], kolom_uang)
        
        kolom_pem = ["ID Order", "Tanggal", "Nama Klien", "Model Topi", "Jumlah (Pcs)", "Total Harga", "File Desain", "Status Validasi"]
        df_pemasaran = get_data("Pemasaran", [0,1,2,3,4,5,6,7], kolom_pem)
        
        # Lempar 2 data itu ke modul keuangan
        import modul_keuangan
        modul_keuangan.jalankan(df_uang, df_pemasaran, conn)

    # ==========================================
    # MODUL 3: PRODUKSI (PPIC & QC)
    # ==========================================
    elif menu == "🏭 Produksi (PPIC & QC)":
        st.header("🏭 Modul Produksi & Quality Control")
        
        # Insinyur sejati memanggil 4 tabel sekaligus!
        kolom_pem = ["ID Order", "Tanggal", "Nama Klien", "Model Topi", "Jumlah (Pcs)", "Total Harga", "File Desain", "Status Validasi"]
        df_pem = get_data("Pemasaran", [0,1,2,3,4,5,6,7], kolom_pem)
        
        kolom_prod = ["ID Produksi", "ID Order", "Model Topi", "Jumlah (Pcs)", "Status Produksi"]
        df_prod = get_data("Produksi", [0,1,2,3,4], kolom_prod)
        
        kolom_bahan = ["Nama Bahan", "Stok", "Satuan", "Max Kapasitas"]
        df_bahan = get_data("Bahan_Baku", [0,1,2,3], kolom_bahan)
        
        kolom_jadi = ["Model Topi", "Stok", "Satuan", "Max Kapasitas"]
        df_jadi = get_data("Barang_Jadi", [0,1,2,3], kolom_jadi)
        
        import modul_produksi
        modul_produksi.jalankan(df_pem, df_prod, df_bahan, df_jadi, conn)

    # ==========================================
    # MODUL 4: GUDANG (INVENTORY) - VERSI ANTI-ERROR
    # ==========================================
    elif menu == "📦 Gudang (Inventory)":
        st.header("📦 Modul Gudang Terpadu")
        
        try:
            # Baca semua kolom di tab Bahan_Baku
            df_bahan = conn.read(worksheet="Bahan_Baku")
            df_bahan = df_bahan.dropna(how="all") # Hapus baris kosong
            
            # Baca semua kolom di tab Barang_Jadi
            df_jadi = conn.read(worksheet="Barang_Jadi")
            df_jadi = df_jadi.dropna(how="all") # Hapus baris kosong
            
            import modul_gudang
            modul_gudang.jalankan(df_bahan, df_jadi, conn)
            
        except Exception as e:
            st.error(f"🚨 Gagal terhubung ke Google Sheets: {e}")
            st.info("Pastikan nama Tab di Google Sheets adalah 'Bahan_Baku' dan 'Barang_Jadi'")

# --- 4. SAKLAR UTAMA ---
if not st.session_state.logged_in:
    login_screen()
else:
    main_app()