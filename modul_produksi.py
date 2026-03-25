import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pem, df_prod, df_bahan, df_jadi, conn):
    st.markdown("## 🏭 Dapur Produksi (PPIC & Alur Pabrik)")
    
    # --- PENGAMANAN DATA KOLOM ---
    df_bahan['Stok'] = pd.to_numeric(df_bahan['Stok'], errors='coerce').fillna(0)
    
    # --- MINI DASHBOARD PRODUKSI ---
    antrean = len(df_pem[df_pem['Status Validasi'] == 'Siap Produksi'])
    wip = len(df_prod[df_prod['Status Produksi'].isin(['Potong Selesai', 'Bordir Selesai', 'Jahit Selesai', 'Siap QC'])])
    
    c1, c2 = st.columns(2)
    c1.metric("📥 Menunggu Potong Bahan", f"{antrean} Batch")
    c2.metric("⚙️ Sedang Dalam Pabrik (WIP)", f"{wip} Batch")
    st.divider()

    # --- 5 TAB STASIUN KERJA PABRIK ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✂️ 1. Persiapan & Potong", 
        "🎨 2. Bordir & Sablon", 
        "🧵 3. Proses Jahit", 
        "🧢 4. Aksesoris", 
        "🔎 5. QC & Gudang"
    ])

    # ==========================================
    # TAB 1: PERSIAPAN & PEMOTONGAN BAHAN
    # ==========================================
    with tab1:
        st.markdown("### ✂️ Stasiun 1: Pemotongan Bahan Baku")
        df_antrean = df_pem[df_pem['Status Validasi'] == 'Siap Produksi']
        
        if df_antrean.empty:
            st.info("Tidak ada antrean pesanan baru.")
        else:
            for index, row in df_antrean.iterrows():
                with st.container(border=True): 
                    col_img, col_desc, col_action = st.columns([1.5, 2, 2])
                    
                    with col_img:
                        path_gambar = os.path.join("desain_topi", str(row['File Desain']))
                        if os.path.exists(path_gambar):
                            st.image(path_gambar, use_container_width=True)
                        else:
                            st.info("🖼️ Gambar Tidak Ditemukan")
                            
                    with col_desc:
                        st.markdown(f"#### {row['ID Order']} - {row['Nama Klien']}")
                        st.write(f"**Model:** {row['Model Topi']} | **Total:** {row['Jumlah (Pcs)']} Pcs")
                        jml = int(row['Jumlah (Pcs)'])
                        butuh_kain = jml * 0.1
                        butuh_benang = jml * 0.05
                        butuh_pengait = jml * 1
                        st.caption(f"**BOM (Kebutuhan):**\n- Kain {butuh_kain} m2\n- Benang {butuh_benang} Roll\n- Pengait {butuh_pengait} Pcs")
                        
                    with col_action:
                        # Logika Cek Stok
                        id_order = row['ID Order']
                        
                        # Inisialisasi state tombol Cek
                        if f"cek_{id_order}" not in st.session_state:
                            st.session_state[f"cek_{id_order}"] = False
                            
                        st.write("**Validasi Material:**")
                        if st.button("🔍 Cek Ketersediaan Bahan", key=f"btn_cek_{id_order}", use_container_width=True):
                            st.session_state[f"cek_{id_order}"] = True
                            st.rerun()

                        # Jika tombol cek sudah ditekan, tampilkan hasilnya
                        if st.session_state[f"cek_{id_order}"]:
                            # Ambil stok saat ini
                            stok_kain = df_bahan.loc[df_bahan['Nama Bahan'].astype(str).str.contains('Kain', case=False, na=False), 'Stok'].sum()
                            stok_benang = df_bahan.loc[df_bahan['Nama Bahan'].astype(str).str.contains('Benang', case=False, na=False), 'Stok'].sum()
                            stok_pengait = df_bahan.loc[df_bahan['Nama Bahan'].astype(str).str.contains('Pengait', case=False, na=False), 'Stok'].sum()
                            
                            ok_kain = stok_kain >= butuh_kain
                            ok_benang = stok_benang >= butuh_benang
                            ok_pengait = stok_pengait >= butuh_pengait
                            
                            # Tampilkan Checklist
                            st.markdown(f"""
                            * {'✅' if ok_kain else '❌'} Kain ({stok_kain}/{butuh_kain} m2)
                            * {'✅' if ok_benang else '❌'} Benang ({stok_benang}/{butuh_benang} Roll)
                            * {'✅' if ok_pengait else '❌'} Pengait ({stok_pengait}/{butuh_pengait} Pcs)
                            """)
                            
                            if ok_kain and ok_benang and ok_pengait:
                                st.success("Bahan Lengkap!")
                                if st.button("✂️ Eksekusi Potong Bahan", key=f"potong_{id_order}", type="primary", use_container_width=True):
                                    # Potong Bahan
                                    df_bahan.loc[df_bahan['Nama Bahan'].astype(str).str.contains('Kain', case=False, na=False), 'Stok'] -= butuh_kain
                                    df_bahan.loc[df_bahan['Nama Bahan'].astype(str).str.contains('Benang', case=False, na=False), 'Stok'] -= butuh_benang
                                    df_bahan.loc[df_bahan['Nama Bahan'].astype(str).str.contains('Pengait', case=False, na=False), 'Stok'] -= butuh_pengait
                                    conn.update(worksheet="Bahan_Baku", data=df_bahan)

                                    # Masukkan ke Produksi
                                    id_prod = f"PRD-{datetime.now().strftime('%H%M%S')}"
                                    data_prod = pd.DataFrame([{"ID Produksi": id_prod, "ID Order": id_order, "Model Topi": row['Model Topi'], "Jumlah (Pcs)": jml, "Status Produksi": "Potong Selesai"}])
                                    conn.update(worksheet="Produksi", data=pd.concat([df_prod, data_prod], ignore_index=True))
                                    
                                    # Update Pemasaran
                                    df_pem.loc[df_pem['ID Order'] == id_order, 'Status Validasi'] = 'Sedang Diproduksi'
                                    conn.update(worksheet="Pemasaran", data=df_pem)
                                    
                                    st.session_state[f"cek_{id_order}"] = False # Reset
                                    st.cache_data.clear(); st.rerun()
                            else:
                                st.error("Bahan Kurang! Hubungi Gudang.")

    # FUNGSI BANTUAN UNTUK TAB 2-5 (Menarik data Pemasaran)
    def get_info_order(id_order):
        match = df_pem[df_pem['ID Order'] == id_order]
        if not match.empty:
            return match.iloc[0]['Nama Klien'], match.iloc[0]['File Desain']
        return "Unknown Klien", "None"

    # ==========================================
    # TAB 2: BORDIR & SABLON
    # ==========================================
    with tab2:
        st.markdown("### 🎨 Stasiun 2: Bordir & Sablon")
        df_bordir = df_prod[df_prod['Status Produksi'] == 'Potong Selesai']
        
        if df_bordir.empty: st.info("Tidak ada topi di stasiun Bordir.")
        for index, row in df_bordir.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 2, 1])
                klien, foto = get_info_order(row['ID Order'])
                with c1: st.image(os.path.join("desain_topi", str(foto))) if os.path.exists(os.path.join("desain_topi", str(foto))) else st.write("No Image")
                with c2: st.markdown(f"**{row['ID Produksi']}**\n\nKlien: {klien}\nModel: {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                with c3:
                    st.write("<br>", unsafe_allow_html=True)
                    if st.button("🎨 Selesai Bordir", key=f"bdr_{row['ID Produksi']}", use_container_width=True):
                        df_prod.loc[df_prod['ID Produksi'] == row['ID Produksi'], 'Status Produksi'] = 'Bordir Selesai'
                        conn.update(worksheet="Produksi", data=df_prod)
                        st.cache_data.clear(); st.rerun()

    # ==========================================
    # TAB 3: PROSES JAHIT
    # ==========================================
    with tab3:
        st.markdown("### 🧵 Stasiun 3: Penjahitan Topi")
        df_jahit = df_prod[df_prod['Status Produksi'] == 'Bordir Selesai']
        
        if df_jahit.empty: st.info("Tidak ada topi di stasiun Jahit.")
        for index, row in df_jahit.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 2, 1])
                klien, foto = get_info_order(row['ID Order'])
                with c1: st.image(os.path.join("desain_topi", str(foto))) if os.path.exists(os.path.join("desain_topi", str(foto))) else st.write("No Image")
                with c2: st.markdown(f"**{row['ID Produksi']}**\n\nKlien: {klien}\nModel: {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                with c3:
                    st.write("<br>", unsafe_allow_html=True)
                    if st.button("🧵 Selesai Jahit", key=f"jht_{row['ID Produksi']}", use_container_width=True):
                        df_prod.loc[df_prod['ID Produksi'] == row['ID Produksi'], 'Status Produksi'] = 'Jahit Selesai'
                        conn.update(worksheet="Produksi", data=df_prod)
                        st.cache_data.clear(); st.rerun()

    # ==========================================
    # TAB 4: PASANG AKSESORIS
    # ==========================================
    with tab4:
        st.markdown("### 🧢 Stasiun 4: Pemasangan Aksesoris (Kancing, Pengait, Label)")
        df_aksesoris = df_prod[df_prod['Status Produksi'] == 'Jahit Selesai']
        
        if df_aksesoris.empty: st.info("Tidak ada topi di stasiun Aksesoris.")
        for index, row in df_aksesoris.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 2, 1])
                klien, foto = get_info_order(row['ID Order'])
                with c1: st.image(os.path.join("desain_topi", str(foto))) if os.path.exists(os.path.join("desain_topi", str(foto))) else st.write("No Image")
                with c2: st.markdown(f"**{row['ID Produksi']}**\n\nKlien: {klien}\nModel: {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                with c3:
                    st.write("<br>", unsafe_allow_html=True)
                    if st.button("🧢 Selesai Aksesoris", key=f"aks_{row['ID Produksi']}", use_container_width=True):
                        df_prod.loc[df_prod['ID Produksi'] == row['ID Produksi'], 'Status Produksi'] = 'Siap QC'
                        conn.update(worksheet="Produksi", data=df_prod)
                        st.cache_data.clear(); st.rerun()

    # ==========================================
    # TAB 5: QC & GUDANG BARANG JADI
    # ==========================================
    with tab5:
        st.markdown("### 🔎 Stasiun 5: Quality Control (QC) & Packing")
        df_qc = df_prod[df_prod['Status Produksi'] == 'Siap QC']
        
        if df_qc.empty: st.info("Tidak ada topi yang menunggu QC.")
        for index, row in df_qc.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 2, 1])
                klien, foto = get_info_order(row['ID Order'])
                with c1: st.image(os.path.join("desain_topi", str(foto))) if os.path.exists(os.path.join("desain_topi", str(foto))) else st.write("No Image")
                with c2: st.markdown(f"**{row['ID Produksi']}**\n\nKlien: {klien}\nModel: {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                with c3:
                    st.write("<br>", unsafe_allow_html=True)
                    if st.button("✅ Lulus QC & Masuk Gudang", key=f"qc_{row['ID Produksi']}", type="primary", use_container_width=True):
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
                            df_pem.loc[df_pem['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Selesai & Masuk Gudang'
                            conn.update(worksheet="Pemasaran", data=df_pem)
                            st.cache_data.clear(); st.rerun()
                        except Exception as e: st.error(e)