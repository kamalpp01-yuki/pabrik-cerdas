import streamlit as st
import pandas as pd
from datetime import datetime

def jalankan(df_pem, df_klien, df_piutang, df_uang, conn):
    st.markdown("## 👥 Manajemen Klien, Piutang & Pembayaran")
    
    # --- 1. MESIN SINKRONISASI OTOMATIS (SALES -> PIUTANG) ---
    if not df_pem.empty:
        order_pem = set(df_pem['ID Order'])
        order_piutang = set(df_piutang['ID Order']) if not df_piutang.empty else set()
        order_baru = order_pem - order_piutang
        
        if order_baru:
            data_baru = []
            for o_id in order_baru:
                total_harga = df_pem.loc[df_pem['ID Order'] == o_id, 'Total Harga'].values[0]
                data_baru.append({
                    "ID Order": o_id,
                    "Sudah Dibayar": 0,
                    "Sisa Tagihan": total_harga,
                    "Status Pembayaran": "Belum Bayar"
                })
            df_piutang = pd.concat([df_piutang, pd.DataFrame(data_baru)], ignore_index=True)
            conn.update(worksheet="Buku_Piutang", data=df_piutang)

    # --- 2. MINI DASHBOARD CRM ---
    df_piutang['Sisa Tagihan'] = pd.to_numeric(df_piutang['Sisa Tagihan'], errors='coerce').fillna(0)
    total_piutang = df_piutang['Sisa Tagihan'].sum()
    total_klien = len(df_klien)

    c1, c2 = st.columns(2)
    c1.metric("👥 Total Klien Terdaftar", f"{total_klien} Klien/Instansi")
    c2.metric("💸 Total Tagihan di Luar (Piutang)", f"Rp {total_piutang:,.0f}".replace(",", "."), delta="- Belum Lunas", delta_color="inverse")
    st.divider()

    # --- TAMBAHAN TAB 3 UNTUK INVOICE ---
    tab1, tab2, tab3 = st.tabs(["📒 Catat Pembayaran Tagihan", "👥 Database Klien (CRM)", "🖨️ Cetak Invoice Lengkap"])

    # ==========================================
    # TAB 1: BUKU PIUTANG & PEMBAYARAN
    # ==========================================
    with tab1:
        st.markdown("### 💸 Pencatatan Uang Masuk (DP / Pelunasan)")
        
        if df_piutang.empty:
            st.info("Belum ada data order untuk ditagih.")
        else:
            df_merge = pd.merge(df_piutang, df_pem[['ID Order', 'Nama Klien', 'Total Harga']], on="ID Order", how="left")
            df_belum_lunas = df_merge[df_merge['Status Pembayaran'] != 'Lunas']
            
            col_form, col_data = st.columns([1.2, 2])
            
            with col_form:
                st.markdown("#### 💳 Proses Pembayaran")
                if df_belum_lunas.empty:
                    st.success("🎉 Luar biasa! Semua tagihan klien saat ini sudah LUNAS.")
                else:
                    daftar_tagihan = df_belum_lunas['ID Order'] + " - " + df_belum_lunas['Nama Klien']
                    pilih_order = st.selectbox("Pilih Tagihan:", daftar_tagihan)
                    
                    id_terpilih = pilih_order.split(" - ")[0]
                    data_order = df_belum_lunas[df_belum_lunas['ID Order'] == id_terpilih].iloc[0]
                    sisa_tagihan_asli = float(data_order['Sisa Tagihan'])
                    
                    st.info(
                        f"**Total Harga:** Rp {float(data_order['Total Harga']):,.0f} \n\n"
                        f"**Sudah Dibayar:** Rp {float(data_order['Sudah Dibayar']):,.0f} \n\n"
                        f"**Sisa Tagihan:** Rp {sisa_tagihan_asli:,.0f}"
                    )
                    
                    # LOGIKA BARU: Pilihan Cepat Lunas vs DP
                    tipe_bayar = st.radio("Pilih Nominal Pembayaran:", ["✅ Langsung Lunas (Sesuai Sisa Tagihan)", "✍️ Bayar Sebagian (Input DP / Cicilan)"], horizontal=True)
                    
                    with st.form("form_bayar", clear_on_submit=True):
                        if "Langsung Lunas" in tipe_bayar:
                            nominal_bayar = sisa_tagihan_asli
                            st.success(f"Uang yang akan dicatat: **Rp {nominal_bayar:,.0f}**")
                        else:
                            nominal_bayar = st.number_input("Masukkan Nominal Uang Masuk (Rp)", min_value=0.0, max_value=sisa_tagihan_asli, step=50000.0)
                        
                        st.caption("⚠️ Setelah disimpan, data akan dikirim ke Akuntan untuk Divalidasi.")
                        
                        if st.form_submit_button("🚀 Catat & Kirim ke Keuangan", type="primary", use_container_width=True):
                            if nominal_bayar > 0:
                                with st.spinner("Mencatat & Mengirim ke Ruang Tunggu Keuangan..."):
                                    # 1. Update status Piutang
                                    sudah_bayar_baru = float(data_order['Sudah Dibayar']) + nominal_bayar
                                    sisa_baru = float(data_order['Total Harga']) - sudah_bayar_baru
                                    status_baru = "Lunas" if sisa_baru <= 0 else "DP / Cicilan"
                                    
                                    df_piutang.loc[df_piutang['ID Order'] == id_terpilih, 'Sudah Dibayar'] = sudah_bayar_baru
                                    df_piutang.loc[df_piutang['ID Order'] == id_terpilih, 'Sisa Tagihan'] = sisa_baru
                                    df_piutang.loc[df_piutang['ID Order'] == id_terpilih, 'Status Pembayaran'] = status_baru
                                    conn.update(worksheet="Buku_Piutang", data=df_piutang)
                                    
                                    # 2. Kirim ke Keuangan dengan Status "Menunggu Validasi"
                                    try: 
                                        df_uang_k = conn.read(worksheet="Keuangan").dropna(how="all")
                                        if 'Status' not in df_uang_k.columns: df_uang_k['Status'] = 'Valid'
                                    except: 
                                        df_uang_k = pd.DataFrame(columns=["Tanggal", "Keterangan", "Pemasukan (Rp)", "Pengeluaran (Rp)", "Status"])
                                        
                                    new_uang = pd.DataFrame([{
                                        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                                        "Keterangan": f"Pembayaran {id_terpilih} ({status_baru})",
                                        "Pemasukan (Rp)": nominal_bayar,
                                        "Pengeluaran (Rp)": 0,
                                        "Status": "Menunggu Validasi" # <--- KUNCI PINTU VALIDATOR
                                    }])
                                    df_uang_k = pd.concat([df_uang_k, new_uang], ignore_index=True)
                                    conn.update(worksheet="Keuangan", data=df_uang_k)
                                        
                                    st.success(f"Berhasil! Rp {nominal_bayar:,.0f} sedang menunggu verifikasi Keuangan.")
                                    st.cache_data.clear()
                                    st.rerun()
                            else:
                                st.error("Nominal harus lebih besar dari 0!")

            with col_data:
                st.markdown("#### 📊 Status Tagihan Seluruh Order")
                kolom_tampil = ['ID Order', 'Nama Klien', 'Status Pembayaran', 'Total Harga', 'Sudah Dibayar', 'Sisa Tagihan']
                st.dataframe(df_merge[kolom_tampil], use_container_width=True, hide_index=True)

    # ==========================================
    # TAB 2: DATABASE KLIEN (CRM)
    # ==========================================
    with tab2:
        st.markdown("### 🏢 Buku Kontak & Profil Klien")
        col_f, col_d = st.columns([1, 2])
        
        with col_f:
            st.markdown("#### ➕ Tambah Kontak Baru")
            with st.form("form_klien", clear_on_submit=True):
                nama = st.text_input("Nama Klien / Instansi")
                wa = st.text_input("No. WhatsApp", placeholder="Contoh: 08123456789")
                alamat = st.text_area("Alamat Pengiriman")
                kategori = st.selectbox("Kategori Klien", ["Reguler", "VIP (Langganan)", "Corporate"])
                
                if st.form_submit_button("💾 Simpan Kontak", use_container_width=True):
                    if nama != "":
                        new_klien = pd.DataFrame([{"Nama Klien": nama, "No WA": wa, "Alamat": alamat, "Kategori": kategori}])
                        df_klien = pd.concat([df_klien, new_klien], ignore_index=True)
                        conn.update(worksheet="Database_Klien", data=df_klien)
                        st.success(f"Kontak {nama} berhasil disimpan!")
                        st.cache_data.clear(); st.rerun()
                    else:
                        st.error("Nama Klien wajib diisi!")
        
        with col_d:
            st.markdown("#### 📋 Daftar Klien Terdaftar")
            if df_klien.empty:
                st.info("Belum ada data klien yang terdaftar.")
            else:
                for idx, row in df_klien.iterrows():
                    with st.container(border=True):
                        c_info, c_btn = st.columns([3, 1])
                        c_info.markdown(f"**{row.get('Nama Klien', 'Tanpa Nama')}** — *( {row.get('Kategori', 'Reguler')} )*")
                        c_info.caption(f"📍 {row.get('Alamat', '-')}")
                        
                        no_wa = str(row.get('No WA', '')).replace('0', '62', 1) if str(row.get('No WA', '')).startswith('0') else str(row.get('No WA', ''))
                        if no_wa:
                            c_btn.markdown(f"<a href='https://wa.me/{no_wa}' target='_blank'><button style='width:100%; border-radius:5px; background-color:#25D366; color:white; border:none; padding:8px; font-weight:bold; cursor:pointer;'>💬 Chat WA</button></a>", unsafe_allow_html=True)
                        else:
                            c_btn.button("No WA Kosong", disabled=True, key=f"wa_{idx}")

    # ==========================================
    # TAB 3: CETAK INVOICE OTOMATIS (PINDAHAN)
    # ==========================================
    with tab3:
        st.markdown("### 🖨️ Cetak Invoice & Nota Pembayaran")
        if df_pem.empty:
            st.info("Belum ada data pesanan untuk dicetak.")
        else:
            daftar_order = df_pem['ID Order'].dropna().tolist()
            pilih_order = st.selectbox("Pilih ID Order yang akan dicetak:", daftar_order, key="pilih_inv")
            
            if pilih_order:
                data_order = df_pem[df_pem['ID Order'] == pilih_order].iloc[0]
                
                # Sinkronkan data dari Piutang
                try: 
                    data_piutang = df_piutang[df_piutang['ID Order'] == pilih_order].iloc[0]
                    dp_inv = float(data_piutang['Sudah Dibayar'])
                    sisa_inv = float(data_piutang['Sisa Tagihan'])
                    status_inv = data_piutang['Status Pembayaran']
                except:
                    dp_inv, sisa_inv, status_inv = 0, float(data_order['Total Harga']), "Belum Bayar"

                html_invoice = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 40px; color: #333; }}
                        .invoice-box {{ max-width: 800px; margin: auto; padding: 30px; border: 1px solid #eee; box-shadow: 0 0 10px rgba(0, 0, 0, 0.15); }}
                        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #00ADB5; padding-bottom: 20px; margin-bottom: 20px; }}
                        .header h1 {{ margin: 0; color: #00ADB5; font-size: 32px; }}
                        .info-toko {{ text-align: right; color: #555; font-size: 14px; }}
                        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                        th, td {{ padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }}
                        th {{ background-color: #f8f9fa; color: #333; }}
                        .total-row {{ font-weight: bold; background-color: #e9ecef; }}
                        .dp-row {{ color: #28a745; font-weight: bold; }}
                        .sisa-row {{ color: #d9534f; font-weight: bold; font-size: 1.1em; }}
                        .footer {{ text-align: center; margin-top: 50px; color: #888; font-size: 12px; border-top: 1px solid #eee; padding-top: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="invoice-box">
                        <div class="header">
                            <h1>INVOICE</h1>
                            <div class="info-toko">
                                <strong>Pabrik Konveksi Topi Cerdas</strong><br>
                                Jl. Industri Raya No. 1, Bandung<br>
                                Telp: 0812-3456-7890
                            </div>
                        </div>
                        
                        <div style="display: flex; justify-content: space-between; margin-bottom: 30px;">
                            <div>
                                <p style="margin: 0; color: #777;">Tagihan Kepada:</p>
                                <h3 style="margin: 5px 0;">{data_order['Nama Klien']}</h3>
                            </div>
                            <div style="text-align: right;">
                                <p style="margin: 0;"><strong>No. Order:</strong> {data_order['ID Order']}</p>
                                <p style="margin: 5px 0;"><strong>Tanggal:</strong> {data_order['Tanggal']}</p>
                                <p style="margin: 0; color: #17a2b8;"><strong>Status:</strong> {status_inv}</p>
                            </div>
                        </div>
                        
                        <table>
                            <tr>
                                <th>Deskripsi Produk</th>
                                <th style="text-align: center;">Jumlah</th>
                                <th style="text-align: right;">Total Harga</th>
                            </tr>
                            <tr>
                                <td>Pembuatan <b>{data_order['Model Topi']}</b> (Custom Design)</td>
                                <td style="text-align: center;">{data_order['Jumlah (Pcs)']} Pcs</td>
                                <td style="text-align: right;">Rp {float(data_order['Total Harga']):,.0f}</td>
                            </tr>
                            <tr class="total-row">
                                <td colspan="2" style="text-align: right;">GRAND TOTAL</td>
                                <td style="text-align: right;">Rp {float(data_order['Total Harga']):,.0f}</td>
                            </tr>
                            <tr class="dp-row">
                                <td colspan="2" style="text-align: right;">SUDAH DIBAYAR (DP)</td>
                                <td style="text-align: right;">- Rp {dp_inv:,.0f}</td>
                            </tr>
                            <tr class="sisa-row">
                                <td colspan="2" style="text-align: right;">SISA TAGIHAN</td>
                                <td style="text-align: right;">Rp {sisa_inv:,.0f}</td>
                            </tr>
                        </table>
                        
                        <div class="footer">
                            <p>Terima kasih atas kepercayaan Anda pada Pabrik Konveksi Topi Cerdas.</p>
                            <p><i>Invoice ini dicetak otomatis oleh Sistem ERP dan sah tanpa tanda tangan.</i></p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                st.components.v1.html(html_invoice, height=600, scrolling=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    label="📄 Download Invoice (Buka & Print jadi PDF)",
                    data=html_invoice,
                    file_name=f"Invoice_{data_order['ID Order']}.html",
                    mime="text/html",
                    type="primary",
                    use_container_width=True
                )