import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- JUDUL ---
st.set_page_config(page_title="Smart Factory Cloud", layout="wide")
st.title("🏭 Smart Factory: Database Online Edition")

# --- KONEKSI KE GOOGLE SHEETS ---
# Masukkan Link Google Sheets kamu di sini
URL_SHEET = "PASTE_LINK_GOOGLE_SHEETS_KAMU_DI_SINI"

conn = st.connection("gsheets", type=GSheetsConnection)

# Fungsi Membaca Data dari Cloud
def load_data():
    return conn.read(spreadsheet=URL_SHEET, usecols=[0,1,2,3,4])

# --- SIDEBAR INPUT ---
st.sidebar.header("Input Order Produksi")
produk = st.sidebar.selectbox("Pilih Produk", ["Meja Kayu", "Kursi Makan", "Lemari Pakaian"])
jumlah = st.sidebar.number_input("Jumlah Pesanan", min_value=1, value=10)

def hitung_kebutuhan(p, j):
    data = {"Meja Kayu": (2, 1.5), "Kursi Makan": (1, 0.5), "Lemari Pakaian": (4, 3.0)}
    return data[p][0] * j, data[p][1] * j

if st.sidebar.button("🚀 Kirim ke Database Cloud"):
    k_kayu, k_waktu = hitung_kebutuhan(produk, jumlah)
    waktu_skrg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Ambil data lama, tambah data baru
    data_lama = load_data()
    data_baru = pd.DataFrame([{
        "Produk": produk, "Jumlah": jumlah, "Kayu (Balok)": k_kayu, 
        "Waktu (Jam)": k_waktu, "Waktu Input": waktu_skrg
    }])
    
    df_update = pd.concat([data_lama, data_baru], ignore_index=True)
    
    # Upload ke Google Sheets
    conn.update(spreadsheet=URL_SHEET, data=df_update)
    st.sidebar.success("Data Tersimpan Permanen di Cloud!")
    st.rerun()

# --- TAMPILAN DASHBOARD ---
df_display = load_data()

if not df_display.empty:
    st.subheader("📋 Database Produksi Real-Time")
    st.dataframe(df_display, use_container_width=True)
    
    # Metrik Total
    total_waktu = df_display["Waktu (Jam)"].sum()
    st.metric("Total Beban Kerja Pabrik", f"{total_waktu} Jam")
else:
    st.info("Database masih kosong.")