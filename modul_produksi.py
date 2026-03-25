import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pem, df_prod, df_bahan, df_jadi, conn):
    st.markdown("## 🏭 Dapur Produksi & Quality Control")
    
    # --- MINI DASHBOARD PRODUKSI ---
    antrean = len(df_pem[df_pem['Status Validasi'] == 'Siap Produksi'])
    wip = len(df_prod[df_prod['Status Produksi'] == 'Sedang Diproduksi'])
    c1, c2 = st.columns(2)
    c1.metric("📥 Antrean Siap Potong", f"{antrean} Batch")
    c2.metric("⚙️ Sedang Dijahit (WIP)", f"{wip} Batch")
    st.divider()

    tab1, tab2 = st.tabs(["✂️ Antrean Potong & Jahit", "🔎 Proses QC & Masuk Gudang"])

    with tab1:
        df_antrean = df_pem[df_pem['Status Validasi'] == 'Siap Produksi']
        if df_antrean.empty:
            st.info("Santai dulu, tidak ada antrean pesanan.")
        else:
            for index, row in df_antrean.iterrows():
                # INI BIKIN EFEK KARTU (CARD UI)
                with st.container(border=True): 
                    col_img, col_desc, col_btn = st.columns([1, 2.5, 1])
                    
                    with col_img:
                        path_gambar = os.path.join("desain_topi", str(row['File Desain']))
                        if os.path.exists(path_gambar):
                            # Gambar ditaruh di dalam kartu dengan lebar menyesuaikan
                            st.image(path_gambar, use_container_width=True)
                        else:
                            st.info("🖼️ No Image")
                            
                    with col_desc:
                        st.markdown(f"#### {row['ID Order']} - {row['Nama Klien']}")
                        st.write(f"**Model:** {row['Model Topi']} | **Total:** {row['Jumlah (Pcs)']} Pcs")
                        jml = int(row['Jumlah (Pcs)'])
                        st.caption(f"**BOM:** Kain {jml*0.1}m2 | Benang {jml*0.05} Roll | Pengait {jml*1} Pcs")
                        
                    with col_btn:
                        st.markdown("<br>", unsafe_allow_html=True) # Spasi biar tombol ke tengah
                        if st.button("✂️ Mulai Jahit", key=f"jahit_{row['ID Order']}", use_container_width=True):
                            df_bahan['Stok'] = pd.to_numeric(df_bahan['Stok'], errors='coerce').fillna(0)
                            df_bahan.loc[df_bahan['Nama Bahan'].astype(str).str.contains('Kain', case=False, na=False), 'Stok'] -= (jml*0.1)
                            df_bahan.loc[df_bahan['Nama Bahan'].astype(str).str.contains('Benang', case=False, na=False), 'Stok'] -= (jml*0.05)
                            df_bahan.loc[df_bahan['Nama Bahan'].astype(str).str.contains('Pengait', case=False, na=False), 'Stok'] -= (jml*1)
                            conn.update(worksheet="Bahan_Baku", data=df_bahan)

                            id_prod = f"PRD-{datetime.now().strftime('%H%M%S')}"
                            data_prod = pd.DataFrame([{"ID Produksi": id_prod, "ID Order": row['ID Order'], "Model Topi": row['Model Topi'], "Jumlah (Pcs)": jml, "Status Produksi": "Sedang Diproduksi"}])
                            conn.update(worksheet="Produksi", data=pd.concat([df_prod, data_prod], ignore_index=True))
                            
                            df_pem.loc[df_pem['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Sedang Diproduksi'
                            conn.update(worksheet="Pemasaran", data=df_pem)
                            st.cache_data.clear(); st.rerun()

    with tab2:
        df_wip = df_prod[df_prod['Status Produksi'] == 'Sedang Diproduksi']
        if df_wip.empty:
            st.info("Tidak ada topi yang sedang dijahit.")
        else:
            for index, row in df_wip.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"⚙️ **{row['ID Produksi']}** | Model: {row['Model Topi']} | Jumlah: {row['Jumlah (Pcs)']} Pcs")
                    with c2:
                        if st.button("✅ Lulus QC", key=f"qc_{row['ID Produksi']}", use_container_width=True):
                            try:
                                jml, model_topi = int(row['Jumlah (Pcs)']), str(row['Model Topi'])
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
                                st.cache_data.clear(); st.rerun()
                            except Exception as e: st.error(e)