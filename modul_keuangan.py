import streamlit as st
import pandas as pd
from datetime import datetime

def jalankan(df_uang, conn):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("➕ Catat Transaksi Baru")
        with st.form("form_keuangan", clear_on_submit=True):
            tanggal = st.date_input("Tanggal Transaksi")
            keterangan = st.text_input("Keterangan (Cth: Jual 100 Pcs Topi Rimba)")
            jenis = st.radio("Jenis Transaksi", ["Pemasukan", "Pengeluaran"])
            nominal = st.number_input("Nominal (Rp)", min_value=0, step=10000)
            
            submit = st.form_submit_button("💾 Simpan ke Buku Kas")
            
            if submit:
                # Pisahkan angka sesuai jenisnya
                uang_masuk = nominal if jenis == "Pemasukan" else 0
                uang_keluar = nominal if jenis == "Pengeluaran" else 0
                
                data_baru = pd.DataFrame([{
                    "Tanggal": tanggal.strftime("%Y-%m-%d"),
                    "Keterangan": keterangan,
                    "Pemasukan (Rp)": uang_masuk,
                    "Pengeluaran (Rp)": uang_keluar
                }])
                
                # Gabung dan Update ke Google Sheets
                df_update = pd.concat([df_uang, data_baru], ignore_index=True)
                conn.update(worksheet="Keuangan", data=df_update)
                
                st.cache_data.clear() # Bersihkan memori agar langsung update
                st.success("✅ Transaksi berhasil dicatat!")
                st.rerun()

    with col2:
        st.subheader("📒 Buku Kas Pabrik Topi")
        st.dataframe(df_uang, use_container_width=True)
        
        # --- PERHITUNGAN OTOMATIS (PROFIT) ---
        if not df_uang.empty:
            # Paksa jadi angka biar nggak error kalau Google Sheets ngaco
            df_uang['Pemasukan (Rp)'] = pd.to_numeric(df_uang['Pemasukan (Rp)'], errors='coerce').fillna(0)
            df_uang['Pengeluaran (Rp)'] = pd.to_numeric(df_uang['Pengeluaran (Rp)'], errors='coerce').fillna(0)
            
            tot_masuk = df_uang['Pemasukan (Rp)'].sum()
            tot_keluar = df_uang['Pengeluaran (Rp)'].sum()
            saldo = tot_masuk - tot_keluar
            
            st.divider()
            st.subheader("📊 Ringkasan Finansial")
            c1, c2, c3 = st.columns(3)
            
            # Format angka agar ada pemisah ribuan
            c1.metric("🟢 Total Pemasukan", f"Rp {tot_masuk:,.0f}".replace(",", "."))
            c2.metric("🔴 Total Pengeluaran", f"Rp {tot_keluar:,.0f}".replace(",", "."))
            
            # Ubah warna saldo (Hijau kalau untung, Merah kalau rugi)
            if saldo >= 0:
                c3.metric("💎 Saldo Bersih (Profit)", f"Rp {saldo:,.0f}".replace(",", "."))
            else:
                c3.metric("⚠️ Saldo Minus (Rugi)", f"Rp {saldo:,.0f}".replace(",", "."))