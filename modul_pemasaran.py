import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pemasaran, conn):
    # Jurus Engineer: Bikin folder otomatis kalau foldernya belum ada
    if not os.path.exists("desain_topi"):
        os.makedirs("desain_topi")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📝 Input Pesanan Baru (Sales)")
        with st.form("form_pesanan", clear_on_submit=True):
            nama_klien = st.text_input("Nama Klien / Perusahaan")
            model = st.selectbox("Model Topi", ["Topi Baseball", "Topi Rimba", "Topi Trucker"])
            jumlah = st.number_input("Jumlah (Pcs)", min_value=1, value=50)
            harga_total = st.number_input("Total Harga Kesepakatan (Rp)", min_value=10000, step=50000)
            
            # FITUR SAKTI: Upload Gambar Desain
            file_desain = st.file_uploader("Upload Desain Topi (JPG/PNG)", type=['png', 'jpg', 'jpeg'])
            
            submit = st.form_submit_button("💾 Simpan Pesanan")

            if submit:
                if nama_klien == "":
                    st.error("⚠️ Nama Klien tidak boleh kosong!")
                elif file_desain is None:
                    st.error("⚠️ File Desain topi wajib di-upload!")
                else:
                    # 1. Simpan Gambar ke dalam folder 'desain_topi'
                    # Kita kasih nama unik biar file gak ketimpa kalau namanya sama
                    nama_file_unik = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_desain.name}"
                    lokasi_simpan = os.path.join("desain_topi", nama_file_unik)
                    
                    with open(lokasi_simpan, "wb") as f:
                        f.write(file_desain.getbuffer())

                    # 2. Bikin ID Order Otomatis (Contoh: ORD-240325-1030)
                    id_order = f"ORD-{datetime.now().strftime('%y%m%d-%H%M')}"
                    tanggal_sekarang = datetime.now().strftime("%Y-%m-%d")

                    # 3. Simpan Data ke Google Sheets (Tab Pemasaran)
                    data_baru = pd.DataFrame([{
                        "ID Order": id_order,
                        "Tanggal": tanggal_sekarang,
                        "Nama Klien": nama_klien,
                        "Model Topi": model,
                        "Jumlah (Pcs)": jumlah,
                        "Total Harga": harga_total,
                        "File Desain": nama_file_unik,
                        "Status Validasi": "Menunggu Pembayaran" # Status awal yang akan dicegat Keuangan
                    }])

                    df_update = pd.concat([df_pemasaran, data_baru], ignore_index=True)
                    conn.update(worksheet="Pemasaran", data=df_update)
                    
                    st.cache_data.clear()
                    st.success(f"✅ Pesanan {id_order} berhasil dibuat! Status: Menunggu validasi Keuangan.")
                    st.rerun()

    with col2:
        st.subheader("📋 Daftar Pesanan (Sales Order)")
        st.dataframe(df_pemasaran, use_container_width=True)