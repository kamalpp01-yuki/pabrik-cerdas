import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. SETTING HALAMAN (WAJIB PALING ATAS) ---
st.set_page_config(
    page_title="PabrikTopi Pro | ERP Cerdas",
    page_icon="🧢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# SUPER CSS INJECTION (OVERHAUL TOTAL UI)
# ==========================================
st.markdown("""
<style>
    /* 1. Import Font Modern (Poppins) */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    /* 2. Global Styles */
    html, body, [class*="css"]  {
        font-family: 'Poppins', sans-serif;
        color: #E0E0E0;
    }
    
    .stApp {
        background-color: #0F1116; /* Background Utama Super Gelap */
    }

    /* 3. Menghilangkan Header Default Streamlit (Biar Pro) */
    header, footer { visibility: hidden; }
    
    /* 4. OVERHAUL SIDEBAR NAVIGASI (KIRI) */
    [data-testid="stSidebar"] {
        background-color: #16191F !important; /* Warna Sidebar */
        border-right: 1px solid #2D343F;
        padding-top: 20px;
    }
    
    /* Judul Navigasi */
    [data-testid="stSidebar"] h1 {
        font-size: 20px !important;
        color: #00D2D2 !important; /* Warna Aksen Teal */
        font-weight: 700 !important;
        text-align: center;
        margin-bottom: 30px !important;
    }

    /* Mengubah Radio Button jadi Menu Vertical Modern */
    div.stRadio > div {
        background-color: transparent !important;
        gap: 8px; /* Jarak antar menu */
    }

    div.stRadio > div > label {
        background-color: transparent;
        border-radius: 8px;
        padding: 10px 15px !important;
        transition: all 0.2s ease;
        border: 1px solid transparent;
        width: 100%;
    }

    /* Efek Hover di Menu Sidebar */
    div.stRadio > div > label:hover {
        background-color: #2D343F !important;
        cursor: pointer;
    }

    /* Efek Menu Aktif (Selected) */
    div.stRadio > div > label[data-testid="stWidgetLabel"] > div[data-testid="stMarkdownContainer"] > p {
        font-weight: 500 !important;
    }
    
    div.stRadio > div > label[data-selected="true"] {
        background-color: rgba(0, 210, 210, 0.1) !important; /* Background Teal Transparan */
        border: 1px solid #00D2D2 !important; /* Border Teal */
    }
    
    div.stRadio > div > label[data-selected="true"] p {
        color: #00D2D2 !important; /* Warna Teks Teal pas aktif */
    }

    /* 5. STYLING KONTEN UTAMA (KARTU ELEGAN) */
    /* Container untuk Box Konten */
    .erp-card {
        background-color: #16191F;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #2D343F;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    
    h1.main-title {
        color: #FFFFFF;
        font-weight: 700;
        font-size: 28px;
        margin-bottom: 5px;
    }
    
    p.sub-title {
        color: #A0A0A0;
        margin-bottom: 25px;
        font-weight: 300;
    }

    /* Tabel yang lebih bersih */
    div[data-testid="stDataFrame"] {
        border: 1px solid #2D343F;
        border-radius: 8px;
        overflow: hidden;
    }

    /* Perbaikan Input Form */
    div[data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
    }
    
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #0F1116 !important;
        border: 1px solid #2D343F !important;
        border-radius: 8px !important;
        color: #E0E0E0 !important;
    }

    /* Tombol Utama Pro */
    div.stButton > button {
        background-color: #00D2D2 !important; /* Warna Teal */
        color: #0F1116 !important; /* Teks Gelap */
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease !important;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 210, 210, 0.3);
    }
    
    /* Tombol Logout di Sidebar */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: transparent !important;
        color: #FF4B4B !important;
        border: 1px solid #FF4B4B !important;
        width: 100%;
        margin-top: 20px;
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: rgba(255, 75, 75, 0.1) !important;
        box-shadow: none;
    }

    /* CUSTOM CSS UNTUK DASHBOARD METRICS */
    div[data-testid="stMetric"] {
        background-color: #1E1E24; /* Kotak Metric */
        border-left: 5px solid #00D2D2;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 4px 10px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
    }
</style>
""", unsafe_allow_html=True)


# --- 2. FUNGSI BACA DATABASE (DENGAN CACHE) ---
@st.cache_data(ttl=5) 
def get_data_v2(tab_name):
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df = conn.read(worksheet=tab_name)
        df = df.dropna(how="all")
        return df
    except Exception as e:
        st.error(f"Gagal baca tab {tab_name}: {e}")
        return pd.DataFrame()

# --- 3. LOGIN SCREEN (STYLED) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_screen():
    st.markdown("<div style='text-align:center; margin-top:100px;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size:40px; color:#FFFFFF;'>🧢 Pabrik<span style='color:#00D2D2;'>Topi</span> Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#A0A0A0; font-weight:300; margin-bottom:30px;'>Sistem ERP Cerdas Generasi Baru</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("<h3 style='text-align:center; color:#FFFFFF; margin-bottom:20px;'>Gerbang Masuk Sistem</h3>", unsafe_allow_html=True)
            user = st.text_input("Username", placeholder="Masukkan username")
            pw = st.text_input("Password", type="password", placeholder="Masukkan password")
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Masuk Ke Sistem 🚀")
            
            if submit:
                if user == "admin" and pw == "kamal123":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Username/Password Salah!")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 4. MAIN APP (OVERHAUL STRUCTURE) ---
def main_app():
    # SIDEBAR TITLE
    st.sidebar.markdown("<h1>⚙️ ERP MENU</h1>", unsafe_allow_html=True)
    
    # NAVIGATION (RADIO BUTTON STYLED AS MENU)
    menu = st.sidebar.radio("Pilih Divisi:", [
        "📊 Dashboard Executive",
        "🤝 Divisi Pemasaran", 
        "💰 Divisi Keuangan",
        "🏭 Divisi Produksi", 
        "📦 Divisi Gudang"
    ], label_visibility="collapsed") # Sembunyikan label radio asli
    
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    
    # LOGOUT BUTTON
    st.sidebar.button("🚪 Logout Sistem", on_click=lambda: st.session_state.update(logged_in=False))

    conn = st.connection("gsheets", type=GSheetsConnection)

    # ------------------------------------------
    # MODUL 0: DASHBOARD EXECUTIVE (FINAL UI)
    # ------------------------------------------
    if menu == "📊 Dashboard Executive":
        st.markdown("<h1 class='main-title'>DASHBOARD EXECUTIVE</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Ringkasan Performa Pabrik Real-Time</p>", unsafe_allow_html=True)
        
        try:
            # 1. Sedot semua data
            df_pem = get_data_v2("Pemasaran")
            df_uang = get_data_v2("Keuangan")
            df_prod = get_data_v2("Produksi")
            df_jadi = get_data_v2("Barang_Jadi")
            
            # 2. Hitung Metrics
            total_order = len(df_pem)
            
            pemasukan = pd.to_numeric(df_uang['Pemasukan (Rp)'], errors='coerce').fillna(0).sum()
            pengeluaran = pd.to_numeric(df_uang['Pengeluaran (Rp)'], errors='coerce').fillna(0).sum()
            saldo = pemasukan - pengeluaran
            
            dijahit = len(df_prod[df_prod['Status Produksi'] == 'Sedang Diproduksi'])
            gudang_pcs = pd.to_numeric(df_jadi['Stok'], errors='coerce').fillna(0).sum()
            
            # 3. TAMPILKAN METRICS (DALAM ER-CARD)
            st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
            st.markdown("### 📈 Indikator Kunci (KPI)")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(label="🛒 Pesanan Masuk", value=f"{total_order} Order")
            c2.metric(label="💰 Saldo Kas", value=f"Rp {saldo:,.0f}".replace(",", "."))
            c3.metric(label="⚙️ Proses Jahit", value=f"{dijahit} Batch WIP")
            c4.metric(label="📦 Stok Barang Jadi", value=f"{gudang_pcs} Pcs")
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
            st.markdown("### 📊 Analitik Visual")
            
            cg1, cg2 = st.columns(2)
            with cg1:
                st.markdown("**📊 Posisi Stok Topi**")
                if not df_jadi.empty:
                    st.bar_chart(df_jadi.set_index("Model Topi")["Stok"], color="#00D2D2")
                    
            with cg2:
                st.markdown("**📉 Tren Keuangan (Harian)**")
                if not df_uang.empty:
                    df_u_chart = df_uang.groupby("Tanggal")[["Pemasukan (Rp)", "Pengeluaran (Rp)"]].sum()
                    st.line_chart(df_u_chart)
            st.markdown("</div>", unsafe_allow_html=True)
            
        except Exception:
            st.info("💡 Selamat datang! Silakan isi data di modul operasional untuk mengisi dashboard ini.")

    # ------------------------------------------
    # MODUL 1: PEMASARAN (OVERHAUL UI)
    # ------------------------------------------
    elif menu == "🤝 Divisi Pemasaran":
        # Header di luar kartu
        st.markdown("<h1 class='main-title'>DIVISI PEMASARAN</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Manajemen Pesanan Pelanggan (CRM)</p>", unsafe_allow_html=True)
        
        # Suntikkan fungsi pemasaran yang baru (akan kita buat di langkah berikutnya)
        import modul_pemasaran_v2
        modul_pemasaran_v2.jalankan(conn)

    # ------------------------------------------
    # MODUL 2, 3, 4 (UNDER CONSTRUCTION VERSI MANTAP)
    # ------------------------------------------
    else:
        st.markdown(f"<h1 class='main-title'>{menu}</h1>", unsafe_allow_html=True)
        st.markdown("<div class='erp-card' style='text-align:center;'>", unsafe_allow_html=True)
        st.markdown("### 🛠️ Modul Sedang Dirombak")
        st.write("Sabar Bos! Divisi ini lagi dipasangin kramik baru biar mengkilap.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. RUN SAKLAR ---
if not st.session_state.logged_in:
    login_screen()
else:
    main_app()