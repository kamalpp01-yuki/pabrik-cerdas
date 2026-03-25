import streamlit as st
import pandas as pd
from datetime import datetime

def jalankan(df_bahan, df_jadi, conn):
    st.markdown("## 📦 Modul Gudang Terpadu (Inventory)")
    st.write("Pantau kapasitas dan lakukan restock material.")
    st.divider()

    tab1, tab2 = st.tabs(["🏭 Gudang Bahan Baku", "🛍️ Gudang Barang Jadi"])

    # --- TAB 1: BAHAN BAKU ---
    with tab1:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("### 📥 Beli Bahan Baku")
            with st.form("form_beli_bahan", clear_on_submit=True):
                if df_bahan.empty:
                    st.warning("⚠️ Data kosong!"); st.stop()
                pilihan_bahan = st.selectbox("Pilih Material", df_bahan["Nama Bahan"].tolist())
                tambah_stok = st.number_input("Jumlah Masuk", min_value=1, value=10)
                harga_beli = st.number_input("Total Harga Beli (Rp)", min_value=0, step=10000)
                
                if st.form_submit_button("🛒 Restock Material", use_container_width=True):
                    df_bahan['Stok'] = pd.to_numeric(df_bahan['Stok'], errors='coerce').fillna(0)
                    df_bahan.loc[df_bahan['Nama Bahan'] == pilihan_bahan, 'Stok'] += tambah_stok
                    conn.update(worksheet="Bahan_Baku", data=df_bahan)
                    
                    if harga_beli > 0:
                        try: df_uang = conn.read(worksheet="Keuangan").dropna(how="all")
                        except: df_uang = pd.DataFrame(columns=["Tanggal", "Keterangan", "Pemasukan (Rp)", "Pengeluaran (Rp)"])
                        
                        df_uang_update = pd.concat([df_uang, pd.DataFrame([{"Tanggal": datetime.now().strftime("%Y-%m-%d"), "Keterangan": f"Beli {tambah_stok} {pilihan_bahan}", "Pemasukan (Rp)": 0, "Pengeluaran (Rp)": harga_beli}])], ignore_index=True)
                        conn.update(worksheet="Keuangan", data=df_uang_update)
                    
                    st.cache_data.clear()
                    st.success(f"✅ {pilihan_bahan} berhasil masuk!")
                    st.rerun()

        with col2:
            st.markdown("### 📊 Status Kapasitas Material")
            df_bahan['Stok'] = pd.to_numeric(df_bahan['Stok'], errors='coerce').fillna(0)
            df_bahan['Max Kapasitas'] = pd.to_numeric(df_bahan['Max Kapasitas'], errors='coerce').fillna(1000)
            
            for index, row in df_bahan.iterrows():
                stok, maks = row['Stok'], row['Max Kapasitas']
                persentase = min(stok / maks, 1.0) if maks > 0 else 0
                if stok <= 0: st.error(f"🚨 HABIS: {row['Nama Bahan']} kosong!")
                elif persentase < 0.1: st.warning(f"⚠️ Menipis: {row['Nama Bahan']} (Sisa {stok})")
                st.progress(persentase, text=f"{row['Nama Bahan']}: {stok}/{maks} {row['Satuan']}")
            
            st.dataframe(df_bahan, use_container_width=True)

    # --- TAB 2: BARANG JADI ---
    with tab2:
        st.markdown("### 📊 Status Ruangan Gudang Barang Jadi")
        df_jadi['Stok'] = pd.to_numeric(df_jadi['Stok'], errors='coerce').fillna(0)
        total_stok_jadi = df_jadi['Stok'].sum()
        KAPASITAS_MAX_GUDANG = 2000 
        
        persentase_gudang = min(total_stok_jadi / KAPASITAS_MAX_GUDANG, 1.0)
        
        if persentase_gudang >= 1.0: st.error(f"🚨 GUDANG PENUH! (Total: {total_stok_jadi} Pcs)")
        elif persentase_gudang > 0.8: st.warning(f"⚠️ Hampir penuh! ({total_stok_jadi}/{KAPASITAS_MAX_GUDANG} Pcs)")
            
        st.progress(persentase_gudang, text=f"Kapasitas Total: {total_stok_jadi} / {KAPASITAS_MAX_GUDANG} Pcs")
        st.divider()
        st.dataframe(df_jadi, use_container_width=True)