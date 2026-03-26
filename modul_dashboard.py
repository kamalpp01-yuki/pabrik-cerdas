import streamlit as st
import pandas as pd

def jalankan(df_pem, df_uang, df_prod, df_jadi):
    # (Judul sudah ada di app_industri.py, jadi kita langsung masuk ke isinya)
    
    try:
        # --- 1. DATA PREPARATION (Pembersihan Data) ---
        total_order = len(df_pem) if not df_pem.empty else 0
        
        if not df_uang.empty and 'Pemasukan (Rp)' in df_uang.columns:
            df_uang['Pemasukan (Rp)'] = pd.to_numeric(df_uang['Pemasukan (Rp)'], errors='coerce').fillna(0)
            df_uang['Pengeluaran (Rp)'] = pd.to_numeric(df_uang['Pengeluaran (Rp)'], errors='coerce').fillna(0)
            total_pendapatan = df_uang['Pemasukan (Rp)'].sum()
        else:
            total_pendapatan = 0
            
        if not df_prod.empty and 'Status Produksi' in df_prod.columns:
            sedang_diproses = len(df_prod[df_prod['Status Produksi'].str.contains('Tahap', na=False)])
        else:
            sedang_diproses = 0
            
        if not df_jadi.empty and 'Stok' in df_jadi.columns:
            df_jadi['Stok'] = pd.to_numeric(df_jadi['Stok'], errors='coerce').fillna(0)
            total_gudang = df_jadi['Stok'].sum()
        else:
            total_gudang = 0

        # --- 2. METRICS (PAPAN SKOR UTAMA) ---
        st.markdown("### 🎯 Skor Performa Hari Ini")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🛒 Total Order Masuk", f"{total_order} Order")
        c2.metric("💰 Total Pemasukan", f"Rp {total_pendapatan:,.0f}".replace(",", "."))
        c3.metric("⚙️ Sedang Diproduksi", f"{sedang_diproses} Batch")
        c4.metric("📦 Stok Gudang", f"{total_gudang:,.0f} Pcs")
        st.divider()

        # --- 3. ANALITIK VISUAL TINGKAT LANJUT ---
        st.markdown("### 🧠 Analitik Bisnis & Penjualan")

        # Baris Grafik 1
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown("**🔥 Model Topi Paling Laris**")
            if not df_pem.empty and 'Model Topi' in df_pem.columns and 'Jumlah (Pcs)' in df_pem.columns:
                df_pem['Jumlah (Pcs)'] = pd.to_numeric(df_pem['Jumlah (Pcs)'], errors='coerce').fillna(0)
                # Jurus Dinamis: Mengelompokkan otomatis berdasarkan Model Topi yang ada
                df_laris = df_pem.groupby("Model Topi")["Jumlah (Pcs)"].sum()
                # Sortir dari yang terbanyak
                df_laris = df_laris.sort_values(ascending=False)
                st.bar_chart(df_laris, color="#FF6B6B") # Warna merah merona
            else:
                st.info("Belum ada data pesanan untuk dianalisis.")

        with col_chart2:
            st.markdown("**📉 Tren Arus Kas Harian**")
            if not df_uang.empty and 'Tanggal' in df_uang.columns:
                # Menggabungkan pemasukan & pengeluaran per hari
                df_chart_uang = df_uang.groupby("Tanggal")[["Pemasukan (Rp)", "Pengeluaran (Rp)"]].sum()
                st.line_chart(df_chart_uang, color=["#00ADB5", "#FF2E63"]) # Custom warna ganda
            else:
                st.info("Belum ada data transaksi keuangan.")

        st.markdown("<br>", unsafe_allow_html=True)

        # Baris Grafik 2
        col_chart3, col_chart4 = st.columns(2)

        with col_chart3:
            st.markdown("**📦 Posisi Stok Barang Jadi (Gudang)**")
            if not df_jadi.empty:
                df_chart_jadi = df_jadi.set_index("Model Topi")["Stok"]
                st.bar_chart(df_chart_jadi, color="#F8B500") # Warna kuning emas
            else:
                st.info("Belum ada data barang jadi di gudang.")

        with col_chart4:
            st.markdown("**📊 Sebaran Status Order**")
            if not df_pem.empty and 'Status Validasi' in df_pem.columns:
                # Menghitung otomatis berapa banyak orderan di setiap status
                df_status = df_pem['Status Validasi'].value_counts()
                st.bar_chart(df_status, color="#393E46") # Warna abu-abu elegan
            else:
                st.info("Belum ada data status pesanan.")

        st.divider()

        # --- 4. TABEL AKTIVITAS TERBARU ---
        st.markdown("### 🔔 5 Transaksi Pesanan Terakhir")
        if not df_pem.empty:
            # Ambil 5 data paling bawah (terbaru), lalu balik urutannya biar yang ter-update ada di nomor 1
            df_recent = df_pem.tail(5).iloc[::-1] 
            kolom_tampil = ["Tanggal", "ID Order", "Nama Klien", "Model Topi", "Jumlah (Pcs)", "Status Validasi"]
            # Filter kolom biar gak error kalau ada kolom yang hilang
            kolom_ada = [k for k in kolom_tampil if k in df_recent.columns]
            
            st.dataframe(df_recent[kolom_ada], use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada aktivitas transaksi pesanan yang masuk.")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat merender grafik: {e}")
        st.warning("Pastikan Anda sudah mengisi Master Produk dan membuat pesanan pertama Anda!")