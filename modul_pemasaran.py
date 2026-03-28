import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pem, df_produk, conn): 
    # --- SISTEM NOTIFIKASI ---
    if st.session_state.get('notif_sukses'):
        st.success(st.session_state['notif_sukses'])
        st.session_state['notif_sukses'] = ""

    # --- MINI DASHBOARD PEMASARAN ---
    total_order = len(df_pem)
    pending = len(df_pem[df_pem['Status Validasi'] == 'Menunggu Pembayaran']) if not df_pem.empty else 0
    
    c1, c2 = st.columns(2)
    c1.metric("🛒 Total Pesanan Masuk", f"{total_order} Order")
    c2.metric("⏳ Menunggu Pembayaran Klien", f"{pending} Order", delta="- Action Needed", delta_color="inverse")
    st.divider()

    tab1, tab2 = st.tabs(["📝 Form Order Terpadu", "📋 Database Pesanan"])

    # ==========================================
    # TAB 1: FORM PESANAN TERPADU 
    # ==========================================
    with tab1:
        if df_produk.empty:
            st.warning("⚠️ Katalog Produk kosong! Minta divisi Produksi mengisi Master BOM terlebih dahulu.")
        else:
            st.markdown("### ➕ Buat Pesanan Baru")
            st.info("💡 Formulir ini akan mendaftarkan pesanan dan klien. Pembayaran nominal dilakukan di Menu CRM.")
            
            with st.container(border=True):
                # --- BAGIAN 1: DATA KLIEN ---
                st.markdown("#### 👤 1. Informasi Klien")
                c_k1, c_k2 = st.columns(2)
                with c_k1:
                    nama_klien = st.text_input("Nama Instansi / Klien *", placeholder="Wajib Diisi", key="in_nama")
                    wa_klien = st.text_input("No. WhatsApp", placeholder="Contoh: 08123456789", key="in_wa")
                with c_k2:
                    kategori_klien = st.selectbox("Kategori Klien", ["Reguler", "VIP (Langganan)", "Corporate"], key="in_kat")
                    alamat_klien = st.text_input("Alamat Pengiriman", placeholder="Masukkan alamat lengkap", key="in_alamat")

                st.divider()

                # --- BAGIAN 2: DETAIL PESANAN ---
                st.markdown("#### 🧢 2. Detail Order")
                c_p1, c_p2 = st.columns(2)
                with c_p1:
                    daftar_topi = df_produk["Model Topi"].tolist()
                    model_topi = st.selectbox("Pilih Model Topi", daftar_topi, key="in_model")
                    jumlah = st.number_input("Jumlah (Pcs)", min_value=1, value=50, key="in_jumlah")
                with c_p2:
                    file_desain = st.file_uploader("Upload Desain", type=["jpg", "png"], key="in_file")
                    harga_satuan = df_produk.loc[df_produk['Model Topi'] == model_topi, 'Harga Satuan (Rp)'].values[0]
                    total_harga = float(harga_satuan) * jumlah
                    st.caption(f"Harga Satuan: Rp {float(harga_satuan):,.0f} / Pcs")
                
                st.divider()

                # --- BAGIAN 3: METODE PEMBAYARAN ---
                st.markdown("#### 💳 3. Kesepakatan Pembayaran")
                st.success(f"**💰 TOTAL TAGIHAN: Rp {total_harga:,.0f}**")
                
                # Cuma pilih Lunas atau DP
                metode_bayar = st.radio("Metode Pembayaran (Direncanakan):", ["Bayar Penuh (Lunas)", "Bayar Sebagian (DP)"], horizontal=True, key="in_metode")
                
                status_produksi = "Menunggu Pembayaran"
                status_bayar_awal = "Belum Bayar"
                
                st.caption("Setelah disimpan, silakan menuju Modul **CRM & Piutang** untuk mencatat nominal transfer dari Klien.")

            # --- TOMBOL SAKTI PENYIMPANAN ---
            if st.button("🚀 Simpan Pesanan & Teruskan ke CRM", use_container_width=True, type="primary"):
                if nama_klien == "": 
                    st.error("⚠️ Nama Klien harus diisi!")
                else:
                    with st.spinner("🔄 Mendistribusikan data ke Pemasaran & CRM..."):
                        # 0. Persiapan ID & File
                        id_order = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        tgl_skrg = datetime.now().strftime("%Y-%m-%d")
                        nama_file = "Tidak Ada Desain"
                        if file_desain:
                            os.makedirs("desain_topi", exist_ok=True)
                            nama_file = f"{id_order}_{file_desain.name}"
                            with open(os.path.join("desain_topi", nama_file), "wb") as f:
                                f.write(file_desain.getbuffer())

                        # 1. Update Database PEMASARAN
                        data_pem_baru = pd.DataFrame([{"ID Order": id_order, "Tanggal": tgl_skrg, "Nama Klien": nama_klien, "Model Topi": model_topi, "Jumlah (Pcs)": jumlah, "Total Harga": total_harga, "File Desain": nama_file, "Status Validasi": status_produksi}])
                        conn.update(worksheet="Pemasaran", data=pd.concat([df_pem, data_pem_baru], ignore_index=True))

                        # 2. Update Database KLIEN (CRM)
                        try: 
                            df_klien = conn.read(worksheet="Database_Klien").dropna(how="all")
                            if 'Nama Klien' not in df_klien.columns: df_klien = pd.DataFrame(columns=["Nama Klien", "No WA", "Alamat", "Kategori"])
                        except: df_klien = pd.DataFrame(columns=["Nama Klien", "No WA", "Alamat", "Kategori"])
                        
                        if df_klien.empty or nama_klien not in df_klien['Nama Klien'].values:
                            new_klien = pd.DataFrame([{"Nama Klien": nama_klien, "No WA": wa_klien, "Alamat": alamat_klien, "Kategori": kategori_klien}])
                            conn.update(worksheet="Database_Klien", data=pd.concat([df_klien, new_klien], ignore_index=True))

                        # 3. Update BUKU PIUTANG (Sebagai Tagihan Baru)
                        try: 
                            df_piutang = conn.read(worksheet="Buku_Piutang").dropna(how="all")
                            if 'ID Order' not in df_piutang.columns: df_piutang = pd.DataFrame(columns=["ID Order", "Sudah Dibayar", "Sisa Tagihan", "Status Pembayaran"])
                        except: df_piutang = pd.DataFrame(columns=["ID Order", "Sudah Dibayar", "Sisa Tagihan", "Status Pembayaran"])
                        
                        new_piutang = pd.DataFrame([{"ID Order": id_order, "Sudah Dibayar": 0, "Sisa Tagihan": total_harga, "Status Pembayaran": status_bayar_awal}])
                        conn.update(worksheet="Buku_Piutang", data=pd.concat([df_piutang, new_piutang], ignore_index=True))

                        # Bersihkan Form
                        for k in ['in_nama', 'in_wa', 'in_alamat', 'in_model', 'in_jumlah', 'in_metode', 'in_file']: 
                            if k in st.session_state: del st.session_state[k]
                        
                        st.session_state['notif_sukses'] = f"✅ Pesanan {id_order} tercatat! Silakan catat nominal uang masuk di Menu CRM & Piutang."
                        st.cache_data.clear(); st.rerun()

    # ==========================================
    # TAB 2: DATABASE PESANAN
    # ==========================================
    with tab2:
        st.markdown("### 📋 Seluruh Data Pesanan Masuk")
        st.dataframe(df_pem, use_container_width=True, hide_index=True)