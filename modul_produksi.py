import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pem, df_prod, df_bahan, df_jadi, conn):
    st.markdown("## 🏭 Dapur Produksi & Quality Control")
    st.write("Eksekusi pesanan, potong bahan baku, dan lakukan *Quality Control* (QC).")
    st.divider()

    tab1, tab2 = st.tabs(["✂️ Antrean Potong & Jahit", "🔎 Proses QC & Masuk Gudang"])

    # --- TAB 1: ANTREAN JAHIT ---
    with tab1:
        st.markdown("### 📥 Antrean Siap Produksi")
        df_antrean = df_pem[df_pem['Status Validasi'] == 'Siap Produksi']

        if df_antrean.empty:
            st.info("Santai dulu, tidak ada antrean pesanan yang siap dijahit.")
        else:
            for index, row in df_antrean.iterrows():
                with st.expander(f"🔥 ORDER: {row['ID Order']} | {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Klien:** {row['Nama Klien']}")
                        # BOM
                        jml = int(row['Jumlah (Pcs)'])
                        butuh_kain = jml * 0.1
                        butuh_benang = jml * 0.05
                        butuh_pengait = jml * 1
                        st.markdown(f"**Material:** ✂️ Kain {butuh_kain}m2 | 🧵 Benang {butuh_benang} Roll | 🔗 Pengait {butuh_pengait} Pcs")
                        
                        if st.button("✂️ Mulai Jahit & Potong Bahan", key=f"jahit_{row['ID Order']}", use_container_width=True):
                            df_bahan['Stok'] = pd.to_numeric(df_bahan['Stok'], errors='coerce').fillna(0)
                            df_bahan.loc[df_bahan['Nama Bahan'].astype(str).str.contains('Kain', case=False, na=False), 'Stok'] -= butuh_kain
                            df_bahan.loc[df_bahan['Nama Bahan'].astype(str).str.contains('Benang', case=False, na=False), 'Stok'] -= butuh_benang
                            df_bahan.loc[df_bahan['Nama Bahan'].astype(str).str.contains('Pengait', case=False, na=False), 'Stok'] -= butuh_pengait
                            conn.update(worksheet="Bahan_Baku", data=df_bahan)

                            id_prod = f"PRD-{datetime.now().strftime('%H%M%S')}"
                            data_prod = pd.DataFrame([{"ID Produksi": id_prod, "ID Order": row['ID Order'], "Model Topi": row['Model Topi'], "Jumlah (Pcs)": jml, "Status Produksi": "Sedang Diproduksi"}])
                            conn.update(worksheet="Produksi", data=pd.concat([df_prod, data_prod], ignore_index=True))
                            
                            df_pem.loc[df_pem['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Sedang Diproduksi'
                            conn.update(worksheet="Pemasaran", data=df_pem)
                            st.cache_data.clear()
                            st.success("Bahan dipotong! Mulai dijahit.")
                            st.rerun()
                    with c2:
                        path_gambar = os.path.join("desain_topi", str(row['File Desain']))
                        if os.path.exists(path_gambar):
                            st.image(path_gambar, caption="Desain", width=200)
                        else:
                            st.warning("⚠️ Tidak ada file gambar.")

    # --- TAB 2: QC & WIP ---
    with tab2:
        st.markdown("### 🔎 Sedang Dijahit (WIP) & QC")
        df_wip = df_prod[df_prod['Status Produksi'] == 'Sedang Diproduksi']
        
        if df_wip.empty:
            st.info("Tidak ada topi yang sedang dijahit saat ini.")
        else:
            for index, row in df_wip.iterrows():
                with st.container():
                    st.info(f"⚙️ **{row['ID Produksi']}** | {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                    if st.button("✅ Lulus QC & Masuk Gudang", key=f"qc_{row['ID Produksi']}"):
                        try:
                            jml = int(row['Jumlah (Pcs)'])
                            model_topi = str(row['Model Topi'])
                            if 'Stok' not in df_jadi.columns: df_jadi['Stok'] = 0
                            df_jadi['Stok'] = pd.to_numeric(df_jadi['Stok'], errors='coerce').fillna(0)
                            
                            if model_topi in df_jadi['Model Topi'].astype(str).values:
                                df_jadi.loc[df_jadi['Model Topi'].astype(str) == model_topi, 'Stok'] += jml
                            else:
                                df_jadi = pd.concat([df_jadi, pd.DataFrame([{"Model Topi": model_topi, "Stok": jml, "Satuan": "Pcs", "Max Kapasitas": 500}])], ignore_index=True)
                                
                            conn.update(worksheet="Barang_Jadi", data=df_jadi)
                            df_prod.loc[df_prod['ID Produksi'] == row['ID Produksi'], 'Status Produksi'] = 'Selesai'
                            conn.update(worksheet="Produksi", data=df_prod)
                            df_pem.loc[df_pem['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Selesai'
                            conn.update(worksheet="Pemasaran", data=df_pem)

                            st.cache_data.clear()
                            st.success("✅ Topi masuk Gudang!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"🚨 ERROR: {e}")