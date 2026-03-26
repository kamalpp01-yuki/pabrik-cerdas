import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pem, df_produk, conn):
    # --- SISTEM NOTIFIKASI SETELAH RESET FORM ---
    if st.session_state.get('notif_sukses'):
        st.success(st.session_state['notif_sukses'])
        st.session_state['notif_sukses'] = ""

    # --- MINI DASHBOARD PEMASARAN ---
    total_order = len(df_pem)
    pending = len(df_pem[df_pem['Status Validasi'] == 'Menunggu Pembayaran']) if not df_pem.empty else 0
    total_produk = len(df_produk) if not df_produk.empty else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🛒 Total Pesanan Klien", f"{total_order} Order")
    c2.metric("⏳ Menunggu Pembayaran", f"{pending} Order", delta="- Action Needed", delta_color="inverse")
    c3.metric("📦 Master Data Produk", f"{total_produk} Varian Topi")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📝 Form Pesanan Baru", "📋 Database Pesanan", "🗄️ Master Data & BOM"])

    # ==========================================
    # TAB 1: FORM PESANAN (AUTO PRICING & AUTO RESET)
    # ==========================================
    with tab1:
        if df_produk.empty:
            st.warning("⚠️ Katalog Produk masih kosong! Silakan tambah produk di Tab 'Master Data Produk' terlebih dahulu.")
        else:
            st.markdown("### ➕ Buat Pesanan Baru")
            col_kiri, col_kanan = st.columns(2)
            
            with col_kiri:
                nama_klien = st.text_input("Nama Klien / Instansi", placeholder="Misal: PT Maju Jaya", key="in_nama")
                daftar_topi = df_produk["Model Topi"].tolist()
                model_topi = st.selectbox("Pilih Model Topi", daftar_topi, key="in_model")
                jumlah = st.number_input("Jumlah (Pcs)", min_value=1, value=50, key="in_jumlah")
                
            with col_kanan:
                file_desain = st.file_uploader("Upload Desain Topi (JPG/PNG)", type=["jpg", "png"], key="in_file")
                harga_satuan = df_produk.loc[df_produk['Model Topi'] == model_topi, 'Harga Satuan (Rp)'].values[0]
                total_harga_otomatis = float(harga_satuan) * jumlah
                st.info(f"💡 **Info Harga:** Rp {float(harga_satuan):,.0f} / Pcs")
                st.success(f"💰 **TOTAL TAGIHAN: Rp {total_harga_otomatis:,.0f}**")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Simpan & Teruskan ke Keuangan", use_container_width=True):
                if nama_klien == "": st.error("⚠️ Nama Klien harus diisi!")
                else:
                    with st.spinner("🚀 Sedang menyimpan pesanan..."):
                        id_order = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        nama_file_simpan = "Tidak Ada Desain"
                        
                        if file_desain:
                            os.makedirs("desain_topi", exist_ok=True)
                            nama_file_simpan = f"{id_order}_{file_desain.name}"
                            with open(os.path.join("desain_topi", nama_file_simpan), "wb") as f:
                                f.write(file_desain.getbuffer())

                        data_baru = pd.DataFrame([{"ID Order": id_order, "Tanggal": datetime.now().strftime("%Y-%m-%d"), "Nama Klien": nama_klien, "Model Topi": model_topi, "Jumlah (Pcs)": jumlah, "Total Harga": total_harga_otomatis, "File Desain": nama_file_simpan, "Status Validasi": "Menunggu Pembayaran"}])
                        conn.update(worksheet="Pemasaran", data=pd.concat([df_pem, data_baru], ignore_index=True))
                        st.cache_data.clear()
                        
                        for key in ['in_nama', 'in_model', 'in_jumlah', 'in_file']:
                            if key in st.session_state: del st.session_state[key]
                        
                        st.session_state['notif_sukses'] = f"✅ Pesanan dari {nama_klien} berhasil disimpan & form telah di-reset!"
                        st.rerun()

    # ==========================================
    # TAB 2: DATABASE PEMASARAN (EFEK DOMINO)
    # ==========================================
    with tab2:
        st.markdown("### 📋 Seluruh Data Pesanan Masuk")
        st.info("💡 **Tips Anti-Panik:** Jika Anda salah menghapus baris, cukup klik di dalam tabel lalu tekan `Ctrl + Z` di keyboard untuk mengembalikannya (Undo).")
        
        df_pem_edit = st.data_editor(df_pem, use_container_width=True, num_rows="dynamic", key="editor_pemasaran")
        
        # 1. Tombol Awal (Memicu Peringatan)
        if st.button("💾 Simpan Perubahan Database", type="primary"):
            st.session_state['konfirmasi_simpan_pem'] = True

        # 2. Logika Validasi Ya/Tidak & Efek Domino
        if st.session_state.get('konfirmasi_simpan_pem', False):
            st.warning("⚠️ **KONFIRMASI PENTING:** Anda yakin ingin menyimpan? Jika ada pesanan yang dihapus atau diubah di sini, data terkait di **Produksi** dan uang di **Keuangan** juga akan ikut terhapus/berubah secara otomatis!")
            
            col_y, col_n = st.columns(2)
            if col_y.button("✅ Ya, Simpan & Sinkronkan Semua Divisi"):
                with st.spinner("🔄 Sedang menyinkronkan data Pemasaran, Produksi, dan Keuangan..."):
                    # Deteksi pesanan yang dihapus
                    pesanan_lama = set(df_pem['ID Order'])
                    pesanan_baru = set(df_pem_edit['ID Order'])
                    pesanan_dihapus = pesanan_lama - pesanan_baru

                    # Sedot data Keuangan & Produksi
                    try: df_prod_sync = conn.read(worksheet="Produksi").dropna(how="all")
                    except: df_prod_sync = pd.DataFrame()

                    try: df_uang_sync = conn.read(worksheet="Keuangan").dropna(how="all")
                    except: df_uang_sync = pd.DataFrame()

                    # CASCADING DELETE (Menghapus efek domino)
                    if pesanan_dihapus:
                        if not df_prod_sync.empty and 'ID Order' in df_prod_sync.columns:
                            df_prod_sync = df_prod_sync[~df_prod_sync['ID Order'].isin(pesanan_dihapus)]

                        if not df_uang_sync.empty and 'Keterangan' in df_uang_sync.columns:
                            # Hapus transaksi keuangan yang keterangannya mengandung ID Order yang dihapus
                            mask = df_uang_sync['Keterangan'].apply(lambda x: any(d_id in str(x) for d_id in pesanan_dihapus))
                            df_uang_sync = df_uang_sync[~mask]
                            conn.update(worksheet="Keuangan", data=df_uang_sync)

                    # CASCADING UPDATE (Mengupdate Produksi jika model/jumlah diubah)
                    if not df_prod_sync.empty and 'ID Order' in df_prod_sync.columns:
                        model_map = dict(zip(df_pem_edit['ID Order'], df_pem_edit['Model Topi']))
                        jumlah_map = dict(zip(df_pem_edit['ID Order'], df_pem_edit['Jumlah (Pcs)']))
                        
                        df_prod_sync['Model Topi'] = df_prod_sync['ID Order'].map(model_map).fillna(df_prod_sync['Model Topi'])
                        df_prod_sync['Jumlah (Pcs)'] = df_prod_sync['ID Order'].map(jumlah_map).fillna(df_prod_sync['Jumlah (Pcs)'])
                        conn.update(worksheet="Produksi", data=df_prod_sync)

                    # Simpan hasil akhir
                    conn.update(worksheet="Pemasaran", data=df_pem_edit)
                    
                    st.session_state['konfirmasi_simpan_pem'] = False
                    st.cache_data.clear()
                    st.success("✅ Perubahan tersimpan dan seluruh divisi telah disinkronkan!")
                    st.rerun()

            if col_n.button("❌ Batal"):
                st.session_state['konfirmasi_simpan_pem'] = False
                st.rerun()

    # ==========================================
    # TAB 3: MASTER DATA PRODUK
    # ==========================================
    with tab3:
        st.markdown("### 🗄️ Katalog Produk & Bill of Materials (BOM)")
        
        with st.form("form_tambah_produk", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                nama_topi = st.text_input("Nama Varian Topi")
                harga_jual = st.number_input("Harga Satuan (Rp)", min_value=0, step=5000)
            with c2:
                kebutuhan_kain = st.number_input("Kain (m2) per Pcs", min_value=0.0, step=0.01)
                kebutuhan_benang = st.number_input("Benang (Roll) per Pcs", min_value=0.0, step=0.01)
            with c3:
                kebutuhan_pengait = st.number_input("Pengait (Pcs) per Pcs", min_value=0, step=1)
                st.markdown("<br>", unsafe_allow_html=True)
                submit_produk = st.form_submit_button("➕ Tambah Produk", use_container_width=True)

            if submit_produk:
                if nama_topi == "" or harga_jual <= 0: st.error("Nama Topi dan Harga wajib diisi!")
                else:
                    with st.spinner("Menyimpan produk..."):
                        data_produk_baru = pd.DataFrame([{"Model Topi": nama_topi, "Kain (m2)": kebutuhan_kain, "Benang (Roll)": kebutuhan_benang, "Pengait (Pcs)": kebutuhan_pengait, "Harga Satuan (Rp)": harga_jual}])
                        conn.update(worksheet="Master_Produk", data=pd.concat([df_produk, data_produk_baru], ignore_index=True))
                        st.cache_data.clear(); st.rerun()
        
        st.divider()
        st.markdown("#### ✏️ Tabel Master Data (Edit & Hapus)")
        df_produk_edit = st.data_editor(df_produk, use_container_width=True, num_rows="dynamic", key="editor_produk")
        
        # Validasi juga untuk Master Produk
        if st.button("💾 Simpan Perubahan Katalog", type="primary"):
            st.session_state['konfirmasi_simpan_prod'] = True
            
        if st.session_state.get('konfirmasi_simpan_prod', False):
            st.warning("Apakah Anda yakin ingin menyimpan perubahan Katalog Produk?")
            cy, cn = st.columns(2)
            if cy.button("✅ Ya, Simpan Katalog"):
                with st.spinner("Menyimpan..."):
                    conn.update(worksheet="Master_Produk", data=df_produk_edit)
                    st.session_state['konfirmasi_simpan_prod'] = False
                    st.cache_data.clear()
                    st.success("✅ Katalog berhasil diperbarui!")
                    st.rerun()
            if cn.button("❌ Batal Simpan"):
                st.session_state['konfirmasi_simpan_prod'] = False
                st.rerun()