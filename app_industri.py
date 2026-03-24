import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Smart Factory Cloud", layout="wide")
st.title("🏭 Smart Factory: Database Abadi")
st.write("Sistem Pencatatan Produksi Real-Time dengan Google Sheets")

# --- KONEKSI KE DATABASE (GOOGLE SHEETS) ---
# Mengambil kunci rahasia dari Streamlit Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# Membaca data dari Google Sheets (ttl=0 agar selalu mengambil data paling baru)
# Kita batasi membaca 5 kolom saja (A sampai E)
df_lama = conn.read(ttl=0, usecols=[0, 1, 2, 3, 4])
df_lama = df_lama.dropna(how="all") # Membersihkan baris kosong bawaan Excel

# --- SIDEBAR: FORM INPUT DATA ---
st.sidebar.header("📥 Input Order Baru")

# Menggunakan form agar web tidak loading terus saat mengetik angka
with st.sidebar.form("form_produksi", clear_on_submit=True):
    produk = st.selectbox("Pilih Produk", ["Meja Kayu", "Kursi Makan", "Lemari Pakaian"])
    jumlah = st.number_input("Jumlah Pesanan", min_value=1, value=10)
    submit_button = st.form_submit_button("🚀 Simpan ke Cloud")

# Logika Perhitungan Teknik Industri
def hitung_kebutuhan(p, j):
    data = {"Meja Kayu": (2, 1.5), "Kursi Makan": (1, 0.5), "Lemari Pakaian": (4, 3.0)}
    return data[p][0] * j, data[p][1] * j

# --- PROSES PENYIMPANAN DATA (BACKEND) ---
if submit_button:
    k_kayu, k_waktu = hitung_kebutuhan(produk, jumlah)
    waktu_skrg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Membuat baris data baru
    data_baru = pd.DataFrame([{
        "Produk": produk, 
        "Jumlah": jumlah, 
        "Kayu (Balok)": k_kayu, 
        "Waktu (Jam)": k_waktu, 
        "Waktu Input": waktu_skrg
    }])
    
    # Menggabungkan data lama dari Google Sheets dengan data baru
    df_update = pd.concat([df_lama, data_baru], ignore_index=True)
    
    # Menimpa file Google Sheets dengan data yang sudah diupdate
    conn.update(data=df_update)
    
    st.sidebar.success("✅ Data berhasil disimpan permanen di Google Sheets!")
    # Memaksa web memuat ulang agar tabel langsung menampilkan data terbaru
    st.rerun()

# --- TAMPILAN DASHBOARD UTAMA (FRONTEND) ---
if not df_lama.empty:
    st.subheader("📋 Database Produksi Real-Time")
    # Menampilkan data seperti tabel profesional
    st.dataframe(df_lama, use_container_width=True)
    
    st.divider()
    
    # Kalkulasi Total Pabrik
    total_kayu = df_lama["Kayu (Balok)"].sum()
    total_waktu = df_lama["Waktu (Jam)"].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Order (Batch)", len(df_lama))
    col2.metric("🪵 Total Kebutuhan Kayu", f"{total_kayu} Balok")
    col3.metric("⏱️ Total Beban Kerja", f"{total_waktu} Jam")
    
    # Fitur Download ke Excel lokal
    csv = df_lama.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Laporan (CSV)",
        data=csv,
        file_name='Laporan_Pabrik_Cloud.csv',
        mime='text/csv',
    )
else:
    st.info("ℹ️ Database masih kosong. Silakan input order pertama Anda dari menu sebelah kiri.")