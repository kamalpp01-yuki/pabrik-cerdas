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
    
    c1, c2 = st.columns(2)
    c1.metric("🛒 Total Pesanan Klien", f"{total_order} Order")
    c2.metric("⏳ Menunggu Pembayaran", f"{pending} Order", delta="- Action Needed", delta_color="inverse")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📝 Form Pesanan Baru", "📋 Database Pesanan", "🖨️ Cetak Invoice"])

    # ==========================================
    # TAB 1: FORM PESANAN
    # ==========================================
    with tab1:
        if df_produk.empty:
            st.warning("⚠️ Katalog Produk kosong! Minta divisi Produksi mengisi Master BOM terlebih dahulu.")
        else:
            st.markdown("### ➕ Buat Pesanan Baru")
            col_kiri, col_kanan = st.columns(2)
            
            with col_kiri:
                nama_klien = st.text_input("Nama Klien / Instansi", key="in_nama")
                daftar_topi = df_produk["Model Topi"].tolist()
                model_topi = st.selectbox("Pilih Model Topi", daftar_topi, key="in_model")
                jumlah = st.number_input("Jumlah (Pcs)", min_value=1, value=50, key="in_jumlah")
                
            with col_kanan:
                file_desain = st.file_uploader("Upload Desain", type=["jpg", "png"], key="in_file")
                harga_satuan = df_produk.loc[df_produk['Model Topi'] == model_topi, 'Harga Satuan (Rp)'].values[0]
                total_harga = float(harga_satuan) * jumlah
                st.info(f"💡 Info Harga: Rp {float(harga_satuan):,.0f} / Pcs")
                st.success(f"💰 TOTAL TAGIHAN: Rp {total_harga:,.0f}")

            if st.button("💾 Simpan & Teruskan ke Keuangan", use_container_width=True):
                if nama_klien == "": st.error("⚠️ Nama Klien harus diisi!")
                else:
                    with st.spinner("🚀 Menyimpan pesanan..."):
                        id_order = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        nama_file = "Tidak Ada Desain"
                        if file_desain:
                            os.makedirs("desain_topi", exist_ok=True)
                            nama_file = f"{id_order}_{file_desain.name}"
                            with open(os.path.join("desain_topi", nama_file), "wb") as f:
                                f.write(file_desain.getbuffer())

                        data_baru = pd.DataFrame([{"ID Order": id_order, "Tanggal": datetime.now().strftime("%Y-%m-%d"), "Nama Klien": nama_klien, "Model Topi": model_topi, "Jumlah (Pcs)": jumlah, "Total Harga": total_harga, "File Desain": nama_file, "Status Validasi": "Menunggu Pembayaran"}])
                        conn.update(worksheet="Pemasaran", data=pd.concat([df_pem, data_baru], ignore_index=True))
                        
                        for k in ['in_nama', 'in_model', 'in_jumlah', 'in_file']: 
                            if k in st.session_state: del st.session_state[k]
                        
                        st.session_state['notif_sukses'] = f"✅ Pesanan dari {nama_klien} tersimpan!"
                        st.cache_data.clear(); st.rerun()

    # ==========================================
    # TAB 2: DATABASE PESANAN (EFEK DOMINO)
    # ==========================================
    with tab2:
        st.markdown("### 📋 Seluruh Data Pesanan Masuk")
        df_pem_edit = st.data_editor(df_pem, use_container_width=True, num_rows="dynamic", key="edit_pem")
        if st.button("💾 Simpan Perubahan Database", type="primary"):
            st.session_state['konf_pem'] = True

        if st.session_state.get('konf_pem', False):
            st.warning("⚠️ Yakin simpan? Data Produksi & Keuangan akan ikut menyesuaikan!")
            cy, cn = st.columns(2)
            if cy.button("✅ Ya, Sinkronkan"):
                with st.spinner("🔄 Menyinkronkan..."):
                    pesanan_lama = set(df_pem['ID Order'])
                    pesanan_baru = set(df_pem_edit['ID Order'])
                    dihapus = pesanan_lama - pesanan_baru

                    try: df_prod_sync = conn.read(worksheet="Produksi").dropna(how="all")
                    except: df_prod_sync = pd.DataFrame()
                    try: df_uang_sync = conn.read(worksheet="Keuangan").dropna(how="all")
                    except: df_uang_sync = pd.DataFrame()

                    if dihapus:
                        if not df_prod_sync.empty and 'ID Order' in df_prod_sync.columns:
                            df_prod_sync = df_prod_sync[~df_prod_sync['ID Order'].isin(dihapus)]
                        if not df_uang_sync.empty and 'Keterangan' in df_uang_sync.columns:
                            mask = df_uang_sync['Keterangan'].apply(lambda x: any(d in str(x) for d in dihapus))
                            df_uang_sync = df_uang_sync[~mask]
                            conn.update(worksheet="Keuangan", data=df_uang_sync)

                    if not df_prod_sync.empty and 'ID Order' in df_prod_sync.columns:
                        model_map = dict(zip(df_pem_edit['ID Order'], df_pem_edit['Model Topi']))
                        jml_map = dict(zip(df_pem_edit['ID Order'], df_pem_edit['Jumlah (Pcs)']))
                        df_prod_sync['Model Topi'] = df_prod_sync['ID Order'].map(model_map).fillna(df_prod_sync['Model Topi'])
                        df_prod_sync['Jumlah (Pcs)'] = df_prod_sync['ID Order'].map(jml_map).fillna(df_prod_sync['Jumlah (Pcs)'])
                        conn.update(worksheet="Produksi", data=df_prod_sync)

                    conn.update(worksheet="Pemasaran", data=df_pem_edit)
                    st.session_state['konf_pem'] = False
                    st.cache_data.clear(); st.success("✅ Tersimpan!"); st.rerun()

            if cn.button("❌ Batal"):
                st.session_state['konf_pem'] = False; st.rerun()

    # ==========================================
    # TAB 3: CETAK INVOICE OTOMATIS
    # ==========================================
    with tab3:
        st.markdown("### 🖨️ Cetak Invoice & Nota Pembayaran")
        if df_pem.empty:
            st.info("Belum ada data pesanan untuk dicetak.")
        else:
            # Filter cuma pesanan yang udah punya ID Order yang jelas
            daftar_order = df_pem['ID Order'].dropna().tolist()
            pilih_order = st.selectbox("Pilih ID Order yang akan dicetak:", daftar_order)
            
            if pilih_order:
                # Sedot data pesanan yang dipilih
                data_order = df_pem[df_pem['ID Order'] == pilih_order].iloc[0]
                
                # Desain HTML Kustom yang Cantik ala Struk/Invoice
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
                        .total-row {{ font-weight: bold; font-size: 1.2em; background-color: #e9ecef; }}
                        .total-harga {{ text-align: right; color: #d9534f; }}
                        .footer {{ text-align: center; margin-top: 50px; color: #888; font-size: 12px; border-top: 1px solid #eee; padding-top: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="invoice-box">
                        <div class="header">
                            <h1>INVOICE</h1>
                            <div class="info-toko">
                                <strong>Pabrik Konveksi Topi</strong><br>
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
                                <p style="margin: 0; color: #17a2b8;"><strong>Status:</strong> {data_order['Status Validasi']}</p>
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
                                <td colspan="2" style="text-align: right;">TOTAL TAGIHAN</td>
                                <td class="total-harga">Rp {float(data_order['Total Harga']):,.0f}</td>
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
                
                # Tampilkan Preview Invoice di layar Streamlit
                st.components.v1.html(html_invoice, height=500, scrolling=True)
                
                # Tombol Download File HTML
                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    label="📄 Download Invoice (Buka & Print jadi PDF)",
                    data=html_invoice,
                    file_name=f"Invoice_{data_order['Nama Klien']}_{data_order['ID Order']}.html",
                    mime="text/html",
                    type="primary",
                    use_container_width=True
                )
                
                st.info("💡 **Cara mengubah jadi PDF:** Klik tombol Download di atas, buka file yang terunduh di *browser* (Chrome/Edge), lalu tekan **Ctrl + P** dan pilih opsi **Save as PDF** / Simpan sebagai PDF.")