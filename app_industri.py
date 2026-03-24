import streamlit as st
import pandas as pd

# --- JUDUL APLIKASI ---
st.set_page_config(page_title="Smart Factory System", layout="wide")
st.title("🏭 Sistem Kendali Produksi (Tahap 3)")
st.write("Dilengkapi Sensor Kapasitas Otomatis & Download Laporan")

# --- MEMORI APLIKASI (SESSION STATE) ---
if 'jadwal_produksi' not in st.session_state:
    st.session_state.jadwal_produksi = []

# --- SIDEBAR (INPUT DATA) ---
st.sidebar.header("Input Order Produksi")
produk = st.sidebar.selectbox("Pilih Produk", ["Meja Kayu", "Kursi Makan", "Lemari Pakaian"])
jumlah = st.sidebar.number_input("Jumlah Pesanan", min_value=1, value=10)

def hitung_kebutuhan(p, j):
    data = {"Meja Kayu": (2, 1.5), "Kursi Makan": (1, 0.5), "Lemari Pakaian": (4, 3.0)}
    return data[p][0] * j, data[p][1] * j

if st.sidebar.button("➕ Tambah ke Jadwal"):
    k_kayu, k_waktu = hitung_kebutuhan(produk, jumlah)
    st.session_state.jadwal_produksi.append({
        "Produk": produk, "Jumlah": jumlah, "Kayu (Balok)": k_kayu, "Waktu (Jam)": k_waktu
    })
    st.sidebar.success(f"Berhasil: {jumlah} {produk} masuk antrean!")

if st.sidebar.button("🗑️ Reset Semua Jadwal"):
    st.session_state.jadwal_produksi = [] 
    st.rerun() # Memaksa aplikasi refresh otomatis

# --- TAMPILAN DASHBOARD (FRONTEND) ---
if len(st.session_state.jadwal_produksi) > 0:
    df = pd.DataFrame(st.session_state.jadwal_produksi)
    
    # Menghitung Total
    total_waktu = df["Waktu (Jam)"].sum()
    
    # 💡 FITUR BARU 1: ALARM KAPASITAS (Maksimal 24 Jam Kerja)
    if total_waktu > 24:
        st.error(f"🚨 PERINGATAN! Total jam kerja ({total_waktu} Jam) melebihi kapasitas harian pabrik (24 Jam). Harap kurangi pesanan atau tambah shift pekerja!")
    elif total_waktu > 18:
        st.warning(f"⚠️ Hati-hati! Beban kerja sudah tinggi ({total_waktu} Jam). Mendekati batas maksimal harian.")
    else:
        st.success("✅ Kapasitas pabrik masih aman. Lanjutkan produksi.")

    st.subheader("📋 Daftar Antrean Produksi")
    st.dataframe(df, use_container_width=True)
    
    # 💡 FITUR BARU 2: DOWNLOAD LAPORAN CSV
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Jadwal (Format CSV/Excel)",
        data=csv_data,
        file_name='jadwal_produksi_pabrik.csv',
        mime='text/csv',
    )
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="🪵 TOTAL Kebutuhan Kayu Pabrik", value=f'{df["Kayu (Balok)"].sum()} Balok')
    with col2:
        st.metric(label="⏱️ TOTAL Jam Kerja Pabrik", value=f"{total_waktu} Jam")
        
else:
    st.info("ℹ️ Jadwal produksi masih kosong. Silakan tambah pesanan dari sidebar.")