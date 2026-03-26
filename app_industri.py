import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- IMPORT SEMUA MODUL ---
import modul_login
# Nanti modul lain di-import di dalam masing-menu biar loadingnya cepat!

# --- 1. PENGATURAN HALAMAN & SESSION STATE ---
st.set_page_config(page_title="ERP Konveksi Topi", page_icon="", layout="wide")

# Inisialisasi Kunci Pintu (Session State)
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False
if "current_user" not in st.session_state:
    st.session_state["current_user"] = ""

# --- SUNTIKAN CUSTOM CSS (LEVEL 4 UI + MOBILE FRIENDLY) ---
st.markdown("""
<style>
    /* 1. Efek Kartu (Card) untuk Papan Skor / Metric */
    div[data-testid="stMetric"] {
        background-color: #1E1E24;
        border-left: 5px solid #00ADB5;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 2px 4px 10px rgba(0,0,0,0.4);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 4px 8px 15px rgba(0, 173, 181, 0.3);
    }

    /* 2. Merombak Radio Button Sidebar menjadi Menu Tombol Elegan */
    div[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
        display: none; 
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: transparent;
        border: 1px solid #00ADB5;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background-color: rgba(0, 173, 181, 0.2);
        transform: translateX(5px);
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #00ADB5;
        color: white !important;
        box-shadow: 0px 4px 10px rgba(0, 173, 181, 0.5);
        border: none;
    }

    /* 3. Efek Tombol (Button) */
    div[data-testid="stButton"] button {
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stButton"] button:hover {
        transform: scale(1.03);
    }
    
    /* 4. Ngilangin menu bawaan Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ========================================================= */
    /* 5. SIHIR MOBILE FRIENDLY (DETEKSI LAYAR HP MAX 768px) 📱  */
    /* ========================================================= */
    @media (max-width: 768px) {
        div[data-testid="stMetric"] {
            padding: 8px 12px !important;
            margin-bottom: -10px !important; 
        }
        div[data-testid="stMetricValue"] > div {
            font-size: 1.4rem !important; 
        }
        div[data-testid="stMetricLabel"] > div {
            font-size: 0.85rem !important;
        }
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
    }
 /* ========================================================= */
    /* 6. SULAP TAB JADI GOOGLE MATERIAL (CLEAN & SIMPLE)        */
    /* ========================================================= */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 4px solid transparent !important; /* Disiapkan tempat buat garis */
        border-radius: 4px 4px 0 0 !important;
        padding: 12px 20px !important;
        margin-right: 5px !important;
        color: #7A8089 !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
    }

    /* Saat mouse lewat */
    button[data-baseweb="tab"]:hover {
        color: #EEEEEE !important;
        background-color: rgba(255, 255, 255, 0.03) !important;
    }

    /* Saat Tab Aktif */
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #00ADB5 !important; /* Teks berubah tosca */
        border-bottom: 4px solid #00ADB5 !important; /* Muncul garis tosca tebal */
        background-color: rgba(0, 173, 181, 0.05) !important; /* Background tosca super pudar */
    }

    /* Hilangkan garis biru tipis bawaan Streamlit */
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

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

# --- 3. MODUL ERP UTAMA (DIJALANKAN KALAU SUDAH LOGIN) ---
def main_app():
    st.sidebar.title("🧭 Navigasi ERP Topi")
    
    # Sapaan personal
    st.sidebar.markdown(f"👤 Selamat bekerja, **{st.session_state['current_user'].capitalize()}**!")
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    # MENU BARU YANG LEBIH RAPI
    menu = st.sidebar.radio("Pilih Modul:", [
        "📊 Dashboard Executive",
        "🤝 Pemasaran (Sales)", 
        "💰 Keuangan (Validator)",
        "🏭 Produksi (PPIC & QC)", 
        "📦 Gudang (Inventory)"
    ])
    
    st.sidebar.divider()
    
    # Tombol Logout Estetik
    if st.sidebar.button("🚪 Logout dari Sistem", use_container_width=True):
        st.session_state["is_logged_in"] = False
        st.session_state["current_user"] = ""
        st.rerun()

    # Koneksi Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)

    # ==========================================
    # MODUL 0: DASHBOARD EXECUTIVE
    # ==========================================
    if menu == "📊 Dashboard Executive":
        with st.spinner("⏳ Mengambil data terbaru dari server..."):
            try: df_pem = conn.read(worksheet="Pemasaran").dropna(how="all")
            except: df_pem = pd.DataFrame()
                
            try: df_uang = conn.read(worksheet="Keuangan").dropna(how="all")
            except: df_uang = pd.DataFrame()
                
            try: df_prod = conn.read(worksheet="Produksi").dropna(how="all")
            except: df_prod = pd.DataFrame()
                
            try: df_jadi = conn.read(worksheet="Barang_Jadi").dropna(how="all")
            except: df_jadi = pd.DataFrame()

            import modul_dashboard
            modul_dashboard.jalankan(df_pem, df_uang, df_prod, df_jadi)
            
    # ==========================================
    # MODUL 1: PEMASARAN
    # ==========================================
    elif menu == "🤝 Pemasaran (Sales)":
        st.header("🤝 Modul Pemasaran & Order")
        with st.spinner("⏳ Memuat data Pemasaran & Katalog Produk..."):
            kolom_pem = ["ID Order", "Tanggal", "Nama Klien", "Model Topi", "Jumlah (Pcs)", "Total Harga", "File Desain", "Status Validasi"]
            try: df_pem = get_data("Pemasaran", [0,1,2,3,4,5,6,7], kolom_pem)
            except: df_pem = pd.DataFrame(columns=kolom_pem)
            
            try: df_produk = conn.read(worksheet="Master_Produk").dropna(how="all")
            except Exception: df_produk = pd.DataFrame()
            
            import modul_pemasaran
            modul_pemasaran.jalankan(df_pem, df_produk, conn)

    # ==========================================
    # MODUL 2: KEUANGAN (VALIDATOR)
    # ==========================================
    elif menu == "💰 Keuangan (Validator)":
        st.header("ERP Keuangan & Validasi")
        kolom_uang = ["Tanggal", "Keterangan", "Pemasukan (Rp)", "Pengeluaran (Rp)"]
        df_uang = get_data("Keuangan", [0,1,2,3], kolom_uang)
        
        kolom_pem = ["ID Order", "Tanggal", "Nama Klien", "Model Topi", "Jumlah (Pcs)", "Total Harga", "File Desain", "Status Validasi"]
        df_pemasaran = get_data("Pemasaran", [0,1,2,3,4,5,6,7], kolom_pem)
        
        import modul_keuangan
        modul_keuangan.jalankan(df_uang, df_pemasaran, conn)

    # ==========================================
    # MODUL 3: PRODUKSI (PPIC & QC)
    # ==========================================
    elif menu == "🏭 Produksi (PPIC & QC)":
        with st.spinner("⏳ Memuat data Dapur Produksi & Master BOM..."):
            kolom_pem = ["ID Order", "Tanggal", "Nama Klien", "Model Topi", "Jumlah (Pcs)", "Total Harga", "File Desain", "Status Validasi"]
            df_pem = get_data("Pemasaran", [0,1,2,3,4,5,6,7], kolom_pem)
            
            kolom_prod = ["ID Produksi", "ID Order", "Model Topi", "Jumlah (Pcs)", "Status Produksi"]
            df_prod = get_data("Produksi", [0,1,2,3,4], kolom_prod)
            
            kolom_bahan = ["Nama Bahan", "Stok", "Satuan", "Max Kapasitas"]
            df_bahan = get_data("Bahan_Baku", [0,1,2,3], kolom_bahan)
            
            kolom_jadi = ["Model Topi", "Stok", "Satuan", "Max Kapasitas"]
            df_jadi = get_data("Barang_Jadi", [0,1,2,3], kolom_jadi)
            
            try: 
                df_produk = conn.read(worksheet="Master_Produk").dropna(how="all")
            except Exception: 
                df_produk = pd.DataFrame()
            
            import modul_produksi
            modul_produksi.jalankan(df_pem, df_prod, df_bahan, df_jadi, df_produk, conn)
            
    # ==========================================
    # MODUL 4: GUDANG (INVENTORY)
    # ==========================================
    elif menu == "📦 Gudang (Inventory)":
        with st.spinner("⏳ Memuat data Gudang & Pesanan Siap Kirim..."):
            kolom_pem = ["ID Order", "Tanggal", "Nama Klien", "Model Topi", "Jumlah (Pcs)", "Total Harga", "File Desain", "Status Validasi"]
            try: 
                df_pem = get_data("Pemasaran", [0,1,2,3,4,5,6,7], kolom_pem)
            except Exception: 
                df_pem = pd.DataFrame(columns=kolom_pem)
            
            kolom_bahan = ["Nama Bahan", "Stok", "Satuan", "Max Kapasitas"]
            try: 
                df_bahan = get_data("Bahan_Baku", [0,1,2,3], kolom_bahan)
            except Exception: 
                df_bahan = pd.DataFrame(columns=kolom_bahan)
            
            import modul_gudang
            modul_gudang.jalankan(df_pem, df_bahan, conn)


# --- 4. SAKLAR UTAMA (THE GATEKEEPER) ---
# Jika belum login, panggil modul login. Jika sudah, buka aplikasi utama.
if not st.session_state["is_logged_in"]:
    modul_login.tampilkan_login()
else:
    main_app()