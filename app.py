import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from data_loader import load_data

# Import fungsi algoritma
from methods.lcr import solve_lcr
from methods.rpw import solve_rpw
from methods.mdy import solve_mdy

# Import modul AI Baru (Gimita)
from ai_advisor import get_ai_suggestions, chat_with_data, construct_context

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Line Balancing App", layout="wide")

# --- SESSION STATE ---
if 'hasil_perhitungan' not in st.session_state:
    st.session_state['hasil_perhitungan'] = None
if 'metode_terpilih' not in st.session_state:
    st.session_state['metode_terpilih'] = ""
# State untuk Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- JUDUL ---
st.title("📱Line Balancing Calculator")
st.markdown("Aplikasi optimasi lintasan produksi dengan AI Assistant.")
st.divider()

# --- SIDEBAR: INPUT ---
st.sidebar.header("1. Input Data")
uploaded_file = st.sidebar.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

# (Input API Key Dihapus karena menggunakan API Gimita custom)

if uploaded_file is not None:
    # Load Data
    data, error_msg = load_data(uploaded_file)
    
    if error_msg:
        st.error(f" Terjadi Kesalahan: {error_msg}")
    else:
        # --- PARAMETER ---
        st.sidebar.header("2. Parameter")
        max_task_time = max([t['Time'] for t in data])
        
        cycle_time = st.sidebar.number_input(
            "Cycle Time (Detik/Menit)", 
            min_value=int(max_task_time), 
            value=max(10, int(max_task_time)),
            help="Cycle Time tidak boleh lebih kecil dari waktu tugas terpanjang."
        )
        
        st.sidebar.header("3. Metode")
        method_option = st.sidebar.selectbox(
            "Pilih Algoritma", 
            ["LCR (Largest Candidate Rule)", "RPW (Ranked Positional Weight)", "MDY (Moodie Young)"]
        )
        
        # Tombol Hitung
        if st.sidebar.button("Hitung Keseimbangan"):
            # Reset Chat History saat hitung ulang agar konteks baru
            st.session_state.messages = []
            
            result = []
            if "LCR" in method_option:
                result = solve_lcr(data, cycle_time)
            elif "RPW" in method_option:
                result = solve_rpw(data, cycle_time)
            elif "MDY" in method_option:
                result = solve_mdy(data, cycle_time)
            
            st.session_state['hasil_perhitungan'] = result
            st.session_state['metode_terpilih'] = method_option
            st.rerun()

        # --- TAMPILAN DATA MENTAH ---
        with st.expander("Lihat Data Input Mentah", expanded=True):
            df_view = pd.DataFrame(data)
            df_view['Predecessors'] = df_view['Predecessors'].apply(lambda x: ", ".join(x) if x else "-")
            st.dataframe(df_view, width='stretch')

        # --- TAMPILAN HASIL ---
        hasil = st.session_state['hasil_perhitungan']
        metode = st.session_state['metode_terpilih']

        if hasil is not None:
            st.divider()
            
            if isinstance(hasil, str):
                st.error(f"Gagal: {hasil}")
            else:
                st.subheader(f" Hasil Perhitungan: {metode}")
                
                # SIAPKAN DATA RINGKASAN
                summary_data = []
                for stn in hasil:
                    waktu_terpakai = cycle_time - stn['time_left']
                    efisiensi_stasiun = (waktu_terpakai / cycle_time) * 100
                    summary_data.append({
                        "Stasiun": f"Stasiun {stn['id']}",
                        "Daftar Tugas": ", ".join(stn['tasks']),
                        "Waktu Terpakai": waktu_terpakai,
                        "Idle Time": stn['time_left'],
                        "Efisiensi (%)": round(efisiensi_stasiun, 1)
                    })
                
                df_summary = pd.DataFrame(summary_data)

                # Hitung Metrik Global
                num_stations = len(hasil)
                total_time_used = df_summary["Waktu Terpakai"].sum()
                global_efficiency = (total_time_used / (num_stations * cycle_time)) * 100
                balance_delay = 100 - global_efficiency

                # KPI
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Jumlah Stasiun", num_stations)
                c2.metric("Cycle Time", cycle_time)
                c3.metric("Efisiensi Lintasan", f"{global_efficiency:.1f}%")
                c4.metric("Balance Delay", f"{balance_delay:.1f}%")

                # GRAFIK
                st.write("### Grafik Beban Kerja")
                fig, ax = plt.subplots(figsize=(10, 4))
                bars = ax.bar(df_summary['Stasiun'], df_summary['Waktu Terpakai'], color='#2E86C1', zorder=3)
                ax.axhline(y=cycle_time, color='red', linestyle='--', linewidth=2, label=f'Cycle Time ({cycle_time})', zorder=4)
                ax.set_ylabel("Waktu")
                ax.legend(loc='lower right')
                ax.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + (cycle_time * 0.02),
                            f'{height}', ha='center', va='bottom', fontsize=9, fontweight='bold')
                st.pyplot(fig)

                # TABEL
                st.write("### 📑 Rincian Tabel")
                st.dataframe(
                    df_summary.style.background_gradient(subset=['Efisiensi (%)'], cmap="RdYlGn"),
                    width='stretch'
                )

                # --- BAGIAN 1: AI ADVISOR (Analisis Otomatis) ---
                st.divider()
                st.subheader("Analisa Otomatis")
                
                if st.button("Minta Analisis Cepat "):
                    with st.spinner("Menghubungi Gimita AI..."):
                        saran = get_ai_suggestions(
                            method_name=metode,
                            cycle_time=cycle_time,
                            efficiency=global_efficiency,
                            stations_data=summary_data
                        )
                        st.success("Analisis Selesai!")
                        st.info(saran)

                # --- BAGIAN 2: CHATBOT INTERAKTIF ---
                st.divider()
                st.subheader("💬 Chat Ai")
                st.caption("Tanyakan apa saja mengenai hasil perhitungan di atas.")

                # Tampilkan riwayat chat
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                # Input Chat User
                if prompt := st.chat_input("Contoh: Stasiun mana yang paling sibuk?"):
                    # Simpan pesan user
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    # Proses Jawaban AI
                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        message_placeholder.markdown("Sedang mengetik...")
                        
                        # Bangun konteks data terkini
                        context_str = construct_context(metode, cycle_time, global_efficiency, summary_data)
                        
                        # Panggil API Gimita untuk Chat
                        full_response = chat_with_data(prompt, context_str)
                        
                        message_placeholder.markdown(full_response)
                    
                    # Simpan jawaban AI
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

else:
    st.info("Upload file Excel untuk memulai.")