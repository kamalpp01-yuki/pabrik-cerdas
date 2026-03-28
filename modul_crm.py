import streamlit as st
import pandas as pd
from datetime import datetime

def jalankan(df_pem, df_klien, df_piutang, df_uang, conn):
    st.markdown("## 👥 Manajemen Klien & Buku Piutang")
    
    # --- 1. MESIN SINKRONISASI OTOMATIS (SALES -> PIUTANG) ---
    if not df_pem.empty:
        order_pem = set(df_pem['ID Order'])
        order_piutang = set(df_piutang['ID Order']) if not df_piutang.empty else set()
        order_baru = order_pem - order_piutang
        
        if order_baru:
            data_baru = []
            for o_id in order_baru:
                total_harga = df_pem.loc[df_pem['ID Order'] == o_id, 'Total Harga'].values[0]
                data_baru.append({
                    "ID Order": o_id,
                    "Sudah Dibayar": 0,
                    "Sisa Tagihan": total_harga,
                    "Status Pembayaran": "Belum Bayar"
                })
            df_piutang = pd.concat([df_piutang, pd.DataFrame(data_baru)], ignore_index=True)
            conn.update(worksheet="Buku_Piutang", data=df_piutang)

    # --- 2. MINI DASHBOARD CRM ---
    df_piutang['Sisa Tagihan'] = pd.to_numeric(df_piutang['Sisa Tagihan'], errors='coerce').fillna(0)
    total_piutang = df_piutang['Sisa Tagihan'].sum()
    total_klien = len(df_klien)

    c1, c2 = st.columns(2)
    c1.metric("👥 Total Klien Terdaftar", f"{total_klien} Klien/Instansi")
    c2.metric("💸 Total Piutang (Tagihan di Luar)", f"Rp {total_piutang:,.0f}".replace(",", "."), delta="- Belum Lunas", delta_color="inverse")
    st.divider()

    tab1, tab2 = st.tabs(["📒 Buku Piutang & Pembayaran", "👥 Database Klien (CRM)"])

    # ==========================================
    # TAB 1: BUKU PIUTANG & PEMBAYARAN
    # ==========================================
    with tab1:
        st.markdown("### 💸 Pencatatan DP & Pelunasan")
        
        if df_piutang.empty:
            st.info("Belum ada data order untuk ditagih.")
        else:
            df_merge = pd.merge(df_piutang, df_pem[['ID Order', 'Nama Klien', 'Total Harga']], on="ID Order", how="left")
            df_belum_lunas = df_merge[df_merge['Status Pembayaran'] != 'Lunas']
            
            col_form, col_data = st.columns([1.2, 2])
            
            with col_form:
                st.markdown("#### 💳 Catat Pembayaran")
                if df_belum_lunas.empty:
                    st.success("🎉 Luar biasa! Semua tagihan klien saat ini sudah LUNAS.")
                else:
                    # =========================================================
                    # PERBAIKAN: SELECTBOX & INFO DITARUH DI LUAR FORM!
                    # =========================================================
                    daftar_tagihan = df_belum_lunas['ID Order'] + " - " + df_belum_lunas['Nama Klien']
                    pilih_order = st.selectbox("Pilih Tagihan:", daftar_tagihan)
                    
                    id_terpilih = pilih_order.split(" - ")[0]
                    data_order = df_belum_lunas[df_belum_lunas['ID Order'] == id_terpilih].iloc[0]
                    
                    # Tampilkan Info (Lengkap dengan Uang Masuk)
                    st.info(
                        f"**Total Tagihan:** Rp {float(data_order['Total Harga']):,.0f} \n\n"
                        f"**Uang Masuk (Sudah Dibayar):** Rp {float(data_order['Sudah Dibayar']):,.0f} \n\n"
                        f"**Sisa Hutang:** Rp {float(data_order['Sisa Tagihan']):,.0f}"
                    )
                    
                    # FORM HANYA UNTUK INPUT NOMINAL & TOMBOL
                    with st.form("form_bayar", clear_on_submit=True):
                        nominal_bayar = st.number_input("Nominal Bayar (Rp)", min_value=0.0, max_value=float(data_order['Sisa Tagihan']), step=50000.0)
                        catat_ke_keuangan = st.checkbox("Otomatis catat sebagai Pemasukan di Kas Keuangan", value=True)
                        
                        if st.form_submit_button("✅ Konfirmasi Pembayaran", type="primary", use_container_width=True):
                            if nominal_bayar > 0:
                                with st.spinner("Mencatat pembayaran..."):
                                    sudah_bayar_baru = float(data_order['Sudah Dibayar']) + nominal_bayar
                                    sisa_baru = float(data_order['Total Harga']) - sudah_bayar_baru
                                    status_baru = "Lunas" if sisa_baru <= 0 else "DP / Cicilan"
                                    
                                    df_piutang.loc[df_piutang['ID Order'] == id_terpilih, 'Sudah Dibayar'] = sudah_bayar_baru
                                    df_piutang.loc[df_piutang['ID Order'] == id_terpilih, 'Sisa Tagihan'] = sisa_baru
                                    df_piutang.loc[df_piutang['ID Order'] == id_terpilih, 'Status Pembayaran'] = status_baru
                                    conn.update(worksheet="Buku_Piutang", data=df_piutang)
                                    
                                    if catat_ke_keuangan:
                                        new_uang = pd.DataFrame([{
                                            "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                                            "Keterangan": f"Pembayaran {id_terpilih} ({status_baru})",
                                            "Pemasukan (Rp)": nominal_bayar,
                                            "Pengeluaran (Rp)": 0
                                        }])
                                        df_uang_baru = pd.concat([df_uang, new_uang], ignore_index=True)
                                        conn.update(worksheet="Keuangan", data=df_uang_baru)
                                        
                                    st.success(f"Pembayaran Rp {nominal_bayar:,.0f} berhasil dicatat!")
                                    st.cache_data.clear()
                                    st.rerun()
                            else:
                                st.error("Nominal harus lebih besar dari 0!")

            with col_data:
                st.markdown("#### 📊 Database Seluruh Piutang")
                kolom_tampil = ['ID Order', 'Nama Klien', 'Status Pembayaran', 'Total Harga', 'Sudah Dibayar', 'Sisa Tagihan']
                st.dataframe(df_merge[kolom_tampil], use_container_width=True, hide_index=True)

    # ==========================================
    # TAB 2: DATABASE KLIEN (CRM)
    # ==========================================
    with tab2:
        st.markdown("### 🏢 Buku Kontak & Profil Klien")
        col_f, col_d = st.columns([1, 2])
        
        with col_f:
            st.markdown("#### ➕ Tambah Kontak Baru")
            with st.form("form_klien", clear_on_submit=True):
                nama = st.text_input("Nama Klien / Instansi")
                wa = st.text_input("No. WhatsApp", placeholder="Contoh: 08123456789")
                alamat = st.text_area("Alamat Pengiriman")
                kategori = st.selectbox("Kategori Klien", ["Reguler", "VIP (Langganan)", "Corporate"])
                
                if st.form_submit_button("💾 Simpan Kontak", use_container_width=True):
                    if nama != "":
                        new_klien = pd.DataFrame([{"Nama Klien": nama, "No WA": wa, "Alamat": alamat, "Kategori": kategori}])
                        df_klien = pd.concat([df_klien, new_klien], ignore_index=True)
                        conn.update(worksheet="Database_Klien", data=df_klien)
                        st.success(f"Kontak {nama} berhasil disimpan!")
                        st.cache_data.clear(); st.rerun()
                    else:
                        st.error("Nama Klien wajib diisi!")
        
        with col_d:
            st.markdown("#### 📋 Daftar Klien Terdaftar")
            if df_klien.empty:
                st.info("Belum ada data klien yang terdaftar.")
            else:
                for idx, row in df_klien.iterrows():
                    with st.container(border=True):
                        c_info, c_btn = st.columns([3, 1])
                        c_info.markdown(f"**{row.get('Nama Klien', 'Tanpa Nama')}** — *( {row.get('Kategori', 'Reguler')} )*")
                        c_info.caption(f"📍 {row.get('Alamat', '-')}")
                        
                        no_wa = str(row.get('No WA', '')).replace('0', '62', 1) if str(row.get('No WA', '')).startswith('0') else str(row.get('No WA', ''))
                        
                        if no_wa:
                            c_btn.markdown(f"<a href='https://wa.me/{no_wa}' target='_blank'><button style='width:100%; border-radius:5px; background-color:#25D366; color:white; border:none; padding:8px; font-weight:bold; cursor:pointer;'>💬 Chat WA</button></a>", unsafe_allow_html=True)
                        else:
                            c_btn.button("No WA Kosong", disabled=True, key=f"wa_{idx}")