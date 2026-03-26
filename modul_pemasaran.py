import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pem, df_produk, conn):
    st.markdown("## 🤝 Modul Pemasaran & Order")
    
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
    tab1, tab2, tab3 = st.tabs(["📝 Form Pesanan Baru", "📋 Database Pesanan Klien", "🗄️ Master Data Produk & BOM"])

# ==========================================
    # TAB 1: FORM PESANAN (AUTO PRICING LIVE!)
    # ==========================================
    with tab1:
        if df_produk.empty:
            st.warning("⚠️ Katalog Produk masih kosong! Silakan tambah produk di Tab 'Master Data Produk' terlebih dahulu.")
        else:
            st.markdown("### ➕ Buat Pesanan Baru")
            
            # KITA HAPUS st.form DI SINI BIAR BISA LIVE UPDATE!
            col_kiri, col_kanan = st.columns(2)
            
            with col_kiri:
                nama_klien = st.text_input("Nama Klien / Instansi", placeholder="Misal: PT Maju Jaya")
                # Dropdown otomatis narik dari Master Data
                daftar_topi = df_produk["Model Topi"].tolist()
                model_topi = st.selectbox("Pilih Model Topi", daftar_topi)
                jumlah = st.number_input("Jumlah (Pcs)", min_value=1, value=50)
                
            with col_kanan:
                file_desain = st.file_uploader("Upload Desain Topi (JPG/PNG)", type=["jpg", "png"])
                
                # Logika Auto-Pricing (Sekarang langsung berubah saat diklik!)
                harga_satuan = df_produk.loc[df_produk['Model Topi'] == model_topi, 'Harga Satuan (Rp)'].values[0]
                total_harga_otomatis = float(harga_satuan) * jumlah
                
                st.info(f"💡 **Info Harga:** Rp {float(harga_satuan):,.0f} / Pcs")
                st.success(f"💰 **TOTAL TAGIHAN: Rp {total_harga_otomatis:,.0f}**")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Ganti form_submit_button jadi tombol biasa (st.button)
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
                        st.success("✅ Pesanan berhasil disimpan!")
                        st.rerun()

    # ==========================================
    # TAB 2: DATABASE PEMASARAN
    # ==========================================
    with tab2:
        st.markdown("### 📋 Seluruh Data Pesanan Masuk")
        st.dataframe(df_pem, use_container_width=True, height=400)

    # ==========================================
    # TAB 3: MASTER DATA PRODUK (MDM)
    # ==========================================
    with tab3:
        st.markdown("### 🗄️ Katalog Produk & Bill of Materials (BOM)")
        st.write("Tambah model topi baru beserta resep bahan bakunya di sini.")
        
        with st.form("form_tambah_produk", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                nama_topi = st.text_input("Nama Varian Topi", placeholder="Misal: Topi Golf")
                harga_jual = st.number_input("Harga Jual Satuan (Rp)", min_value=0, step=5000)
            with c2:
                kebutuhan_kain = st.number_input("Butuh Kain (m2) per Pcs", min_value=0.0, step=0.01, format="%.2f")
                kebutuhan_benang = st.number_input("Butuh Benang (Roll) per Pcs", min_value=0.0, step=0.01, format="%.2f")
            with c3:
                kebutuhan_pengait = st.number_input("Butuh Pengait (Pcs) per Pcs", min_value=0, step=1)
                st.markdown("<br>", unsafe_allow_html=True)
                submit_produk = st.form_submit_button("➕ Tambahkan ke Katalog", use_container_width=True)

            if submit_produk:
                if nama_topi == "" or harga_jual <= 0:
                    st.error("Nama Topi dan Harga Jual wajib diisi!")
                else:
                    with st.spinner("Menyimpan produk ke database..."):
                        data_produk_baru = pd.DataFrame([{
                            "Model Topi": nama_topi, "Kain (m2)": kebutuhan_kain, 
                            "Benang (Roll)": kebutuhan_benang, "Pengait (Pcs)": kebutuhan_pengait, 
                            "Harga Satuan (Rp)": harga_jual
                        }])
                        df_produk_update = pd.concat([df_produk, data_produk_baru], ignore_index=True)
                        conn.update(worksheet="Master_Produk", data=df_produk_update)
                        st.cache_data.clear()
                        st.success(f"✅ Produk {nama_topi} berhasil ditambahkan!")
                        st.rerun()
        
        st.divider()
        st.dataframe(df_produk, use_container_width=True)