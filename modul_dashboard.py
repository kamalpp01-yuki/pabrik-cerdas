import streamlit as st
import pandas as pd

def jalankan(df_pem, df_uang, df_prod, df_jadi):
    try:
        # 1. Rumus Hitung-hitungan Cepat ala Manajer
        total_order = len(df_pem) if not df_pem.empty else 0
        
        if not df_uang.empty and 'Pemasukan (Rp)' in df_uang.columns:
            df_uang['Pemasukan (Rp)'] = pd.to_numeric(df_uang['Pemasukan (Rp)'], errors='coerce').fillna(0)
            total_pendapatan = df_uang['Pemasukan (Rp)'].sum()
        else:
            total_pendapatan = 0
            
        # PERBAIKAN LOGIKA: Hitung semua barang yang masih di "Tahap" potong/jahit/bordir/QC
        if not df_prod.empty and 'Status Produksi' in df_prod.columns:
            sedang_diproses = len(df_prod[df_prod['Status Produksi'].str.contains('Tahap', na=False)])
        else:
            sedang_diproses = 0
            
        if not df_jadi.empty and 'Stok' in df_jadi.columns:
            df_jadi['Stok'] = pd.to_numeric(df_jadi['Stok'], errors='coerce').fillna(0)
            total_gudang = df_jadi['Stok'].sum()
        else:
            total_gudang = 0
            
        # 2. TAMPILKAN PAPAN SKOR (METRICS)
        st.markdown("### 📈 Skor Performa Hari Ini")
        
        # Bagi layar jadi 4 kolom sejajar
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(label="🛒 Total Pesanan Masuk", value=f"{total_order} Order")
        c2.metric(label="💰 Total Pendapatan", value=f"Rp {total_pendapatan:,.0f}".replace(",", "."))
        c3.metric(label="⚙️ Sedang Diproduksi", value=f"{sedang_diproses} Batch")
        c4.metric(label="📦 Stok Barang Jadi", value=f"{total_gudang:,.0f} Pcs")
        
        st.divider()
        
        # --- LEVEL 3: TAMBAHAN GRAFIK VISUAL (CHARTS) ---
        st.markdown("### 📈 Analitik Visual Pabrik")
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("**📊 Posisi Stok Barang Jadi**")
            if not df_jadi.empty:
                df_chart_jadi = df_jadi.set_index("Model Topi")["Stok"]
                st.bar_chart(df_chart_jadi, color="#00ADB5") 
            else:
                st.info("Belum ada data barang jadi di gudang.")
                
        with col_chart2:
            st.markdown("**📉 Tren Arus Kas Harian**")
            if not df_uang.empty and 'Tanggal' in df_uang.columns:
                df_uang['Pemasukan (Rp)'] = pd.to_numeric(df_uang.get('Pemasukan (Rp)', 0), errors='coerce').fillna(0)
                df_uang['Pengeluaran (Rp)'] = pd.to_numeric(df_uang.get('Pengeluaran (Rp)', 0), errors='coerce').fillna(0)
                
                df_chart_uang = df_uang.groupby("Tanggal")[["Pemasukan (Rp)", "Pengeluaran (Rp)"]].sum()
                st.line_chart(df_chart_uang)
            else:
                st.info("Belum ada data transaksi keuangan.")
                
        st.divider()
        st.info("💡 Selamat datang di Sistem ERP Cerdas. Silakan navigasi ke modul di sebelah kiri untuk operasional detail.")
        
    except Exception as e:
        st.warning("Sedang memuat data atau data masih kosong. Silakan isi pesanan pertama Anda!")