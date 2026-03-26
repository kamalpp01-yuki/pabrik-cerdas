import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pem, df_prod, df_bahan, df_jadi, df_produk, conn): 
    st.markdown("## 🏭 Dapur Produksi (Sistem Kanban & BOM)")
    
    df_bahan['Stok'] = pd.to_numeric(df_bahan['Stok'], errors='coerce').fillna(0)
    
    # --- PENYELARASAN KOLOM BOM DINAMIS ---
    # Pastikan semua bahan yang ada di Gudang menjadi kolom di Master Produk
    bahan_gudang = df_bahan['Nama Bahan'].dropna().unique().tolist()
    for bahan in bahan_gudang:
        if bahan not in df_produk.columns:
            df_produk[bahan] = 0.0 # Bikin kolom baru otomatis jika belum ada

    # --- MINI DASHBOARD ---
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

    tab_track, tab_1, tab_2, tab_3, tab_4, tab_bom = st.tabs([
        "📊 Tracking Pesanan", "✂️ 1. Potong", "🧵 2. Jahit", "🎨 3. Bordir", "🧢 4. QC", "🗄️ Master BOM"
    ])

    # ==========================================
    # TAB TRACKING
    # ==========================================
    with tab_track:
        st.markdown("### 📡 Radar Pelacakan Pesanan")
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
        
        if len(frames) == 0: st.info("🏝️ Belum ada pesanan yang masuk lantai produksi.")
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
                        if "Antrean" in status: st.info(status); st.progress(5)
                        elif "1" in status: st.error(status); st.progress(25)
                        elif "2" in status: st.warning(status); st.progress(50)
                        elif "3" in status: st.success(status); st.progress(75)
                        else: st.success(status); st.progress(95)

    # ==========================================
    # TAB 1: CEK BAHAN & PEMOTONGAN (MESIN BOM BARU)
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
                        
                        jml = int(row['Jumlah (Pcs)'])
                        model_topi_order = str(row['Model Topi'])
                        
                        # BACA KOLOM DINAMIS
                        bom_kebutuhan = {}
                        if not df_produk.empty:
                            try:
                                resep = df_produk[df_produk['Model Topi'] == model_topi_order].iloc[0]
                                for bahan in bahan_gudang:
                                    if bahan in resep and pd.notna(resep[bahan]):
                                        try:
                                            kebutuhan_per_pcs = float(resep[bahan])
                                            if kebutuhan_per_pcs > 0:
                                                bom_kebutuhan[bahan] = kebutuhan_per_pcs * jml
                                        except: pass
                            except Exception as e: pass

                        kunci_state = f"status_cek_{row['ID Order']}"
                        kunci_btn = f"tombol_cek_{row['ID Order']}"
                        
                        if st.button("🔍 Cek Ketersediaan Bahan Baku", key=kunci_btn):
                            st.session_state[kunci_state] = True
                            
                        if st.session_state.get(kunci_state, False):
                            if len(bom_kebutuhan) == 0:
                                st.error("⚠️ Model topi ini belum punya resep BOM atau semua takaran 0!")
                                if st.button("Tutup", key=f"tutup_{row['ID Order']}"): 
                                    st.session_state[kunci_state] = False; st.rerun()
                            else:
                                st.markdown("**Kebutuhan Material dari Gudang:**")
                                semua_ok = True
                                for bahan, butuh in bom_kebutuhan.items():
                                    stok_aktual = df_bahan.loc[df_bahan['Nama Bahan'] == bahan, 'Stok'].sum() if not df_bahan.empty else 0
                                    if stok_aktual >= butuh:
                                        st.success(f"✅ {bahan}: {stok_aktual} / {butuh}")
                                    else:
                                        semua_ok = False
                                        st.error(f"❌ {bahan}: {stok_aktual} / {butuh} (KURANG!)")
                                
                                if semua_ok:
                                    st.info("🎉 Bahan baku siap! Lanjut potong.")
                                    if st.button("✂️ Potong Bahan", key=f"potong_{row['ID Order']}", use_container_width=True):
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
                                    st.error("🚨 BAHAN KURANG! Silakan Restock di Gudang.")
                                    if st.button("Batal", key=f"batal_{row['ID Order']}"): 
                                        st.session_state[kunci_state] = False; st.rerun()

    # TAB 2 JAHIT
    with tab_2:
        df_potong = df_prod[df_prod['Status Produksi'] == 'Tahap 1: Pemotongan'].copy()
        if df_potong.empty: st.info("Tidak ada topi di tahap jahit.")
        else:
            for index, row in df_potong.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"⚙️ **{row['ID Produksi']}** | Model: {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                    if c2.button("🪡 Selesai Jahit", key=f"jahit_{row['ID Produksi']}", use_container_width=True):
                        df_prod.loc[df_prod['ID Produksi'] == row['ID Produksi'], 'Status Produksi'] = 'Tahap 2: Jahit'
                        conn.update(worksheet="Produksi", data=df_prod)
                        st.cache_data.clear(); st.rerun()

    # TAB 3 BORDIR
    with tab_3:
        df_jahit = df_prod[df_prod['Status Produksi'] == 'Tahap 2: Jahit'].copy()
        if df_jahit.empty: st.info("Tidak ada topi di tahap bordir.")
        else:
            for index, row in df_jahit.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"⚙️ **{row['ID Produksi']}** | Model: {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                    if c2.button("🖌️ Selesai Bordir", key=f"bordir_{row['ID Produksi']}", use_container_width=True):
                        df_prod.loc[df_prod['ID Produksi'] == row['ID Produksi'], 'Status Produksi'] = 'Tahap 3: Bordir & Sablon'
                        conn.update(worksheet="Produksi", data=df_prod)
                        st.cache_data.clear(); st.rerun()

    # TAB 4 QC
    with tab_4:
        df_bordir = df_prod[df_prod['Status Produksi'] == 'Tahap 3: Bordir & Sablon'].copy()
        if df_bordir.empty: st.info("Tidak ada barang di QC.")
        else:
            for index, row in df_bordir.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([2.5, 1.5])
                    c1.markdown(f"⚙️ **{row['ID Produksi']}** | Model: {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                    if c2.button("✅ Lulus QC & Gudang", key=f"qc_{row['ID Produksi']}", use_container_width=True):
                        jml, model_topi = int(row['Jumlah (Pcs)']), str(row['Model Topi'])
                        if 'Stok' not in df_jadi.columns: df_jadi['Stok'] = 0
                        df_jadi['Stok'] = pd.to_numeric(df_jadi['Stok'], errors='coerce').fillna(0)
                        if model_topi in df_jadi['Model Topi'].astype(str).values:
                            df_jadi.loc[df_jadi['Model Topi'].astype(str) == model_topi, 'Stok'] += jml
                        else:
                            df_jadi = pd.concat([df_jadi, pd.DataFrame([{"Model Topi": model_topi, "Stok": jml, "Satuan": "Pcs", "Max Kapasitas": 500}])], ignore_index=True)
                        conn.update(worksheet="Barang_Jadi", data=df_jadi)
                        
                        df_prod.loc[df_prod['ID Produksi'] == row['ID Produksi'], 'Status Produksi'] = 'Selesai & Masuk Gudang'
                        conn.update(worksheet="Produksi", data=df_prod)
                        df_pem.loc[df_pem['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Selesai & Masuk Gudang'
                        conn.update(worksheet="Pemasaran", data=df_pem)
                        st.cache_data.clear(); st.rerun()

    # ==========================================
    # TAB 6: MASTER BOM & KATALOG (PINDAHAN)
    # ==========================================
    with tab_bom:
        st.markdown("### 🗄️ Master Data & Bill of Materials (BOM)")
        st.info("💡 Semua bahan baku yang terdaftar di Gudang akan otomatis menjadi kolom di tabel ini. Isi angka `0` jika bahan tersebut tidak digunakan untuk model topi terkait.")
        
        with st.form("form_tambah_produk_cepat", clear_on_submit=True):
            st.markdown("#### ✨ Buat Model Topi Baru")
            c1, c2 = st.columns(2)
            with c1: nama_topi = st.text_input("Nama Varian Topi")
            with c2: harga_jual = st.number_input("Harga Jual (Rp)", min_value=0, step=5000)
            
            if st.form_submit_button("➕ Buat Model (Atur Takaran di Tabel Bawah)"):
                if nama_topi == "" or harga_jual <= 0: st.error("Nama & Harga wajib diisi!")
                else:
                    data_baru = {"Model Topi": nama_topi, "Harga Satuan (Rp)": harga_jual}
                    for bahan in bahan_gudang: data_baru[bahan] = 0.0 # Set semua bahan ke 0
                    
                    df_produk_update = pd.concat([df_produk, pd.DataFrame([data_baru])], ignore_index=True)
                    conn.update(worksheet="Master_Produk", data=df_produk_update)
                    st.cache_data.clear(); st.rerun()
        
        st.divider()
        st.markdown("#### ✏️ Tabel Master Resep BOM")
        df_produk_edit = st.data_editor(df_produk, use_container_width=True, num_rows="dynamic", key="editor_produk")
        
        if st.button("💾 Simpan Perubahan Resep BOM", type="primary"):
            st.session_state['konfirmasi_simpan_prod'] = True
            
        if st.session_state.get('konfirmasi_simpan_prod', False):
            st.warning("Yakin simpan perubahan Katalog Produk?")
            cy, cn = st.columns(2)
            if cy.button("✅ Ya, Simpan"):
                conn.update(worksheet="Master_Produk", data=df_produk_edit)
                st.session_state['konfirmasi_simpan_prod'] = False
                st.cache_data.clear(); st.success("Tersimpan!"); st.rerun()
            if cn.button("❌ Batal"):
                st.session_state['konfirmasi_simpan_prod'] = False; st.rerun()