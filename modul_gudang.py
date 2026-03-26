import streamlit as st
import pandas as pd
from datetime import datetime

def jalankan(df_bahan, df_jadi, conn):
    st.markdown("## 📦 Modul Gudang Terpadu")
    
    df_jadi['Stok'] = pd.to_numeric(df_jadi['Stok'], errors='coerce').fillna(0)
    total_stok_jadi = df_jadi['Stok'].sum()
    df_bahan['Stok'] = pd.to_numeric(df_bahan['Stok'], errors='coerce').fillna(0)
    bahan_menipis = len(df_bahan[df_bahan['Stok'] < 20])
    
    c1, c2 = st.columns(2)
    c1.metric("📦 Total Stok Barang Jadi", f"{total_stok_jadi} Pcs")
    c2.metric("⚠️ Material Perlu Restock", f"{bahan_menipis} Item", delta="Cek Gudang Bahan!", delta_color="inverse")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["🛒 Restock & Tambah Bahan", "🏭 Kapasitas Bahan Baku", "🛍️ Gudang Barang Jadi"])

    # --- TAB 1: RESTOCK & TAMBAH BAHAN BARU ---
    with tab1:
        col_baru, col_restock = st.columns(2)
        
        # FITUR BARU: Daftarkan Material Baru
        with col_baru:
            st.markdown("#### ✨ Daftarkan Jenis Bahan Baru")
            with st.form("form_bahan_baru", clear_on_submit=True):
                nama_b_baru = st.text_input("Nama Material Baru", placeholder="Misal: Kancing Besi")
                satuan_baru = st.text_input("Satuan", placeholder="Misal: Pcs / Kg / Roll")
                max_kap = st.number_input("Kapasitas Max Gudang", min_value=1, value=1000)
                
                if st.form_submit_button("➕ Daftarkan ke Gudang", use_container_width=True):
                    if nama_b_baru == "" or satuan_baru == "":
                        st.error("Nama dan Satuan wajib diisi!")
                    elif nama_b_baru in df_bahan['Nama Bahan'].values:
                        st.error("Bahan ini sudah ada di gudang!")
                    else:
                        data_bahan_baru = pd.DataFrame([{"Nama Bahan": nama_b_baru, "Stok": 0, "Satuan": satuan_baru, "Max Kapasitas": max_kap}])
                        conn.update(worksheet="Bahan_Baku", data=pd.concat([df_bahan, data_bahan_baru], ignore_index=True))
                        st.cache_data.clear(); st.success(f"✅ {nama_b_baru} berhasil didaftarkan!"); st.rerun()

        # FITUR LAMA: Restock Material yang sudah ada
        with col_restock:
            st.markdown("#### 📥 Restock Bahan (Beli)")
            with st.form("form_beli_bahan", clear_on_submit=True):
                if df_bahan.empty: st.stop()
                pilihan_bahan = st.selectbox("Pilih Material", df_bahan["Nama Bahan"].tolist())
                tambah_stok = st.number_input("Jumlah Masuk", min_value=1, value=10)
                harga_beli = st.number_input("Total Harga Beli (Rp)", min_value=0, step=10000)
                
                if st.form_submit_button("🛒 Beli & Restock", use_container_width=True):
                    df_bahan.loc[df_bahan['Nama Bahan'] == pilihan_bahan, 'Stok'] += tambah_stok
                    conn.update(worksheet="Bahan_Baku", data=df_bahan)
                    
                    if harga_beli > 0:
                        try: df_uang = conn.read(worksheet="Keuangan").dropna(how="all")
                        except: df_uang = pd.DataFrame(columns=["Tanggal", "Keterangan", "Pemasukan (Rp)", "Pengeluaran (Rp)"])
                        df_uang_update = pd.concat([df_uang, pd.DataFrame([{"Tanggal": datetime.now().strftime("%Y-%m-%d"), "Keterangan": f"Beli {tambah_stok} {pilihan_bahan}", "Pemasukan (Rp)": 0, "Pengeluaran (Rp)": harga_beli}])], ignore_index=True)
                        conn.update(worksheet="Keuangan", data=df_uang_update)
                    
                    st.cache_data.clear(); st.success(f"✅ {tambah_stok} {pilihan_bahan} masuk gudang!"); st.rerun()

    # TAB 2 & 3 (Sama seperti sebelumnya)
    with tab2:
        st.markdown("### 📊 Status Real-Time Gudang Material")
        df_bahan['Max Kapasitas'] = pd.to_numeric(df_bahan['Max Kapasitas'], errors='coerce').fillna(1000)
        for index, row in df_bahan.iterrows():
            stok, maks = row['Stok'], row['Max Kapasitas']
            persentase = min(stok / maks, 1.0) if maks > 0 else 0
            if stok <= 0: st.error(f"🚨 HABIS: {row['Nama Bahan']} kosong!")
            elif persentase < 0.1: st.warning(f"⚠️ Menipis: {row['Nama Bahan']} (Sisa {stok})")
            st.progress(persentase, text=f"{row['Nama Bahan']}: {stok}/{maks} {row['Satuan']}")
        st.dataframe(df_bahan, use_container_width=True)

    with tab3:
        st.markdown("### 📊 Status Ruangan Gudang Barang Jadi")
        KAPASITAS_MAX_GUDANG = 2000 
        persentase_gudang = min(total_stok_jadi / KAPASITAS_MAX_GUDANG, 1.0)
        if persentase_gudang >= 1.0: st.error(f"🚨 GUDANG PENUH! (Total: {total_stok_jadi} Pcs)")
        elif persentase_gudang > 0.8: st.warning(f"⚠️ Hampir penuh! ({total_stok_jadi}/{KAPASITAS_MAX_GUDANG} Pcs)")
        st.progress(persentase_gudang, text=f"Kapasitas Total: {total_stok_jadi} / {KAPASITAS_MAX_GUDANG} Pcs")
        st.dataframe(df_jadi, use_container_width=True)