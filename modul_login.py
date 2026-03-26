import streamlit as st
import time

# --- LOGIKA AUTH DUMMY ---
def cek_credentials(username, password):
    credentials = {
        "admin": "123",
        "sales": "topi",
        "produksi": "jahit"
    }
    return username in credentials and credentials[username] == password

def tampilkan_login():
    # 1. Suntik CSS kustom khusus Login Page (Modern Dark Theme)
    st.markdown("""
        <style>
            /* Background gradasi full screen */
            [data-testid="stAppViewContainer"] {
                background: linear-gradient(135deg, #11141a 0%, #222831 100%);
            }
            
            /* Sembunyikan Header dan Sidebar bawaan */
            [data-testid="stHeader"] {display: none;}
            
            /* Mengubah kotak form bawaan Streamlit menjadi Glassmorphism Card */
            [data-testid="stForm"] {
                background: rgba(34, 40, 49, 0.8) !important;
                border-radius: 20px !important;
                padding: 40px 30px !important;
                border: 1px solid rgba(0, 173, 181, 0.4) !important;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
            }
            
            /* Styling Judul di dalam form */
            .login-title {
                color: #EEEEEE;
                font-weight: 900;
                font-size: 32px;
                text-align: center;
                margin-bottom: 5px;
            }
            .login-subtitle {
                color: #00ADB5;
                font-size: 14px;
                text-align: center;
                margin-bottom: 30px;
                letter-spacing: 1px;
            }
            
            /* Styling Input Fields */
            .stTextInput input {
                border-radius: 10px !important;
                background-color: #393E46 !important;
                color: #EEEEEE !important;
                padding: 12px !important;
                border: 1px solid #555 !important;
            }
            .stTextInput input:focus {
                border: 1px solid #00ADB5 !important;
                box-shadow: 0 0 5px rgba(0, 173, 181, 0.5) !important;
            }
            
            /* Styling Tombol Masuk */
            .stButton button {
                background: linear-gradient(135deg, #00ADB5 0%, #17a2b8 100%) !important;
                color: white !important;
                border-radius: 10px !important;
                border: none !important;
                padding: 10px !important;
                width: 100% !important;
                font-size: 1.1em !important;
                font-weight: bold !important;
                transition: all 0.3s ease !important;
                margin-top: 15px !important;
            }
            .stButton button:hover {
                transform: translateY(-3px) !important;
                box-shadow: 0 5px 15px rgba(0, 173, 181, 0.5) !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 2. Layout Center menggunakan Columns
    # Memberikan ruang kosong di atas biar formnya turun ke tengah
    st.markdown('<br><br><br>', unsafe_allow_html=True)
    
    # Rasio kolom: Kiri kosong (1), Tengah form (1.5), Kanan kosong (1)
    _, login_col, _ = st.columns([1, 1.5, 1]) 

    with login_col:
        # Form Login
        with st.form("form_login_erp"):
            # Judul sekarang dimasukkan ke DALAM form
            st.markdown("<div class='login-title'>ERP Konveksi</div>", unsafe_allow_html=True)
            st.markdown("<div class='login-subtitle'>SISTEM PERENCANAAN SUMBER DAYA</div>", unsafe_allow_html=True)
            
            user = st.text_input("Username", placeholder="Masukkan Username Admin")
            passw = st.text_input("Password", type="password", placeholder="Masukkan Password")
            
            submit = st.form_submit_button("Masuk Ke Sistem 🚀", use_container_width=True)

        # Logika submit (berada di luar with st.form, tapi masih di dalam column)
        if submit:
            if cek_credentials(user, passw):
                st.session_state["is_logged_in"] = True
                st.session_state["current_user"] = user
                st.success(f"✅ Log in berhasil! Selamat bekerja, {user}.")
                time.sleep(1) # Delay biar notif success kebaca
                st.rerun() # Refresh halaman untuk masuk ke ERP
            elif user == "" or passw == "":
                st.warning("⚠️ Silakan isi Username dan Password.")
            else:
                st.error("❌ Username atau Password salah!")
        
        st.markdown("<p style='text-align:center;color:#555;font-size:12px;margin-top:15px;'>Aplikasi ERP - v2.1", unsafe_allow_html=True)