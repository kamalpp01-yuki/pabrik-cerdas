import streamlit as st
import pandas as pd
from datetime import datetime

# --- JUDUL ---
st.set_page_config(page_title="Smart Factory Cloud", layout="wide")
st.title("🏭 Smart Factory: Production Log System")
st.write("Sistem Pencatatan Produksi Real-Time")

# --- MEMORI DATA (SESSION STATE) ---
if 'db_produksi' not in st.session_state:
    # Buat data awal agar tabel tidak kosong
    st.session_state.db_produksi = pd.DataFrame(columns=[
        "Produk", "Jumlah", "Kayu (Balok)", "Waktu (Jam)", "Waktu Input"
    ])

# --- SIDEBAR INPUT ---
st.sidebar.header("Input Order Baru")
produk = st.sidebar.selectbox("Pilih Produk", ["Meja Kayu", "Kursi Makan", "Lemari Pakaian"])
jumlah = st.sidebar.number_input("Jumlah Pesanan", min_value=1, value=10)

def hitung_kebutuhan(p, j):
    data = {"Meja Kayu": (2, 1.5), "Kursi Makan": (1, 0.5), "Lemari Pakaian": (4, 3.0)}
    return data[p][0] * j, data[p][1] * j

if st.sidebar.button("🚀 Simpan ke Log Produksi"):
    k_kayu, k_waktu = hitung_kebutuhan(produk, jumlah)
    waktu_skrg = datetime.now().strftime("%H:%M:%S")
    
    # Data baru yang akan dimasukkan
    new_data = pd.DataFrame([{
        "Produk": produk, 
        "Jumlah": jumlah, 
        "Kayu (Balok)": k_kayu, 
        "Waktu (Jam)": k_waktu, 
        "Waktu Input": waktu_skrg
    }])
    
    # Gabungkan ke memori aplikasi
    st.session_state.db_produksi = pd.concat([st.session_state.db_produksi, new_data], ignore_index=True)
    st.sidebar.success("Data berhasil dicatat!")

if st.sidebar.button("🗑️ Reset Database"):
    st.session_state.db_produksi = st.session_state.db_produksi.iloc[0:0]
    st.rerun()

# --- DASHBOARD UTAMA ---
df = st.session_state.db_produksi

if not df.empty:
    st.subheader("📋 Log Aktivitas Pabrik Hari Ini")
    st.table(df) # Menggunakan table agar lebih statis dan aman di browser
    
    st.divider()
    
    # Kalkulasi Total
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Produk", len(df))
    col2.metric("Total Kayu", f"{df['Kayu (Balok)'].sum()} unit")
    col3.metric("Total Jam", f"{df['Waktu (Jam)'].sum()} jam")

    # Fitur Download untuk dipindah ke Excel manual
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Log ke CSV/Excel",
        data=csv,
        file_name='log_produksi.csv',
        mime='text/csv',
    )
else:
    st.info("Belum ada aktivitas produksi yang dicatat.")