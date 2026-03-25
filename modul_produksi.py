import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pem, df_prod, df_bahan, df_jadi, conn):
    st.subheader("🏭 Dapur Produksi & Quality Control")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📥 Antrean Siap Produksi")
        # Tarik HANYA pesanan yang sudah Lunas divalidasi Keuangan
        df_antrean = df_pem[df_pem['Status Validasi'] == 'Siap Produksi']

        if df_antrean.empty:
            st.info("Santai dulu, tidak ada antrean pesanan yang siap dijahit.")
        else:
            for index, row in df_antrean.iterrows():
                with st.expander(f"🔥 ORDER: {row['ID Order']} | {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)"):
                    st.write(f"**Klien:** {row['Nama Klien']}")
                    
                    # 1. FITUR TAMPILKAN GAMBAR DESAIN
                    path_gambar = os.path.join("desain_topi", str(row['File Desain']))
                    if os.path.exists(path_gambar):
                        st.image(path_gambar, caption="Desain Klien", use_container_width=True)
                    else:
                        st.warning("⚠️ File gambar tidak ditemukan di server.")

                    # 2. LOGIKA MATEMATIKA: Hitung Kebutuhan Bahan (BOM)
                    jml = int(row['Jumlah (Pcs)'])
                    butuh_kain = jml * 0.1  # Asumsi 1 topi butuh 0.1 m2 kain
                    butuh_benang = jml * 0.05 # Asumsi 1 topi butuh 0.05 roll benang
                    butuh_pengait = jml * 1 # 1 topi butuh 1 pengait

                    st.markdown(f"""
                    **Kebutuhan Material:**
                    * ✂️ Kain Kanvas: {butuh_kain} m2
                    * 🧵 Benang Jahit: {butuh_benang} Roll
                    * 🔗 Pengait: {butuh_pengait} Pcs
                    """)

                    if st.button("✂️ Mulai Jahit & Potong Bahan", key=f"jahit_{row['ID Order']}"):
                        # A. POTONG STOK DI GUDANG BAHAN BAKU
                        df_bahan['Stok'] = pd.to_numeric(df_bahan['Stok'], errors='coerce').fillna(0)
                        
                        # Kita pakai 'str.contains' biar cerdas cari nama bahan walaupun ngetiknya beda
                        df_bahan.loc[df_bahan['Nama Bahan'].str.contains('Kain', case=False, na=False), 'Stok'] -= butuh_kain
                        df_bahan.loc[df_bahan['Nama Bahan'].str.contains('Benang', case=False, na=False), 'Stok'] -= butuh_benang
                        df_bahan.loc[df_bahan['Nama Bahan'].str.contains('Pengait', case=False, na=False), 'Stok'] -= butuh_pengait
                        conn.update(worksheet="Bahan_Baku", data=df_bahan)

                        # B. PINDAHKAN KE TABEL PRODUKSI (Work In Progress)
                        id_prod = f"PRD-{datetime.now().strftime('%H%M%S')}"
                        data_prod = pd.DataFrame([{
                            "ID Produksi": id_prod,
                            "ID Order": row['ID Order'],
                            "Model Topi": row['Model Topi'],
                            "Jumlah (Pcs)": jml,
                            "Status Produksi": "Sedang Diproduksi"
                        }])
                        df_prod_update = pd.concat([df_prod, data_prod], ignore_index=True)
                        conn.update(worksheet="Produksi", data=df_prod_update)

                        # C. UPDATE STATUS DI PEMASARAN
                        df_pem.loc[df_pem['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Sedang Diproduksi'
                        conn.update(worksheet="Pemasaran", data=df_pem)

                        st.cache_data.clear()
                        st.success(f"Bahan berhasil dipotong! {row['Model Topi']} mulai dijahit.")
                        st.rerun()

    with col2:
        st.markdown("### 🔎 Sedang Dijahit (WIP) & QC")
        df_wip = df_prod[df_prod['Status Produksi'] == 'Sedang Diproduksi']
        
        if df_wip.empty:
            st.info("Tidak ada topi yang sedang dijahit saat ini.")
        else:
            for index, row in df_wip.iterrows():
                with st.container():
                    st.info(f"⚙️ **{row['ID Produksi']}** | {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                    
                    if st.button("✅ Lulus QC & Masukkan ke Gudang Barang Jadi", key=f"qc_{row['ID Produksi']}"):
                        
                        # A. TAMBAH STOK KE GUDANG BARANG JADI
                        jml = int(row['Jumlah (Pcs)'])
                        df_jadi['Stok'] = pd.to_numeric(df_jadi['Stok'], errors='coerce').fillna(0)
                        df_jadi.loc[df_jadi['Model Topi'] == row['Model Topi'], 'Stok'] += jml
                        conn.update(worksheet="Barang_Jadi", data=df_jadi)

                        # B. UPDATE STATUS PRODUKSI
                        df_prod.loc[df_prod['ID Produksi'] == row['ID Produksi'], 'Status Produksi'] = 'Selesai & Masuk Gudang'
                        conn.update(worksheet="Produksi", data=df_prod)

                        # C. UPDATE STATUS PEMASARAN
                        df_pem.loc[df_pem['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Selesai & Masuk Gudang'
                        conn.update(worksheet="Pemasaran", data=df_pem)

                        st.cache_data.clear()
                        st.success("✅ Topi lulus QC dan sudah terpajang di Gudang Barang Jadi!")
                        st.rerun()