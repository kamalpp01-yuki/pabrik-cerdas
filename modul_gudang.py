import streamlit as st
import pandas as pd
from datetime import datetime

def jalankan(df_gudang, conn):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📥 Barang Masuk (Beli)")
        with st.form("form_update_stok", clear_on_submit=True):
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
            
            # FITUR BARU: Input harga beli material
            harga_beli = st.number_input("Total Harga Beli (Rp)", min_value=0, step=10000)
            
            if st.form_submit_button("Update Stok & Catat Pengeluaran"):
                # 1. TAMBAH STOK DI GUDANG
                df_gudang['Stok Tersedia'] = pd.to_numeric(df_gudang['Stok Tersedia'], errors='coerce').fillna(0)
                df_gudang.loc[df_gudang['Nama Barang'] == pilihan_barang, 'Stok Tersedia'] += tambah_stok
                conn.update(worksheet="Gudang", data=df_gudang)
                
                # 2. INTEGRASI KE KEUANGAN (CATAT PENGELUARAN)
                if harga_beli > 0:
                    try:
                        df_uang = conn.read(worksheet="Keuangan", usecols=[0,1,2,3])
                        df_uang = df_uang.dropna(how="all")
                        df_uang.columns = ["Tanggal", "Keterangan", "Pemasukan (Rp)", "Pengeluaran (Rp)"]
                    except Exception:
                        df_uang = pd.DataFrame(columns=["Tanggal", "Keterangan", "Pemasukan (Rp)", "Pengeluaran (Rp)"])

                    data_uang_baru = pd.DataFrame([{
                        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                        "Keterangan": f"Beli {tambah_stok} {pilihan_barang}",
                        "Pemasukan (Rp)": 0,
                        "Pengeluaran (Rp)": harga_beli
                    }])
                    df_uang_update = pd.concat([df_uang, data_uang_baru], ignore_index=True)
                    conn.update(worksheet="Keuangan", data=df_uang_update)
                
                st.cache_data.clear()
                st.success(f"✅ Berhasil! {tambah_stok} {pilihan_barang} ditambahkan dan uang kas terpotong Rp {harga_beli:,.0f}")
                st.rerun()

    with col2:
        st.subheader("📦 Kondisi Stok Real-Time")
        st.dataframe(df_gudang, use_container_width=True)
        
        df_gudang['Stok Tersedia'] = pd.to_numeric(df_gudang['Stok Tersedia'], errors='coerce').fillna(0)
        for index, row in df_gudang.iterrows():
            if row['Stok Tersedia'] < 10:
                st.warning(f"⚠️ Stok **{row['Nama Barang']}** menipis! Sisa {row['Stok Tersedia']} {row['Satuan']}.")