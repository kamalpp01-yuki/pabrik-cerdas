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

    tab1, tab2, tab3 = st.tabs(["📝 Form Order Terpadu", "📋 Database Pesanan", "🖨️ Cetak Invoice Lengkap"])

    # ==========================================
    # TAB 1: FORM PESANAN TERPADU (MEGA-INTEGRASI)
    # ==========================================
    with tab1:
        if df_produk.empty:
            st.warning("⚠️ Katalog Produk kosong! Minta divisi Produksi mengisi Master BOM terlebih dahulu.")
        else:
            st.markdown("### ➕ Buat Pesanan Baru (Auto-Sync 4 Divisi)")
            st.info("💡 Formulir ini akan otomatis mendistribusikan data ke Pemasaran, Buku Piutang, CRM Klien, dan Kas Keuangan.")
            
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

                # --- BAGIAN 3: PEMBAYARAN & DP ---
                st.markdown("#### 💳 3. Pembayaran Awal (DP)")
                st.success(f"**💰 TOTAL TAGIHAN: Rp {total_harga:,.0f}**")
                
                dp_masuk = st.number_input("Nominal Pembayaran Masuk (Rp)", min_value=0.0, max_value=float(total_harga), step=50000.0, key="in_dp")
                sisa_tagihan = total_harga - dp_masuk
                
                # Logika Penentuan Status Otomatis
                if sisa_tagihan == 0: status_bayar = "Lunas"
                elif dp_masuk > 0: status_bayar = "DP / Cicilan"
                else: status_bayar = "Belum Bayar"
                
                # Logika Masuk Produksi
                status_produksi = "Sedang Diproses" if dp_masuk > 0 else "Menunggu Pembayaran"
                
                st.markdown(f"Status Pembayaran: **{status_bayar}** | Sisa Hutang Klien: **Rp {sisa_tagihan:,.0f}**")
                st.caption(f"Status Order: *{status_produksi}*")

            # --- TOMBOL SAKTI PENYIMPANAN MEGA-INTEGRASI ---
            if st.button("🚀 Simpan & Distribusikan Data Keseluruh Sistem", use_container_width=True, type="primary"):
                if nama_klien == "": 
                    st.error("⚠️ Nama Klien harus diisi!")
                else:
                    with st.spinner("🔄 Sedang menembakkan data ke 4 Divisi (Pemasaran, CRM, Piutang, Keuangan)..."):
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

                        # 2. Update Database KLIEN (CRM) - ANTI ERROR
                        try: 
                            df_klien = conn.read(worksheet="Database_Klien").dropna(how="all")
                            # Jika sheet kosong / gak ada header, paksa bikin kerangka kolom
                            if 'Nama Klien' not in df_klien.columns: 
                                df_klien = pd.DataFrame(columns=["Nama Klien", "No WA", "Alamat", "Kategori"])
                        except: 
                            df_klien = pd.DataFrame(columns=["Nama Klien", "No WA", "Alamat", "Kategori"])
                        
                        # Cek apakah nama klien sudah ada, kalau belum tambahkan
                        if df_klien.empty or nama_klien not in df_klien['Nama Klien'].values:
                            new_klien = pd.DataFrame([{"Nama Klien": nama_klien, "No WA": wa_klien, "Alamat": alamat_klien, "Kategori": kategori_klien}])
                            conn.update(worksheet="Database_Klien", data=pd.concat([df_klien, new_klien], ignore_index=True))

                        # 3. Update BUKU PIUTANG - ANTI ERROR
                        try: 
                            df_piutang = conn.read(worksheet="Buku_Piutang").dropna(how="all")
                            if 'ID Order' not in df_piutang.columns: 
                                df_piutang = pd.DataFrame(columns=["ID Order", "Sudah Dibayar", "Sisa Tagihan", "Status Pembayaran"])
                        except: 
                            df_piutang = pd.DataFrame(columns=["ID Order", "Sudah Dibayar", "Sisa Tagihan", "Status Pembayaran"])
                        
                        new_piutang = pd.DataFrame([{"ID Order": id_order, "Sudah Dibayar": dp_masuk, "Sisa Tagihan": sisa_tagihan, "Status Pembayaran": status_bayar}])
                        conn.update(worksheet="Buku_Piutang", data=pd.concat([df_piutang, new_piutang], ignore_index=True))

                        # 4. Update KAS KEUANGAN (Jika ada DP masuk) - ANTI ERROR
                        if dp_masuk > 0:
                            try: 
                                df_uang = conn.read(worksheet="Keuangan").dropna(how="all")
                                if 'Tanggal' not in df_uang.columns: 
                                    df_uang = pd.DataFrame(columns=["Tanggal", "Keterangan", "Pemasukan (Rp)", "Pengeluaran (Rp)"])
                            except: 
                                df_uang = pd.DataFrame(columns=["Tanggal", "Keterangan", "Pemasukan (Rp)", "Pengeluaran (Rp)"])
                            
                            new_uang = pd.DataFrame([{"Tanggal": tgl_skrg, "Keterangan": f"Penerimaan {status_bayar} - {id_order} ({nama_klien})", "Pemasukan (Rp)": dp_masuk, "Pengeluaran (Rp)": 0}])
                            conn.update(worksheet="Keuangan", data=pd.concat([df_uang, new_uang], ignore_index=True))

                        # Bersihkan Form
                        for k in ['in_nama', 'in_wa', 'in_alamat', 'in_model', 'in_jumlah', 'in_dp', 'in_file']: 
                            if k in st.session_state: del st.session_state[k]
                        
                        st.session_state['notif_sukses'] = f"✅ Pesanan {id_order} berhasil didistribusikan ke seluruh divisi!"
                        st.cache_data.clear(); st.rerun()

    # ==========================================
    # TAB 2: DATABASE PESANAN
    # ==========================================
    with tab2:
        st.markdown("### 📋 Seluruh Data Pesanan Masuk")
        st.info("💡 Karena data sudah terintegrasi, perubahan Nominal Uang/DP hanya bisa dilakukan di menu CRM & Piutang.")
        st.dataframe(df_pem, use_container_width=True, hide_index=True)

    # ==========================================
    # TAB 3: CETAK INVOICE OTOMATIS (UPDATE)
    # ==========================================
    with tab3:
        st.markdown("### 🖨️ Cetak Invoice & Nota Pembayaran")
        if df_pem.empty:
            st.info("Belum ada data pesanan untuk dicetak.")
        else:
            daftar_order = df_pem['ID Order'].dropna().tolist()
            pilih_order = st.selectbox("Pilih ID Order yang akan dicetak:", daftar_order)
            
            if pilih_order:
                data_order = df_pem[df_pem['ID Order'] == pilih_order].iloc[0]
                
                # Sedot data dari Piutang untuk nampilin DP & Sisa Tagihan di Invoice
                try: 
                    df_piutang_inv = conn.read(worksheet="Buku_Piutang").dropna(how="all")
                    data_piutang = df_piutang_inv[df_piutang_inv['ID Order'] == pilih_order].iloc[0]
                    dp_inv = float(data_piutang['Sudah Dibayar'])
                    sisa_inv = float(data_piutang['Sisa Tagihan'])
                    status_inv = data_piutang['Status Pembayaran']
                except:
                    dp_inv, sisa_inv, status_inv = 0, float(data_order['Total Harga']), "Belum Bayar"

                # HTML Invoice Kustom
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