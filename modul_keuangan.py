import streamlit as st
import pandas as pd
from datetime import datetime

def jalankan(df_uang, df_pem, conn):
    st.markdown("## 💰 Modul Keuangan & Validasi")
    
    # --- MINI DASHBOARD KEUANGAN ---
    df_uang['Pemasukan (Rp)'] = pd.to_numeric(df_uang['Pemasukan (Rp)'], errors='coerce').fillna(0)
    df_uang['Pengeluaran (Rp)'] = pd.to_numeric(df_uang['Pengeluaran (Rp)'], errors='coerce').fillna(0)
    
    total_masuk = df_uang['Pemasukan (Rp)'].sum()
    total_keluar = df_uang['Pengeluaran (Rp)'].sum()
    saldo_kas = total_masuk - total_keluar
    
    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Saldo Kas Aktif", f"Rp {saldo_kas:,.0f}")
    c2.metric("📈 Total Pemasukan", f"Rp {total_masuk:,.0f}")
    c3.metric("📉 Total Pengeluaran", f"Rp {total_keluar:,.0f}")
    st.divider()

    # 3 TAB TERPISAH
    tab1, tab2, tab3 = st.tabs(["✅ Validasi Order", "📒 Buku Kas (Riwayat)", "💸 Input Pengeluaran"])

    with tab1:
        df_pending = df_pem[df_pem['Status Validasi'] == 'Menunggu Pembayaran']
        if df_pending.empty:
            st.info("Hore! Belum ada tagihan yang tertunggak.")
        else:
            for index, row in df_pending.iterrows():
                with st.expander(f"💰 {row['ID Order']} - {row['Nama Klien']} (Rp {row['Total Harga']:,.0f})"):
                    st.write(f"**Model:** {row['Model Topi']} | **Jumlah:** {row['Jumlah (Pcs)']} Pcs")
                    if st.button("Lunas & Validasi ➡️ Masuk Produksi", key=f"val_{row['ID Order']}"):
                        df_pem.loc[df_pem['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Siap Produksi'
                        conn.update(worksheet="Pemasaran", data=df_pem)
                        data_uang_baru = pd.DataFrame([{"Tanggal": datetime.now().strftime("%Y-%m-%d"), "Keterangan": f"Pelunasan {row['ID Order']}", "Pemasukan (Rp)": row['Total Harga'], "Pengeluaran (Rp)": 0}])
                        conn.update(worksheet="Keuangan", data=pd.concat([df_uang, data_uang_baru], ignore_index=True))
                        st.cache_data.clear(); st.rerun()

    with tab2:
        st.dataframe(df_uang, use_container_width=True, height=400)
            
    with tab3:
        with st.form("form_pengeluaran", clear_on_submit=True):
            st.markdown("### Catat Arus Kas Keluar")
            ket = st.text_input("Keterangan", placeholder="Misal: Bayar Listrik / Gaji Tukang Jahit")
            nominal = st.number_input("Nominal (Rp)", min_value=0, step=50000)
            if st.form_submit_button("💾 Catat Pengeluaran", use_container_width=True):
                if ket and nominal > 0:
                    data_keluar = pd.DataFrame([{"Tanggal": datetime.now().strftime("%Y-%m-%d"), "Keterangan": ket, "Pemasukan (Rp)": 0, "Pengeluaran (Rp)": nominal}])
                    conn.update(worksheet="Keuangan", data=pd.concat([df_uang, data_keluar], ignore_index=True))
                    st.cache_data.clear(); st.success("Tercatat!"); st.rerun()
                else:
                    # --- TAMBAHKAN SPINNER DI SINI ---
                    with st.spinner("🚀 Sedang  menyimpan data ..."):
                        st.error("Isi data dengan benar!")