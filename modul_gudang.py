import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pem, df_bahan, conn):
    st.markdown("## 📦 Modul Gudang & Distribusi Terpadu")
    
    # --- PENGELOMPOKAN DATA BERDASARKAN STATUS ---d
    df_siap_kirim = df_pem[df_pem['Status Validasi'] == 'Selesai & Masuk Gudang'].copy()
    df_sedang_dikirim = df_pem[df_pem['Status Validasi'] == 'Pesanan Dikirim'].copy()
    
    total_stok_jadi = pd.to_numeric(df_siap_kirim['Jumlah (Pcs)'], errors='coerce').fillna(0).sum() if not df_siap_kirim.empty else 0
    total_di_jalan = len(df_sedang_dikirim)

    df_bahan['Stok'] = pd.to_numeric(df_bahan['Stok'], errors='coerce').fillna(0)
    bahan_menipis = len(df_bahan[df_bahan['Stok'] < 20])
    
    # --- MINI DASHBOARD ---
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Gudang Barang Jadi", f"{total_stok_jadi:,.0f} Pcs")
    c2.metric("🚚 Sedang Distribusi", f"{total_di_jalan} Order", delta="Di Perjalanan")
    c3.metric("⚠️ Material Perlu Restock", f"{bahan_menipis} Item", delta="- Cek Bahan!", delta_color="inverse")
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🛒 Restock & Tambah Bahan", 
        "🏭 Kapasitas Bahan Baku", 
        "🛍️ Gudang Barang Jadi", 
        "🚚 Distribusi Pengiriman"
    ])

    # ==========================================
    # TAB 1: RESTOCK & TAMBAH BAHAN BARU
    # ==========================================
    with tab1:
        col_baru, col_restock = st.columns(2)
        
        with col_baru:
            st.markdown("#### ✨ Daftarkan Jenis Bahan Baru")
            with st.form("form_bahan_baru", clear_on_submit=True):
                nama_b_baru = st.text_input("Nama Material Baru", placeholder="Misal: Kancing Besi")
                satuan_baru = st.text_input("Satuan", placeholder="Misal: Pcs / Kg / Roll")
                max_kap = st.number_input("Kapasitas Max Gudang", min_value=1, value=1000)
                
                if st.form_submit_button("➕ Daftarkan ke Gudang", use_container_width=True):
                    if nama_b_baru == "" or satuan_baru == "":
                        st.error("Nama dan Satuan wajib diisi!")
                    elif not df_bahan.empty and nama_b_baru in df_bahan['Nama Bahan'].values:
                        st.error("Bahan ini sudah ada di gudang!")
                    else:
                        data_bahan_baru = pd.DataFrame([{"Nama Bahan": nama_b_baru, "Stok": 0, "Satuan": satuan_baru, "Max Kapasitas": max_kap}])
                        conn.update(worksheet="Bahan_Baku", data=pd.concat([df_bahan, data_bahan_baru], ignore_index=True))
                        st.cache_data.clear(); st.success(f"✅ {nama_b_baru} berhasil didaftarkan!"); st.rerun()

        with col_restock:
            st.markdown("#### 📥 Restock Bahan (Beli)")
            with st.form("form_beli_bahan", clear_on_submit=True):
                if df_bahan.empty: 
                    st.warning("Belum ada bahan terdaftar.")
                    st.form_submit_button("🛒 Beli & Restock", disabled=True)
                else:
                    pilihan_bahan = st.selectbox("Pilih Material", df_bahan["Nama Bahan"].tolist())
                    tambah_stok = st.number_input("Jumlah Masuk", min_value=1.0, value=10.0, step=1.0)
                    harga_beli = st.number_input("Total Harga Beli (Rp)", min_value=0, step=10000)
                    
                    if st.form_submit_button("🛒 Beli & Restock", use_container_width=True):
                        df_bahan.loc[df_bahan['Nama Bahan'] == pilihan_bahan, 'Stok'] += tambah_stok
                        conn.update(worksheet="Bahan_Baku", data=df_bahan)
                        
                        if harga_beli > 0:
                            try: 
                                df_uang = conn.read(worksheet="Keuangan").dropna(how="all")
                            except Exception: 
                                df_uang = pd.DataFrame(columns=["Tanggal", "Keterangan", "Pemasukan (Rp)", "Pengeluaran (Rp)"])
                            
                            data_uang_baru = pd.DataFrame([{
                                "Tanggal": datetime.now().strftime("%Y-%m-%d"), 
                                "Keterangan": f"Beli {tambah_stok} {pilihan_bahan}", 
                                "Pemasukan (Rp)": 0, 
                                "Pengeluaran (Rp)": harga_beli
                            }])
                            df_uang_update = pd.concat([df_uang, data_uang_baru], ignore_index=True)
                            conn.update(worksheet="Keuangan", data=df_uang_update)
                        
                        st.cache_data.clear(); st.success(f"✅ {tambah_stok} {pilihan_bahan} masuk gudang!"); st.rerun()

    # ==========================================
    # TAB 2: KAPASITAS BAHAN BAKU
    # ==========================================
    with tab2:
        st.markdown("### 📊 Status Real-Time Gudang Material")
        if df_bahan.empty:
            st.info("Gudang bahan baku masih kosong.")
        else:
            df_bahan['Max Kapasitas'] = pd.to_numeric(df_bahan['Max Kapasitas'], errors='coerce').fillna(1000)
            for index, row in df_bahan.iterrows():
                stok, maks = row['Stok'], row['Max Kapasitas']
                persentase = min(stok / maks, 1.0) if maks > 0 else 0
                if stok <= 0: st.error(f"🚨 HABIS: {row['Nama Bahan']} kosong!")
                elif persentase < 0.1: st.warning(f"⚠️ Menipis: {row['Nama Bahan']} (Sisa {stok})")
                st.progress(persentase, text=f"{row['Nama Bahan']}: {stok}/{maks} {row['Satuan']}")
            st.dataframe(df_bahan, use_container_width=True)

    # ==========================================
    # TAB 3: GUDANG BARANG JADI (PER KLIEN)
    # ==========================================
    with tab3:
        st.markdown("### 🛍️ Daftar Pesanan Selesai (Menunggu Kurir)")
        st.info("💡 Klik tombol Kirim Pesanan jika barang sudah diangkut oleh kurir/ekspedisi.")
        
        if df_siap_kirim.empty:
            st.success("🏝️ Gudang barang jadi kosong. Belum ada orderan yang antre untuk dikirim.")
        else:
            for index, row in df_siap_kirim.iterrows():
                with st.container(border=True):
                    col_img, col_desc, col_btn = st.columns([1, 2.5, 1])
                    
                    with col_img:
                        path_gambar = os.path.join("desain_topi", str(row['File Desain']))
                        if os.path.exists(path_gambar): 
                            st.image(path_gambar, use_container_width=True)
                        else: 
                            st.info("🖼️ No Image")
                            
                    with col_desc:
                        st.markdown(f"#### {row['ID Order']}")
                        st.write(f"🏢 **Klien / Instansi:** {row['Nama Klien']}")
                        st.write(f"🧢 **Isi Paket:** {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                        st.caption("Status: 📦 Berada di Gudang")
                        
                    with col_btn:
                        st.markdown("<br>", unsafe_allow_html=True)
                        # Tombol pindah ke Distribusi
                        if st.button("🚚 Kirim Pesanan", key=f"kirim_{row['ID Order']}", use_container_width=True, type="primary"):
                            with st.spinner("Memproses ke bagian distribusi..."):
                                df_pem.loc[df_pem['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Pesanan Dikirim'
                                conn.update(worksheet="Pemasaran", data=df_pem)
                                st.cache_data.clear()
                                st.rerun()

    # ==========================================
    # TAB 4: DISTRIBUSI PENGIRIMAN (FITUR BARU)
    # ==========================================
    with tab4:
        st.markdown("### 🚚 Radar Distribusi & Pengiriman")
        st.info("💡 Orderan di bawah ini sedang dalam perjalanan ke alamat klien. Klik Selesaikan jika klien sudah menerima barang.")
        
        if df_sedang_dikirim.empty:
            st.success("🏝️ Tidak ada orderan yang sedang dalam perjalanan.")
        else:
            for index, row in df_sedang_dikirim.iterrows():
                with st.container(border=True):
                    col_img, col_desc, col_btn = st.columns([1, 2.5, 1])
                    
                    with col_img:
                        path_gambar = os.path.join("desain_topi", str(row['File Desain']))
                        if os.path.exists(path_gambar): 
                            st.image(path_gambar, use_container_width=True)
                        else: 
                            st.info("🖼️ No Image")
                            
                    with col_desc:
                        st.markdown(f"#### {row['ID Order']}")
                        st.write(f"🏢 **Tujuan:** {row['Nama Klien']}")
                        st.write(f"📦 **Paket:** {row['Model Topi']} ({row['Jumlah (Pcs)']} Pcs)")
                        st.caption("Status: 💨 Sedang Di Jalan / Di Ekspedisi")
                        
                    with col_btn:
                        st.markdown("<br>", unsafe_allow_html=True)
                        # Tombol penyelesaian akhir!
                        if st.button("✅ Selesaikan (Diterima)", key=f"selesai_{row['ID Order']}", use_container_width=True):
                            with st.spinner("Menyelesaikan pesanan..."):
                                df_pem.loc[df_pem['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Terkirim'
                                conn.update(worksheet="Pemasaran", data=df_pem)
                                st.cache_data.clear()
                                st.success("Pesanan berhasil diselesaikan!")
                                st.rerun()