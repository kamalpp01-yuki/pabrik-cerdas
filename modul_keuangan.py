import streamlit as st
import pandas as pd
from datetime import datetime

def jalankan(df_uang, df_pem, conn):
    st.markdown("## 💰 Modul Keuangan & Validasi")
    st.write("Validasi pembayaran klien dan pantau arus kas pabrik.")
    st.divider()

    tab1, tab2 = st.tabs(["✅ Validasi Order Masuk", "📒 Buku Kas & Input Pengeluaran"])

    # --- TAB 1: VALIDASI ---
    with tab1:
        st.markdown("### ⏳ Menunggu Pembayaran")
        df_pending = df_pem[df_pem['Status Validasi'] == 'Menunggu Pembayaran']
        
        if df_pending.empty:
            st.info("Hore! Belum ada tagihan yang tertunggak.")
        else:
            for index, row in df_pending.iterrows():
                with st.expander(f"💰 {row['ID Order']} - {row['Nama Klien']} (Rp {row['Total Harga']:,.0f})"):
                    st.write(f"**Model:** {row['Model Topi']} | **Jumlah:** {row['Jumlah (Pcs)']} Pcs")
                    if st.button("Lunas & Validasi ➡️ Masuk Produksi", key=f"val_{row['ID Order']}"):
                        # 1. Update status di Pemasaran
                        df_pem.loc[df_pem['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Siap Produksi'
                        conn.update(worksheet="Pemasaran", data=df_pem)
                        
                        # 2. Catat Uang Masuk ke Keuangan
                        data_uang_baru = pd.DataFrame([{
                            "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                            "Keterangan": f"Pelunasan Order {row['ID Order']} ({row['Nama Klien']})",
                            "Pemasukan (Rp)": row['Total Harga'],
                            "Pengeluaran (Rp)": 0
                        }])
                        df_uang_update = pd.concat([df_uang, data_uang_baru], ignore_index=True)
                        conn.update(worksheet="Keuangan", data=df_uang_update)
                        
                        st.cache_data.clear()
                        st.success(f"Validasi sukses! Rp {row['Total Harga']:,.0f} masuk ke kas.")
                        st.rerun()

    # --- TAB 2: BUKU KAS ---
    with tab2:
        col_kas1, col_kas2 = st.columns([2, 1])
        with col_kas1:
            st.markdown("### 📒 Riwayat Transaksi")
            st.dataframe(df_uang, use_container_width=True, height=300)
            
        with col_kas2:
            st.markdown("### 💸 Catat Pengeluaran")
            with st.form("form_pengeluaran", clear_on_submit=True):
                ket = st.text_input("Keterangan", placeholder="Misal: Bayar Listrik")
                nominal = st.number_input("Nominal (Rp)", min_value=0, step=50000)
                if st.form_submit_button("Catat Pengeluaran", use_container_width=True):
                    if ket == "" or nominal <= 0:
                        st.error("Isi keterangan dan nominal!")
                    else:
                        data_keluar = pd.DataFrame([{
                            "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                            "Keterangan": ket,
                            "Pemasukan (Rp)": 0,
                            "Pengeluaran (Rp)": nominal
                        }])
                        df_uang_update = pd.concat([df_uang, data_keluar], ignore_index=True)
                        conn.update(worksheet="Keuangan", data=df_uang_update)
                        st.cache_data.clear()
                        st.success("Pengeluaran tercatat!")
                        st.rerun()