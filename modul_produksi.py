import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pem, df_prod, df_bahan, df_jadi, df_produk, conn): 
    st.markdown("## 🏭 Dapur Produksi (Sistem Kanban)")
    
    df_bahan['Stok'] = pd.to_numeric(df_bahan['Stok'], errors='coerce').fillna(0)
    
    # --- MINI DASHBOARD KANBAN ---
    antrean = len(df_pem[df_pem['Status Validasi'] == 'Siap Produksi'])
    tahap_potong = len(df_prod[df_prod['Status Produksi'] == 'Tahap 1: Pemotongan'])
    tahap_jahit = len(df_prod[df_prod['Status Produksi'] == 'Tahap 2: Jahit'])
    tahap_bordir = len(df_prod[df_prod['Status Produksi'] == 'Tahap 3: Bordir & Sablon'])
    tahap_qc = len(df_prod[df_prod['Status Produksi'] == 'Tahap 4: Aksesoris & QC'])
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("1️⃣ Antrean", f"{antrean} Order")
    c2.metric("2️⃣ Potong", f"{tahap_potong} Order")
    c3.metric("3️⃣ Jahit", f"{tahap_jahit} Order")
    c4.metric("4️⃣ Bordir", f"{tahap_bordir} Order")
    c5.metric("5️⃣ QC Akhir", f"{tahap_qc} Order")
    st.divider()

    tab_track, tab_1, tab_2, tab_3, tab_4 = st.tabs([
        "📊 Tracking Pesanan", 
        "✂️ 1. Cek & Potong", 
        "🧵 2. Jahit", 
        "🎨 3. Bordir & Sablon", 
        "🧢 4. Aksesoris & QC"
    ])

    # ==========================================
    # TAB TRACKING
    # ==========================================
    with tab_track:
        st.markdown("### 📡 Radar Pelacakan Pesanan (Live Tracking)")
        df_siap = df_pem[df_pem['Status Validasi'] == 'Siap Produksi'].copy()
        if not df_siap.empty:
            df_siap['Status Saat Ini'] = "Antrean (Belum Dipotong)"
            df_siap['ID Produksi'] = "-" 
        
        df_wip = df_prod[df_prod['Status Produksi'] != 'Selesai & Masuk Gudang'].copy()
        if not df_wip.empty:
            df_wip['Status Saat Ini'] = df_wip['Status Produksi']
            mapping_klien = dict(zip(df_pem['ID Order'], df_pem['Nama Klien']))
            mapping_gambar = dict(zip(df_pem['ID Order'], df_pem['File Desain']))
            df_wip['Nama Klien'] = df_wip['ID Order'].map(mapping_klien)
            df_wip['File Desain'] = df_wip['ID Order'].map(mapping_gambar) 
        
        frames = []
        kolom_pilih = ['ID Order', 'ID Produksi', 'Nama Klien', 'Model Topi', 'Jumlah (Pcs)', 'Status Saat Ini', 'File Desain']
        
        if not df_siap.empty: frames.append(df_siap[kolom_pilih])
        if not df_wip.empty: frames.append(df_wip[kolom_pilih])
        
        if len(frames) == 0: st.info("🏝️ Belum ada pesanan yang masuk ke lantai produksi.")
        else:
            df_gabungan = pd.concat(frames, ignore_index=True)
            for index, row in df_gabungan.iterrows():
                with st.container(border=True):
                    col_img, c1, c2, c3 = st.columns([1, 1.5, 2, 1.5])
                    with col_img:
                        path_gambar = os.path.join("desain_topi", str(row['File Desain']))
                        if os.path.exists(path_gambar): st.image(path_gambar, use_container_width=True)
                        else: st.info("🖼️ No Image")
                    with c1:
                        st.markdown(f"**{row['ID Order']}**")
                        st.caption(f"🏢 Klien: **{row['Nama Klien']}**")
                    with c2:
                        st.write(f"🧢 **{row['Model Topi']}** ({row['Jumlah (Pcs)']} Pcs)")
                        if row['ID Produksi'] != "-": st.caption(f"⚙️ Kode Produksi: {row['ID Produksi']}")
                    with c3:
                        status = row['Status Saat Ini']
                        if "Antrean" in status:
                            st.info(f"⏳ {status}"); st.progress(5, text="Persiapan Bahan")
                        elif "1" in status:
                            st.error(f"✂️ {status}"); st.progress(25, text="Tahap 25% - Pemotongan")
                        elif "2" in status:
                            st.warning(f"🧵 {status}"); st.progress(50, text="Tahap 50% - Penjahitan")
                        elif "3" in status:
                            st.success(f"🎨 {status}"); st.progress(75, text="Tahap 75% - Bordir & Sablon")
                        else:
                            st.success(f"🧢 {status}"); st.progress(95, text="Tahap Akhir - QC & Aksesoris")

    # ==========================================
    # TAB 1: CEK BAHAN & PEMOTONGAN
    # ==========================================
    with tab_1:
        st.markdown("### 📦 Pengecekan Bahan & Pemotongan Pola")
        df_antrean = df_pem[df_pem['Status Validasi'] == 'Siap Produksi']
        
        if df_antrean.empty: st.info("Tidak ada antrean pesanan baru.")
        else:
            for index, row in df_antrean.iterrows():
                with st.container(border=True): 
                    col_img, col_desc = st.columns([1, 3])
                    with col_img:
                        path_gambar = os.path.join("desain_topi", str(row['File Desain']))
                        if os.path.exists(path_gambar): st.image(path_gambar, use_container_width=True)
                        else: st.info("🖼️ No Image")
                            
                    with col_desc:
                        st.markdown(f"#### {row['ID Order']} - {row['Nama Klien']} ({row['Jumlah (Pcs)']} Pcs)")
                        
                        # --- MESIN PENGHITUNG BOM DINAMIS (ANTI ERROR) ---
                        jml = int(row['Jumlah (Pcs)'])
                        model_topi_order = str(row['Model Topi'])
                        
                        bom_kebutuhan = {}
                        if not df_produk.empty and 'BOM' in df_produk.columns:
                            try:
                                resep = df_produk[df_produk['Model Topi'] == model_topi_order]
                                if not resep.empty:
                                    bom_str = str(resep.iloc[0]['BOM'])
                                    # Pastikan BOM tidak kosong atau NaN
                                    if pd.notna(bom_str) and bom_str.strip() not in ["", "nan", "None"]:
                                        for item in bom_str.split("|"):
                                            if ":" in item:
                                                nama_bahan, qty_bahan = item.split(":")
                                                bom_kebutuhan[nama_bahan] = float(qty_bahan) * jml
                            except Exception as e: pass

                        kunci_state = f"status_cek_{row['ID Order']}"
                        kunci_btn = f"tombol_cek_{row['ID Order']}"
                        
                        if st.button("🔍 Cek Ketersediaan Bahan Baku", key=kunci_btn):
                            st.session_state[kunci_state] = True
                            
                        if st.session_state.get(kunci_state, False):
                            st.markdown("**Status Material di Gudang:**")
                            
                            semua_ok = True
                            for bahan, butuh in bom_kebutuhan.items():
                                stok_aktual = df_bahan.loc[df_bahan['Nama Bahan'] == bahan, 'Stok'].sum() if not df_bahan.empty else 0
                                if stok_aktual >= butuh:
                                    st.success(f"✅ {bahan}: {stok_aktual} / {butuh}")
                                else:
                                    semua_ok = False
                                    st.error(f"❌ {bahan}: {stok_aktual} / {butuh} (KURANG!)")
                            
                            if len(bom_kebutuhan) > 0:
                                if semua_ok:
                                    st.info("🎉 Semua bahan baku tersedia sesuai resep! Lanjut ke pemotongan.")
                                    if st.button("✂️ Potong Bahan & Masuk Tahap Jahit", key=f"potong_{row['ID Order']}", use_container_width=True):
                                        for bahan, butuh in bom_kebutuhan.items():
                                            df_bahan.loc[df_bahan['Nama Bahan'] == bahan, 'Stok'] -= butuh
                                        conn.update(worksheet="Bahan_Baku", data=df_bahan)

                                        id_prod = f"PRD-{datetime.now().strftime('%H%M%S')}"
                                        data_prod = pd.DataFrame([{"ID Produksi": id_prod, "ID Order": row['ID Order'], "Model Topi": row['Model Topi'], "Jumlah (Pcs)": jml, "Status Produksi": "Tahap 1: Pemotongan"}])
                                        conn.update(worksheet="Produksi", data=pd.concat([df_prod, data_prod], ignore_index=True))
                                        
                                        df_pem.loc[df_pem['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Sedang Diproduksi'
                                        conn.update(worksheet="Pemasaran", data=df_pem)
                                        
                                        st.session_state[kunci_state] = False
                                        st.cache_data.clear(); st.rerun()
                                else:
                                    st.error("🚨 BAHAN BAKU KURANG! Silakan lapor dan Restock di Modul Gudang.")
                                    if st.button("Batal", key=f"batal_{row['ID Order']}"): 
                                        st.session_state[kunci_state] = False; st.rerun()
                            else:
                                st.error("⚠️ Model topi ini belum punya resep BOM di Master Produk!")
                                if st.button("Tutup", key=f"tutup_{row['ID Order']}"): 
                                    st.session_state[kunci_state] = False; st.rerun()

    # ==========================================
    # TAB 2: JAHIT
    # ==========================================
    with tab_2:
        st.markdown("### 🧵 Proses Menjahit")
        df_potong = df_prod[df_prod['Status Produksi'] == 'Tahap 1: Pemotongan'].copy()
        
        if df_potong.empty: st.info("Tidak ada topi di tahap jahit.")
        else:
            mapping_klien = dict(zip(df_pem['ID Order'], df_pem['Nama Klien']))
            mapping_gambar = dict(zip(df_pem['ID Order'], df_pem['File Desain']))
            df_potong['Nama Klien'] = df_potong['ID Order'].map(mapping_klien)
            df_potong['File Desain'] = df_potong['ID Order'].map(mapping_gambar)
            
            for index, row in df_potong.iterrows():
                with st.container(border=True):
                    col_img, col_desc, col_btn = st.columns([1, 2.5, 1])
                    with col_img:
                        path_gambar = os.path.join("desain_topi", str(row['File Desain']))
                        if os.path.exists(path_gambar): st.image(path_gambar, use_container_width=True)
                        else: st.info("🖼️ No Image")
                    with col_desc:
                        st.markdown(f"#### {row['ID Order']} - {row['Nama Klien']}")
                        st.write(f"⚙️ **{row['ID Produksi']}** | 🧢 {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                        st.caption("Status: ⏳ Siap Dijahit")
                    with col_btn:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🪡 Selesai Jahit ➡️", key=f"jahit_{row['ID Produksi']}", use_container_width=True):
                            df_prod.loc[df_prod['ID Produksi'] == row['ID Produksi'], 'Status Produksi'] = 'Tahap 2: Jahit'
                            conn.update(worksheet="Produksi", data=df_prod)
                            st.cache_data.clear(); st.rerun()

    # ==========================================
    # TAB 3: BORDIR & SABLON
    # ==========================================
    with tab_3:
        st.markdown("### 🎨 Proses Bordir & Sablon Logo")
        df_jahit = df_prod[df_prod['Status Produksi'] == 'Tahap 2: Jahit'].copy()
        
        if df_jahit.empty: st.info("Tidak ada topi di tahap bordir.")
        else:
            mapping_klien = dict(zip(df_pem['ID Order'], df_pem['Nama Klien']))
            mapping_gambar = dict(zip(df_pem['ID Order'], df_pem['File Desain']))
            df_jahit['Nama Klien'] = df_jahit['ID Order'].map(mapping_klien)
            df_jahit['File Desain'] = df_jahit['ID Order'].map(mapping_gambar)
            
            for index, row in df_jahit.iterrows():
                with st.container(border=True):
                    col_img, col_desc, col_btn = st.columns([1, 2.5, 1])
                    with col_img:
                        path_gambar = os.path.join("desain_topi", str(row['File Desain']))
                        if os.path.exists(path_gambar): st.image(path_gambar, use_container_width=True)
                        else: st.info("🖼️ No Image")
                    with col_desc:
                        st.markdown(f"#### {row['ID Order']} - {row['Nama Klien']}")
                        st.write(f"⚙️ **{row['ID Produksi']}** | 🧢 {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                        st.caption("Status: ⏳ Siap Dibordir/Sablon")
                    with col_btn:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🖌️ Selesai Bordir ➡️", key=f"bordir_{row['ID Produksi']}", use_container_width=True):
                            df_prod.loc[df_prod['ID Produksi'] == row['ID Produksi'], 'Status Produksi'] = 'Tahap 3: Bordir & Sablon'
                            conn.update(worksheet="Produksi", data=df_prod)
                            st.cache_data.clear(); st.rerun()

    # ==========================================
    # TAB 4: AKSESORIS & QC LULUS
    # ==========================================
    with tab_4:
        st.markdown("### 🧢 Pemasangan Aksesoris & Quality Control Akhir")
        df_bordir = df_prod[df_prod['Status Produksi'] == 'Tahap 3: Bordir & Sablon'].copy()
        
        if df_bordir.empty: st.info("Tidak ada barang yang siap dipasang aksesoris/QC.")
        else:
            mapping_klien = dict(zip(df_pem['ID Order'], df_pem['Nama Klien']))
            mapping_gambar = dict(zip(df_pem['ID Order'], df_pem['File Desain']))
            df_bordir['Nama Klien'] = df_bordir['ID Order'].map(mapping_klien)
            df_bordir['File Desain'] = df_bordir['ID Order'].map(mapping_gambar)
            
            for index, row in df_bordir.iterrows():
                with st.container(border=True):
                    col_img, col_desc, col_btn = st.columns([1, 2.5, 1])
                    with col_img:
                        path_gambar = os.path.join("desain_topi", str(row['File Desain']))
                        if os.path.exists(path_gambar): st.image(path_gambar, use_container_width=True)
                        else: st.info("🖼️ No Image")
                    with col_desc:
                        st.markdown(f"#### {row['ID Order']} - {row['Nama Klien']}")
                        st.write(f"⚙️ **{row['ID Produksi']}** | 🧢 {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                        st.caption("Status: ⏳ Siap Masuk QC Akhir")
                    with col_btn:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("✅ Lulus QC & Gudang", key=f"qc_{row['ID Produksi']}", use_container_width=True):
                            try:
                                jml = int(row['Jumlah (Pcs)'])
                                model_topi = str(row['Model Topi'])
                                
                                if 'Stok' not in df_jadi.columns: df_jadi['Stok'] = 0
                                df_jadi['Stok'] = pd.to_numeric(df_jadi['Stok'], errors='coerce').fillna(0)
                                
                                if model_topi in df_jadi['Model Topi'].astype(str).values:
                                    df_jadi.loc[df_jadi['Model Topi'].astype(str) == model_topi, 'Stok'] += jml
                                else:
                                    data_jadi_baru = pd.DataFrame([{"Model Topi": model_topi, "Stok": jml, "Satuan": "Pcs", "Max Kapasitas": 500}])
                                    df_jadi = pd.concat([df_jadi, data_jadi_baru], ignore_index=True)
                                conn.update(worksheet="Barang_Jadi", data=df_jadi)
                                
                                df_prod.loc[df_prod['ID Produksi'] == row['ID Produksi'], 'Status Produksi'] = 'Selesai & Masuk Gudang'
                                conn.update(worksheet="Produksi", data=df_prod)
                                
                                df_pem.loc[df_pem['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Selesai & Masuk Gudang'
                                conn.update(worksheet="Pemasaran", data=df_pem)
                                
                                st.cache_data.clear(); st.rerun()
                            except Exception as e: st.error(f"Error: {e}")