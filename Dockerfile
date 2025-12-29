# 1. Gunakan Python 3.10 versi ringan (slim) sebagai dasar
FROM python:3.10-slim

# 2. Set folder kerja di dalam container
WORKDIR /app

# 3. Salin file requirements.txt ke dalam container
COPY requirements.txt .

# 4. Install library yang dibutuhkan (tanpa cache agar image lebih kecil)
RUN pip install --no-cache-dir -r requirements.txt

# 5. Salin seluruh kode proyek Anda (app.py, methods/, dll) ke dalam container
COPY . .

# 6. Buka port 8501 (Port default Streamlit)
EXPOSE 8501

# 7. Perintah untuk menjalankan aplikasi saat container hidup
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]