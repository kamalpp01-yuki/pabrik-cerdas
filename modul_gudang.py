import streamlit as st
import pandas as pd

def jalankan(df_gudang, conn):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📥 Barang Masuk (Beli)")
        with st.form("form_update_stok", clear_on_submit=True):
            # Jika tabel gudang di Sheets masih kosong, kita buatkan default-nya
            if df_gudang.empty:
                df_gudang = pd.DataFrame([
                    {"Nama Barang": "Kulit Sintetis", "Stok Tersedia": 0, "Satuan": "m2"},
                    {"Nama Barang": "Sol Karet", "Stok Tersedia": 0, "Satuan": "Pasang"},
                    {"Nama Barang": "Lem Sepatu", "Stok Tersedia": 0, "Satuan": "Liter"}
                ])
                # Otomatis tulis ke Google Sheets biar gak kosong
                conn.update(worksheet="Gudang", data=df_gudang)

            daftar_barang = df_gudang["Nama Barang"].tolist()
            pilihan_barang = st.selectbox("Pilih Material", daftar_barang)
            tambah_stok = st.number_input("Jumlah Masuk", min_value=1, value=10)
            
            if st.form_submit_button("Update Stok Gudang"):
                # Logika Insinyur: Cari nama barangnya, lalu tambahkan stoknya
                df_gudang.loc[df_gudang['Nama Barang'] == pilihan_barang, 'Stok Tersedia'] += tambah_stok
                
                # Timpa data lama dengan data baru yang sudah ditambah
                conn.update(worksheet="Gudang", data=df_gudang)
                st.success(f"✅ {tambah_stok} {pilihan_barang} berhasil masuk gudang!")
                st.rerun()

    with col2:
        st.subheader("📦 Kondisi Stok Real-Time")
        st.dataframe(df_gudang, use_container_width=True)
        
        # Peringatan Stok Menipis (Fitur Canggih)
        for index, row in df_gudang.iterrows():
            if row['Stok Tersedia'] < 10:
                st.warning(f"⚠️ Stok **{row['Nama Barang']}** menipis! Sisa {row['Stok Tersedia']} {row['Satuan']}.")