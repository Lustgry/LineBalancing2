import pandas as pd

def load_data(uploaded_file):
    """
    Membaca file Excel dengan pembersihan data tingkat lanjut
    agar tahan terhadap kesalahan format input user.
    """
    try:
        df = pd.read_excel(uploaded_file)
        
        # 1. Normalisasi Nama Kolom (Semua jadi Huruf Besar & Hapus Spasi)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Kamus untuk menebak nama kolom yang mungkin dipakai user
        # Contoh: User nulis "Waktu" atau "Duration" tetap terbaca sebagai "Time"
        col_map = {
            'TASK': 'Task', 'KODE': 'Task', 'AKTIVITAS': 'Task', 'ACTIVITY': 'Task',
            'TIME': 'Time', 'WAKTU': 'Time', 'DURASI': 'Time', 'DURATION': 'Time', 'ST': 'Time',
            'PREDECESSORS': 'Predecessors', 'PREDECESSOR': 'Predecessors', 
            'PENDAHULU': 'Predecessors', 'DEPENDENCY': 'Predecessors'
        }
        
        # Rename kolom sesuai standar
        df = df.rename(columns=col_map)
        
        # Validasi Kolom Wajib
        required_cols = ['Task', 'Time', 'Predecessors']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return None, f"Kolom Excel tidak sesuai. Wajib ada: {', '.join(required_cols)}. (Kolom Anda: {', '.join(df.columns)})"

        # 2. Bersihkan Kolom 'Task' (Hapus spasi, jadi huruf besar)
        df['Task'] = df['Task'].astype(str).str.strip().str.upper()
        
        # 3. Bersihkan Kolom 'Time' (Pastikan angka)
        # Jika user pakai koma (2,5), ganti jadi titik (2.5) jika terbaca string
        if df['Time'].dtype == 'object':
             df['Time'] = df['Time'].astype(str).str.replace(',', '.')
        
        df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
        
        if df['Time'].isnull().any():
            return None, "Kolom 'Time' mengandung data yang bukan angka/kosong."

        # 4. Bersihkan Kolom 'Predecessors' (BAGIAN KRUSIAL)
        df['Predecessors'] = df['Predecessors'].fillna('').astype(str)
        
        def clean_preds(val):
            # Ganti titik koma (;) jadi koma (,) jaga-jaga user salah separator
            val = val.replace(';', ',')
            parts = val.split(',')
            cleaned = []
            for p in parts:
                p = p.strip().upper() # Hapus spasi & uppercase
                # HAPUS tanda strip (-), 0, nan, none.
                # Hanya simpan jika p adalah kode task yang valid (misal: 'A')
                invalid_chars = ['-', '0', 'NONE', 'NAN', 'NA', '']
                if p not in invalid_chars:
                    cleaned.append(p)
            return cleaned

        df['Predecessors'] = df['Predecessors'].apply(clean_preds)
        
        # Mengembalikan data bersih
        data = df.to_dict('records')
        return data, None
        
    except Exception as e:
        return None, f"Error Sistem saat membaca file: {str(e)}"