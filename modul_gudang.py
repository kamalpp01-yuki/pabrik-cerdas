import streamlit as st
import pandas as pd

def jalankan(df_bahan, df_jadi):
    st.subheader("📦 Monitoring Kapasitas Gudang")
    
    col1, col2 = st.columns(2)

    # --- GUDANG 1: BAHAN BAKU ---
    with col1:
        st.markdown("### 🏗️ Gudang Bahan Baku")
        for index, row in df_bahan.iterrows():
            st.write(f"**{row['Nama Bahan']}**")
            st.write(f"Sisa: {row['Stok']} / {row['Max Kapasitas']} {row['Satuan']}")
            
            # Hitung persentase keterisian
            persen = min(float(row['Stok']) / float(row['Max Kapasitas']), 1.0) if float(row['Max Kapasitas']) > 0 else 0
            
            # Tampilkan progress bar (Warna berubah jadi merah kalau hampir penuh)
            st.progress(persen)
            if persen > 0.9:
                st.error("🚨 Kapasitas Maksimal! Jangan beli bahan dulu.")
            elif persen < 0.1:
                st.warning("⚠️ Stok Kritis! Segera belanja bahan.")
        
        st.divider()
        st.dataframe(df_bahan, use_container_width=True)

    # --- GUDANG 2: BARANG JADI ---
    with col2:
        st.markdown("### 🧢 Gudang Barang Jadi (Siap Kirim)")
        for index, row in df_jadi.iterrows():
            st.write(f"**{row['Model Topi']}**")
            st.write(f"Tersedia: {row['Stok']} / {row['Max Kapasitas']} Pcs")
            
            persen_jadi = min(float(row['Stok']) / float(row['Max Kapasitas']), 1.0) if float(row['Max Kapasitas']) > 0 else 0
            
            st.progress(persen_jadi)
            if persen_jadi > 0.8:
                st.error("🚨 Rak penuh! Segera lakukan pengiriman ke klien.")
        
        st.divider()
        st.dataframe(df_jadi, use_container_width=True)