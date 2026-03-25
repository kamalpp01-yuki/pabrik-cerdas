import streamlit as st
import pandas as pd
from datetime import datetime

def jalankan(df_uang, df_pemasaran, conn):
    # --- FITUR 1: VALIDASI PESANAN MASUK ---
    st.subheader("⚖️ Validasi Pembayaran Pesanan (Dari Sales)")
    
    # Saring HANYA pesanan yang statusnya "Menunggu Pembayaran"
    df_pending = df_pemasaran[df_pemasaran['Status Validasi'] == 'Menunggu Pembayaran']
    
    if df_pending.empty:
        st.info("✅ Santai dulu, Bos! Tidak ada pesanan baru yang menunggu validasi.")
    else:
        # Bikin kotak-kotak rapi untuk setiap pesanan yang butuh divalidasi
        for index, row in df_pending.iterrows():
            with st.expander(f"📦 Order: {row['ID Order']} | Klien: {row['Nama Klien']} | Rp {row['Total Harga']:,.0f}"):
                st.write(f"**Model:** {row['Model Topi']} | **Jumlah:** {row['Jumlah (Pcs)']} Pcs")
                st.write(f"**Tanggal Pesan:** {row['Tanggal']}")
                
                # Tombol sakti Validator
                if st.button(f"✅ Validasi Lunas & Masukkan ke Kas", key=f"val_{row['ID Order']}"):
                    
                    # A. Ubah Status di Tabel Pemasaran
                    df_pemasaran.loc[df_pemasaran['ID Order'] == row['ID Order'], 'Status Validasi'] = 'Siap Produksi'
                    conn.update(worksheet="Pemasaran", data=df_pemasaran)
                    
                    # B. Otomatis Tambah Uang Masuk ke Tabel Keuangan
                    data_uang_baru = pd.DataFrame([{
                        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                        "Keterangan": f"Pelunasan Order {row['ID Order']} ({row['Nama Klien']})",
                        "Pemasukan (Rp)": row['Total Harga'],
                        "Pengeluaran (Rp)": 0
                    }])
                    df_uang_update = pd.concat([df_uang, data_uang_baru], ignore_index=True)
                    conn.update(worksheet="Keuangan", data=df_uang_update)
                    
                    st.cache_data.clear()
                    st.success(f"Berhasil! Pesanan {row['ID Order']} disahkan dan uang masuk ke kas!")
                    st.rerun()

    st.divider()

    # --- FITUR 2: BUKU KAS MANUAL & LAPORAN ---
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("➕ Catat Transaksi Manual")
        with st.form("form_keuangan", clear_on_submit=True):
            tanggal = st.date_input("Tanggal Transaksi")
            keterangan = st.text_input("Keterangan (Cth: Bayar Listrik)")
            jenis = st.radio("Jenis Transaksi", ["Pemasukan", "Pengeluaran"])
            nominal = st.number_input("Nominal (Rp)", min_value=0, step=10000)
            
            if st.form_submit_button("💾 Simpan ke Buku Kas"):
                uang_masuk = nominal if jenis == "Pemasukan" else 0
                uang_keluar = nominal if jenis == "Pengeluaran" else 0
                data_baru = pd.DataFrame([{
                    "Tanggal": tanggal.strftime("%Y-%m-%d"),
                    "Keterangan": keterangan,
                    "Pemasukan (Rp)": uang_masuk,
                    "Pengeluaran (Rp)": uang_keluar
                }])
                df_update = pd.concat([df_uang, data_baru], ignore_index=True)
                conn.update(worksheet="Keuangan", data=df_update)
                st.cache_data.clear() 
                st.success("✅ Transaksi berhasil dicatat!")
                st.rerun()

    with col2:
        st.subheader("📒 Buku Kas Pabrik Topi")
        st.dataframe(df_uang, use_container_width=True)
        
        if not df_uang.empty:
            df_uang['Pemasukan (Rp)'] = pd.to_numeric(df_uang['Pemasukan (Rp)'], errors='coerce').fillna(0)
            df_uang['Pengeluaran (Rp)'] = pd.to_numeric(df_uang['Pengeluaran (Rp)'], errors='coerce').fillna(0)
            tot_masuk = df_uang['Pemasukan (Rp)'].sum()
            tot_keluar = df_uang['Pengeluaran (Rp)'].sum()
            saldo = tot_masuk - tot_keluar
            
            c1, c2, c3 = st.columns(3)
            c1.metric("🟢 Total Pemasukan", f"Rp {tot_masuk:,.0f}".replace(",", "."))
            c2.metric("🔴 Total Pengeluaran", f"Rp {tot_keluar:,.0f}".replace(",", "."))
            c3.metric("💎 Saldo Bersih", f"Rp {saldo:,.0f}".replace(",", ".") if saldo >= 0 else f"-Rp {abs(saldo):,.0f}".replace(",", "."))
            
            csv = df_uang.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Laporan (CSV)", data=csv, file_name="Buku_Kas.csv", mime="text/csv", use_container_width=True)