import streamlit as st
import time

# --- LOGIKA AUTH DUMMY (SESUAIKAN DENGAN PUNYAMU) ---
def cek_credentials(username, password):
    # Ganti dengan logika database atau hardcoded sesungguhnya
    credentials = {
        "admin": "123",
        "sales": "topi",
        "produksi": "jahit"
    }
    return username in credentials and credentials[username] == password

# --- MODUL TAMPILAN LOGIN ESTETIK ---
def tampilkan_login():
    # 1. Suntik CSS kustom khusus Login Page (Modern Dark Theme)
    st.markdown("""
        <style>
            #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
            
            /* Background gradasi full screen */
            [data-testid="stAppViewContainer"] {
                background: linear-gradient(135deg, #11141a 0%, #222831 100%);
            }
            
            /* Sembunyikan Header Streamlit */
            [data-testid="stHeader"] {display: none;}
            
            /* Styling untuk container form login */
            .stForm {background-color: transparent !important; border: None !important; padding: 0 !important;}
            div[data-testid="stForm"] {border: none;}
            
            /* Kotak Login (Glassmorphism effect) */
            .login-card {
                background: rgba(34, 40, 49, 0.7);
                border-radius: 25px;
                padding: 50px;
                border: 1px solid rgba(0, 173, 181, 0.4);
                box-shadow: 0 10px 30px rgba(0, 173, 181, 0.2);
                margin-top: 10vh;
                text-align: center;
            }
            
            /* Styling Judul */
            .login-card h1 {
                color: #EEEEEE;
                font-weight: 900;
                font-size: 36px !important;
                margin-bottom: 10px !important;
            }
            .login-card p.subtitle {
                color: #A9A9A9;
                font-size: 16px;
                margin-bottom: 30px;
            }
            
            /* Styling Input Fields */
            .stTextInput input {
                border-radius: 12px !important;
                background-color: #393E46 !important;
                color: #EEEEEE !important;
                padding: 15px !important;
                font-size: 16px !important;
            }
            .stTextInput label {color: #A9A9A9 !important;}
            
            /* Styling Tombol Masuk */
            .stButton button {
                background: linear-gradient(135deg, #00ADB5 0%, #17a2b8 100%) !important;
                color: white !important;
                border-radius: 12px !important;
                border: none !important;
                padding: 15px !important;
                width: 100% !important;
                font-size: 1.2em !important;
                font-weight: 900 !important;
                transition: all 0.3s ease !important;
            }
            .stButton button:hover {
                transform: translateY(-3px) !important;
                box-shadow: 0 5px 15px rgba(0, 173, 181, 0.5) !important;
                background-color: #EEEEEE !important;
                color: #00ADB5 !important;
            }
            .stButton button:focus:not(:active) {
                background-color: #EEEEEE !important;
                color: #00ADB5 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 2. Layout Center menggunakan Columns
    st.markdown('<br>', unsafe_allow_html=True)
    _, login_col, _ = st.columns([1.2, 2.5, 1.2]) # Mengetengahkan form

    with login_col:
        # Buka div card kustom
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # Header Estetik
        st.markdown("<h1>🎩 ERP Konveksi Topi</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Sistem Perencanaan Sumber Daya Cerdas</p>", unsafe_allow_html=True)
        
        # Form Login
        with st.form("form_login_erp"):
            user = st.text_input("Username", placeholder="Masukkan ID Pengguna Anda", label_visibility="collapsed")
            passw = st.text_input("Password", type="password", placeholder="Masukkan Kata Sandi", label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Masuk Ke Sistem 🚀", use_container_width=True)

        if submit:
            if cek_credentials(user, passw):
                st.session_state["is_logged_in"] = True
                st.session_state["current_user"] = user
                st.success(f"Log in berhasil! Selamat bekerja, {user}.")
                time.sleep(1) # Delay biar notif success kebaca
                st.rerun() # Refresh halaman untuk masuk ke ERP
            elif user == "" or passw == "":
                st.error("Silakan isi Username dan Password.")
            else:
                st.error("Username atau Password salah!")
        
        # Tutup div card kustom
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#555;font-size:12px;margin-top:20px;'>Level Pro - v2.1 | Powered by Streamlit</p>", unsafe_allow_html=True)