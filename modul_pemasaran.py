import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pem, df_produk, conn):
    # (Judul double sudah dihapus dari sini)
    
    # --- SISTEM NOTIFIKASI SETELAH RESET FORM ---
    if st.session_state.get('notif_sukses'):
        st.success(st.session_state['notif_sukses'])
        st.session_state['notif_sukses'] = "" # Kosongkan lagi setelah ditampilkan

    # --- MINI DASHBOARD PEMASARAN ---
    total_order = len(df_pem)
    pending = len(df_pem[df_pem['Status Validasi'] == 'Menunggu Pembayaran']) if not df_pem.empty else 0
    total_produk = len(df_produk) if not df_produk.empty else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🛒 Total Pesanan Klien", f"{total_order} Order")
    c2.metric("⏳ Menunggu Pembayaran", f"{pending} Order", delta="- Action Needed", delta_color="inverse")
    c3.metric("📦 Master Data Produk", f"{total_produk} Varian Topi")
    st.divider()

    # --- 3 TAB TERPISAH ---
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
                # KITA KASIH "key" DI SETIAP INPUT BIAR BISA DI-RESET NANTI
                nama_klien = st.text_input("Nama Klien / Instansi", placeholder="Misal: PT Maju Jaya", key="in_nama")
                daftar_topi = df_produk["Model Topi"].tolist()
                model_topi = st.selectbox("Pilih Model Topi", daftar_topi, key="in_model")
                jumlah = st.number_input("Jumlah (Pcs)", min_value=1, value=50, key="in_jumlah")
                
            with col_kanan:
                file_desain = st.file_uploader("Upload Desain Topi (JPG/PNG)", type=["jpg", "png"], key="in_file")
                
                # Logika Auto-Pricing Live
                harga_satuan = df_produk.loc[df_produk['Model Topi'] == model_topi, 'Harga Satuan (Rp)'].values[0]
                total_harga_otomatis = float(harga_satuan) * jumlah
                st.info(f"💡 **Info Harga:** Rp {float(harga_satuan):,.0f} / Pcs")
                st.success(f"💰 **TOTAL TAGIHAN: Rp {total_harga_otomatis:,.0f}**")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Simpan & Teruskan ke Keuangan", use_container_width=True):
                if nama_klien == "":
                    st.error("⚠️ Nama Klien harus diisi!")
                else:
                    with st.spinner("🚀 Sedang menyimpan pesanan..."):
                        id_order = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        nama_file_simpan = "Tidak Ada Desain"
                        
                        if file_desain:
                            os.makedirs("desain_topi", exist_ok=True)
                            nama_file_simpan = f"{id_order}_{file_desain.name}"
                            with open(os.path.join("desain_topi", nama_file_simpan), "wb") as f:
                                f.write(file_desain.getbuffer())

                        data_baru = pd.DataFrame([{
                            "ID Order": id_order, "Tanggal": datetime.now().strftime("%Y-%m-%d"), 
                            "Nama Klien": nama_klien, "Model Topi": model_topi, "Jumlah (Pcs)": jumlah, 
                            "Total Harga": total_harga_otomatis, "File Desain": nama_file_simpan, 
                            "Status Validasi": "Menunggu Pembayaran"
                        }])
                        conn.update(worksheet="Pemasaran", data=pd.concat([df_pem, data_baru], ignore_index=True))
                        st.cache_data.clear()
                        
                        # --- JURUS RESET FORM ---
                        # Kita hapus memori inputan ini dari server sebelum halaman refresh
                        for key in ['in_nama', 'in_model', 'in_jumlah', 'in_file']:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        # Simpan pesan sukses di memori biar ditampilin pas halamannya loading ulang
                        st.session_state['notif_sukses'] = f"✅ Pesanan dari {nama_klien} berhasil disimpan & form telah di-reset!"
                        st.rerun()

    # ==========================================
    # TAB 2: DATABASE PEMASARAN (BISA EDIT & HAPUS)
    # ==========================================
    with tab2:
        st.markdown("### 📋 Seluruh Data Pesanan Masuk")
        st.info("💡 **Tips Edit & Hapus:** Klik dua kali pada sel tabel untuk mengubah data. Untuk menghapus baris, klik kotak abu-abu di ujung paling kiri barisnya, lalu tekan tombol `Delete` di keyboard.")
        
        # Mengganti st.dataframe menjadi st.data_editor
        df_pem_edit = st.data_editor(
            df_pem, 
            use_container_width=True, 
            num_rows="dynamic", # Kunci sakti biar bisa nambah/hapus baris
            key="editor_pemasaran"
        )
        
        if st.button("💾 Simpan Perubahan Database", type="primary"):
            with st.spinner("Memperbarui database..."):
                conn.update(worksheet="Pemasaran", data=df_pem_edit)
                st.cache_data.clear()
                st.success("✅ Perubahan database berhasil disimpan ke Google Sheets!")
                st.rerun()

    # ==========================================
    # TAB 3: MASTER DATA PRODUK (BISA EDIT & HAPUS)
    # ==========================================
    with tab3:
        st.markdown("### 🗄️ Katalog Produk & Bill of Materials (BOM)")
        
        with st.form("form_tambah_produk", clear_on_submit=True):
            st.write("Tambah model topi baru di sini:")
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
                if nama_topi == "" or harga_jual <= 0:
                    st.error("Nama Topi dan Harga wajib diisi!")
                else:
                    with st.spinner("Menyimpan produk..."):
                        data_produk_baru = pd.DataFrame([{"Model Topi": nama_topi, "Kain (m2)": kebutuhan_kain, "Benang (Roll)": kebutuhan_benang, "Pengait (Pcs)": kebutuhan_pengait, "Harga Satuan (Rp)": harga_jual}])
                        conn.update(worksheet="Master_Produk", data=pd.concat([df_produk, data_produk_baru], ignore_index=True))
                        st.cache_data.clear(); st.rerun()
        
        st.divider()
        st.markdown("#### ✏️ Tabel Master Data (Edit & Hapus)")
        df_produk_edit = st.data_editor(
            df_produk, 
            use_container_width=True, 
            num_rows="dynamic", # Kunci sakti hapus baris
            key="editor_produk"
        )
        if st.button("💾 Simpan Perubahan Katalog", type="primary"):
            with st.spinner("Menyimpan..."):
                conn.update(worksheet="Master_Produk", data=df_produk_edit)
                st.cache_data.clear()
                st.success("✅ Katalog Master Produk berhasil diperbarui!")
                st.rerun()