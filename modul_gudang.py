import streamlit as st
import pandas as pd

def jalankan(df_gudang, conn):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📥 Barang Masuk (Beli)")
        with st.form("form_update_stok", clear_on_submit=True):
            # Default barang khusus Pabrik Topi
            if df_gudang.empty:
                df_gudang = pd.DataFrame([
                    {"Nama Barang": "Kain Kanvas (Bahan Utama)", "Stok Tersedia": 0, "Satuan": "m2"},
                    {"Nama Barang": "Benang Jahit", "Stok Tersedia": 0, "Satuan": "Roll"},
                    {"Nama Barang": "Pengait/Gesper Topi", "Stok Tersedia": 0, "Satuan": "Pcs"}
                ])
                conn.update(worksheet="Gudang", data=df_gudang)
                st.cache_data.clear()

            daftar_barang = df_gudang["Nama Barang"].tolist()
            pilihan_barang = st.selectbox("Pilih Material", daftar_barang)
            tambah_stok = st.number_input("Jumlah Masuk", min_value=1, value=10)
            
            if st.form_submit_button("Update Stok Gudang"):
                df_gudang['Stok Tersedia'] = pd.to_numeric(df_gudang['Stok Tersedia'], errors='coerce').fillna(0)
                df_gudang.loc[df_gudang['Nama Barang'] == pilihan_barang, 'Stok Tersedia'] += tambah_stok
                
                conn.update(worksheet="Gudang", data=df_gudang)
                st.cache_data.clear()
                
                st.success(f"✅ {tambah_stok} {pilihan_barang} berhasil ditambahkan ke gudang topi!")
                st.rerun()

    with col2:
        st.subheader("📦 Kondisi Stok Real-Time")
        st.dataframe(df_gudang, use_container_width=True)
        
        df_gudang['Stok Tersedia'] = pd.to_numeric(df_gudang['Stok Tersedia'], errors='coerce').fillna(0)
        
        for index, row in df_gudang.iterrows():
            if row['Stok Tersedia'] < 10:
                st.warning(f"⚠️ Stok **{row['Nama Barang']}** menipis! Sisa {row['Stok Tersedia']} {row['Satuan']}.")