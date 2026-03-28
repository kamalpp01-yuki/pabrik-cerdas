import streamlit as st
import pandas as pd
from datetime import datetime

def jalankan(df_uang, df_pemasaran, conn):
    st.markdown("## 💰 ERP Keuangan & Validator Mutasi")
    
    # --- AUTO FIX KOLOM STATUS ---
    if 'Status' not in df_uang.columns:
        df_uang['Status'] = 'Valid'
    
    # Pisahkan data Valid dan Menunggu Validasi
    df_valid = df_uang[df_uang['Status'] == 'Valid'].copy()
    df_pending = df_uang[df_uang['Status'] == 'Menunggu Validasi'].copy()
    
    # Hitung Saldo Kas HANYA dari uang yang sudah Valid
    df_valid['Pemasukan (Rp)'] = pd.to_numeric(df_valid['Pemasukan (Rp)'], errors='coerce').fillna(0)
    df_valid['Pengeluaran (Rp)'] = pd.to_numeric(df_valid['Pengeluaran (Rp)'], errors='coerce').fillna(0)
    
    total_masuk = df_valid['Pemasukan (Rp)'].sum()
    total_keluar = df_valid['Pengeluaran (Rp)'].sum()
    saldo_kas = total_masuk - total_keluar
    
    total_menunggu = pd.to_numeric(df_pending['Pemasukan (Rp)'], errors='coerce').fillna(0).sum() if not df_pending.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("💵 Saldo Kas Bersih (Valid)", f"Rp {saldo_kas:,.0f}".replace(",", "."))
    c2.metric("📉 Total Pengeluaran", f"Rp {total_keluar:,.0f}".replace(",", "."))
    c3.metric("⏳ Uang Menunggu Validasi", f"Rp {total_menunggu:,.0f}".replace(",", "."), delta="Cek Mutasi Bank", delta_color="inverse")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["🛡️ Validasi Pembayaran Masuk", "📖 Buku Kas Umum", "📤 Input Pengeluaran Pabrik"])

    # ==========================================
    # TAB 1: RUANG TUNGGU VALIDATOR
    # ==========================================
    with tab1:
        st.markdown("### 🛡️ Menunggu Validasi Akuntan")
        st.info("💡 Pastikan cek mutasi Rekening BCA/Mandiri pabrik. Jika uang sudah benar-benar masuk, klik 'Validasi'.")
        
        if df_pending.empty:
            st.success("🏝️ Semua pembayaran sudah tervalidasi. Tidak ada antrean.")
        else:
            for idx, row in df_pending.iterrows():
                with st.container(border=True):
                    col_info, col_btn = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"**Tanggal:** {row['Tanggal']}")
                        st.write(f"📝 **Keterangan:** {row['Keterangan']}")
                        st.markdown(f"💰 **Nominal Transfer:** <span style='color:#00ADB5; font-size:20px; font-weight:bold;'>Rp {float(row['Pemasukan (Rp)']):,.0f}</span>", unsafe_allow_html=True)
                        
                    with col_btn:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("✅ Validasi Uang Masuk", key=f"val_{idx}", use_container_width=True, type="primary"):
                            with st.spinner("Memvalidasi dana dan meneruskan ke Produksi..."):
                                # 1. Ubah status Keuangan
                                df_uang.loc[idx, 'Status'] = 'Valid'
                                conn.update(worksheet="Keuangan", data=df_uang)
                                
                                # 2. LOGIKA BARU: Pelacak ID Order yang LEBIH KUAT
                                ket = str(row['Keterangan'])
                                if "ORD-" in ket:
                                    try:
                                        # Pakai Regex atau ekstraksi substring yang aman
                                        # Cari kata yang mulai dengan ORD- sampai spasi atau tanda kurung berikutnya
                                        import re
                                        match = re.search(r'ORD-\d+', ket)
                                        
                                        if match:
                                            id_order_pasti = match.group()
                                            
                                            # Paksa hapus spasi di database pemasaran biar cocok 100%
                                            df_pemasaran['ID Order'] = df_pemasaran['ID Order'].astype(str).str.strip()
                                            
                                            if id_order_pasti in df_pemasaran['ID Order'].values:
                                                # Tembak statusnya jadi "Sedang Diproses" (Ini Trigger untuk Produksi)
                                                df_pemasaran.loc[df_pemasaran['ID Order'] == id_order_pasti, 'Status Validasi'] = 'Sedang Diproses'
                                                conn.update(worksheet="Pemasaran", data=df_pemasaran)
                                            else:
                                                st.warning(f"⚠️ Uang tervalidasi, TAPI sistem gagal menemukan {id_order_pasti} di Modul Pemasaran. Harap ubah statusnya ke 'Sedang Diproses' manual di GSheets.")
                                        else:
                                            st.warning("⚠️ Format ID Order di Keterangan tidak standar. Pesanan tidak bisa otomatis diteruskan ke Produksi.")
                                            
                                    except Exception as e:
                                        st.error(f"Error pelacakan ID: {e}")
                                
                                st.cache_data.clear()
                                st.success("✅ Dana divalidasi & Status pesanan berhasil diupdate!")
                                st.rerun()
                        
                        if st.button("❌ Tolak (Gagal Bayar)", key=f"tolak_{idx}", use_container_width=True):
                            df_uang = df_uang.drop(idx)
                            conn.update(worksheet="Keuangan", data=df_uang)
                            st.cache_data.clear()
                            st.rerun()

    # ==========================================
    # TAB 2: BUKU KAS UMUM (HANYA YANG VALID)
    # ==========================================
    with tab2:
        st.markdown("### 📖 Buku Kas Terverifikasi")
        st.dataframe(df_valid, use_container_width=True, hide_index=True)

    # ==========================================
    # TAB 3: INPUT PENGELUARAN PABRIK
    # ==========================================
    with tab3:
        st.markdown("### 📤 Catat Pengeluaran Operasional")
        with st.form("form_pengeluaran", clear_on_submit=True):
            ket_keluar = st.text_input("Keterangan Pengeluaran", placeholder="Misal: Bayar Listrik, Gaji Penjahit, Beli Snack")
            nominal_keluar = st.number_input("Nominal (Rp)", min_value=1000, step=10000)
            
            if st.form_submit_button("💸 Simpan Pengeluaran", use_container_width=True):
                if ket_keluar == "": st.error("Keterangan tidak boleh kosong!")
                else:
                    new_keluar = pd.DataFrame([{
                        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                        "Keterangan": ket_keluar,
                        "Pemasukan (Rp)": 0,
                        "Pengeluaran (Rp)": nominal_keluar,
                        "Status": "Valid"
                    }])
                    df_uang_update = pd.concat([df_uang, new_keluar], ignore_index=True)
                    conn.update(worksheet="Keuangan", data=df_uang_update)
                    st.success("✅ Pengeluaran berhasil dicatat!")
                    st.cache_data.clear(); st.rerun()