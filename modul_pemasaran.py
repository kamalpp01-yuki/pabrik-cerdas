import streamlit as st
import pandas as pd
from datetime import datetime
import os

def jalankan(df_pem, df_produk, conn): 
    if st.session_state.get('notif_sukses'):
        st.success(st.session_state['notif_sukses'])
        st.session_state['notif_sukses'] = ""

    total_order = len(df_pem)
    pending = len(df_pem[df_pem['Status Validasi'] == 'Menunggu Pembayaran']) if not df_pem.empty else 0
    
    c1, c2 = st.columns(2)
    c1.metric("🛒 Total Pesanan Klien", f"{total_order} Order")
    c2.metric("⏳ Menunggu Pembayaran", f"{pending} Order", delta="- Action Needed", delta_color="inverse")
    st.divider()

    tab1, tab2 = st.tabs(["📝 Form Pesanan Baru", "📋 Database Pesanan"])

    # TAB 1: FORM PESANAN
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

    # TAB 2: DATABASE PESANAN (EFEK DOMINO)
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