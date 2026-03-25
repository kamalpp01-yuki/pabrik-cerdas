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
                conn.update(worksheet="Gudang", data=df_gudang)
                st.cache_data.clear() # Bersihkan memori

            # Ambil daftar barang untuk pilihan
            daftar_barang = df_gudang["Nama Barang"].tolist()
            pilihan_barang = st.selectbox("Pilih Material", daftar_barang)
            tambah_stok = st.number_input("Jumlah Masuk", min_value=1, value=10)
            
            if st.form_submit_button("Update Stok Gudang"):
                # Trik Insinyur: Paksa kolom stok jadi ANGKA dulu biar nggak error kalau dibaca sebagai teks oleh Google Sheets
                df_gudang['Stok Tersedia'] = pd.to_numeric(df_gudang['Stok Tersedia'], errors='coerce').fillna(0)
                
                # Tambahkan stok sesuai pilihan
                df_gudang.loc[df_gudang['Nama Barang'] == pilihan_barang, 'Stok Tersedia'] += tambah_stok
                
                # Timpa data lama ke Google Sheets
                conn.update(worksheet="Gudang", data=df_gudang)
                
                # BERSIHKAN CACHE BIAR WEB LANGSUNG UPDATE ANGKA BARU!
                st.cache_data.clear()
                
                st.success(f"✅ {tambah_stok} {pilihan_barang} berhasil ditambahkan!")
                st.rerun()

    with col2:
        st.subheader("📦 Kondisi Stok Real-Time")
        st.dataframe(df_gudang, use_container_width=True)
        
        # Peringatan Stok Menipis
        # Paksa jadi angka juga sebelum dihitung
        df_gudang['Stok Tersedia'] = pd.to_numeric(df_gudang['Stok Tersedia'], errors='coerce').fillna(0)
        
        for index, row in df_gudang.iterrows():
            if row['Stok Tersedia'] < 10:
                st.warning(f"⚠️ Stok **{row['Nama Barang']}** menipis! Sisa {row['Stok Tersedia']} {row['Satuan']}.")