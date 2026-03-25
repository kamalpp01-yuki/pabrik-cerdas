import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pem, conn):
    st.markdown("## 🤝 Modul Pemasaran & Order")
    
    # --- MINI DASHBOARD PEMASARAN ---
    total_order = len(df_pem)
    pending = len(df_pem[df_pem['Status Validasi'] == 'Menunggu Pembayaran'])
    selesai = len(df_pem[df_pem['Status Validasi'].str.contains('Selesai', case=False, na=False)])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pesanan Klien", f"{total_order} Order")
    c2.metric("Menunggu Pembayaran", f"{pending} Order", delta="- Action Needed", delta_color="inverse")
    c3.metric("Pesanan Selesai", f"{selesai} Order")
    st.divider()

    tab1, tab2 = st.tabs(["📝 Form Pesanan Baru", "📋 Database Pesanan Klien"])

    # TAB 1: FORM
    with tab1:
        with st.form("form_order_baru", clear_on_submit=True):
            col_kiri, col_kanan = st.columns(2)
            with col_kiri:
                nama_klien = st.text_input("Nama Klien / Instansi")
                model_topi = st.selectbox("Model Topi", ["Topi Baseball", "Topi Rimba", "Topi Trucker", "Topi Bucket"])
                jumlah = st.number_input("Jumlah (Pcs)", min_value=1, value=50)
            with col_kanan:
                harga = st.number_input("Total Harga (Rp)", min_value=0, step=50000)
                file_desain = st.file_uploader("Upload Desain", type=["jpg", "png"])

            if st.form_submit_button("💾 Simpan & Teruskan ke Keuangan", use_container_width=True):
                if nama_klien == "" or harga <= 0:
                    st.error("⚠️ Nama Klien dan Harga harus diisi!")
                else:
                    # --- TAMBAHKAN SPINNER DI SINI ---
                    with st.spinner("🚀 Sedang mengunggah desain dan menyimpan data pesanan..."):
                        id_order = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        nama_file_simpan = "Tidak Ada Desain"
                        if file_desain:
                            os.makedirs("desain_topi", exist_ok=True)
                            nama_file_simpan = f"{id_order}_{file_desain.name}"
                            with open(os.path.join("desain_topi", nama_file_simpan), "wb") as f:
                                f.write(file_desain.getbuffer())

                        data_baru = pd.DataFrame([{"ID Order": id_order, "Tanggal": datetime.now().strftime("%Y-%m-%d"), "Nama Klien": nama_klien, "Model Topi": model_topi, "Jumlah (Pcs)": jumlah, "Total Harga": harga, "File Desain": nama_file_simpan, "Status Validasi": "Menunggu Pembayaran"}])
                        conn.update(worksheet="Pemasaran", data=pd.concat([df_pem, data_baru], ignore_index=True))
                        st.cache_data.clear()
                        st.success("✅ Pesanan disimpan!")
                        st.rerun()

    # TAB 2: DATABASE
    with tab2:
        st.dataframe(df_pem, use_container_width=True, height=400)