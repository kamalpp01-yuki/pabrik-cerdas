import streamlit as st
import pandas as pd
from datetime import datetime

def jalankan(df_uang, conn):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("➕ Catat Transaksi Manual")
        with st.form("form_keuangan", clear_on_submit=True):
            tanggal = st.date_input("Tanggal Transaksi")
            keterangan = st.text_input("Keterangan (Cth: Bayar Listrik)")
            jenis = st.radio("Jenis Transaksi", ["Pemasukan", "Pengeluaran"])
            nominal = st.number_input("Nominal (Rp)", min_value=0, step=10000)
            
            submit = st.form_submit_button("💾 Simpan ke Buku Kas")
            
            if submit:
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
            
            st.divider()
            st.subheader("📊 Ringkasan Finansial")
            c1, c2, c3 = st.columns(3)
            
            c1.metric("🟢 Total Pemasukan", f"Rp {tot_masuk:,.0f}".replace(",", "."))
            c2.metric("🔴 Total Pengeluaran", f"Rp {tot_keluar:,.0f}".replace(",", "."))
            
            if saldo >= 0:
                c3.metric("💎 Saldo Bersih (Profit)", f"Rp {saldo:,.0f}".replace(",", "."))
            else:
                c3.metric("⚠️ Saldo Minus (Rugi)", f"Rp {saldo:,.0f}".replace(",", "."))

            # --- FITUR DOWNLOAD LAPORAN ---
            st.divider() # Bikin garis pembatas
            
            # Ubah data tabel menjadi format CSV
            csv = df_uang.to_csv(index=False).encode('utf-8')
            
            # Bikin tombol download
            st.download_button(
                label="📥 Download Laporan Keuangan (CSV)",
                data=csv,
                file_name=f"Laporan_Keuangan_Topi_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True # Biar tombolnya panjang dan rapi
            )