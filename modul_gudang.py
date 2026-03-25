import streamlit as st
import pandas as pd
from datetime import datetime

def jalankan(df_bahan, df_jadi, conn):
    st.subheader("📦 Modul Gudang Terpadu (Inventory)")

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📥 Beli Bahan Baku")
        with st.form("form_beli_bahan", clear_on_submit=True):
            if df_bahan.empty:
                st.warning("⚠️ Data Bahan Baku kosong di Google Sheets!")
                st.stop()

            daftar_bahan = df_bahan["Nama Bahan"].tolist()
            pilihan_bahan = st.selectbox("Pilih Material", daftar_bahan)
            tambah_stok = st.number_input("Jumlah Masuk", min_value=1, value=10)
            harga_beli = st.number_input("Total Harga Beli (Rp)", min_value=0, step=10000)
            
            if st.form_submit_button("🛒 Update Stok & Catat Pengeluaran"):
                # 1. TAMBAH STOK DI GUDANG BAHAN BAKU
                df_bahan['Stok'] = pd.to_numeric(df_bahan['Stok'], errors='coerce').fillna(0)
                df_bahan.loc[df_bahan['Nama Bahan'] == pilihan_bahan, 'Stok'] += tambah_stok
                conn.update(worksheet="Bahan_Baku", data=df_bahan)
                
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
                        "Keterangan": f"Beli {tambah_stok} {pilihan_bahan} (Restock)",
                        "Pemasukan (Rp)": 0,
                        "Pengeluaran (Rp)": harga_beli
                    }])
                    df_uang_update = pd.concat([df_uang, data_uang_baru], ignore_index=True)
                    conn.update(worksheet="Keuangan", data=df_uang_update)
                
                st.cache_data.clear()
                st.success(f"✅ {tambah_stok} {pilihan_bahan} masuk gudang. Kas terpotong Rp {harga_beli:,.0f}")
                st.rerun()

    with col2:
        st.markdown("### 🏭 Gudang Bahan Baku (Material)")
        st.dataframe(df_bahan, use_container_width=True)
        
        # BIKIN PROGRESS BAR UNTUK BAHAN BAKU
        df_bahan['Stok'] = pd.to_numeric(df_bahan['Stok'], errors='coerce').fillna(0)
        df_bahan['Max Kapasitas'] = pd.to_numeric(df_bahan['Max Kapasitas'], errors='coerce').fillna(1000)
        
        for index, row in df_bahan.iterrows():
            stok = row['Stok']
            maks = row['Max Kapasitas']
            persentase = min(stok / maks, 1.0) if maks > 0 else 0
            
            if persentase < 0.1:
                st.warning(f"⚠️ Stok {row['Nama Bahan']} menipis! Sisa {stok} {row['Satuan']}.")
            
            st.progress(persentase, text=f"Kapasitas {row['Nama Bahan']}: {stok}/{maks} {row['Satuan']}")

        st.divider()

        st.markdown("### 🛍️ Gudang Barang Jadi (Siap Jual)")
        st.dataframe(df_jadi, use_container_width=True)
        
        # BIKIN PROGRESS BAR UNTUK BARANG JADI
        df_jadi['Stok'] = pd.to_numeric(df_jadi['Stok'], errors='coerce').fillna(0)
        df_jadi['Max Kapasitas'] = pd.to_numeric(df_jadi['Max Kapasitas'], errors='coerce').fillna(500)
        
        for index, row in df_jadi.iterrows():
            stok = row['Stok']
            maks = row['Max Kapasitas']
            persentase = min(stok / maks, 1.0) if maks > 0 else 0
            st.progress(persentase, text=f"Kapasitas {row['Model Topi']}: {stok}/{maks} {row['Satuan']}")