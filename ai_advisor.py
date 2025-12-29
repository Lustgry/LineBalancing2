import requests
import urllib.parse
import json

def call_gimita_api(prompt_text):
    """
    Fungsi dasar untuk memanggil API Gimita ID via HTTP GET
    """
    try:
        # Encode prompt agar aman untuk URL
        encoded_prompt = urllib.parse.quote(prompt_text)
        
        # URL Endpoint
        url = f"https://api.gimita.id/api/ai/gpt4?prompt={encoded_prompt}"
        
        # Kirim Request GET
        response = requests.get(url)
        
        # Cek status sukses (200 OK)
        if response.status_code == 200:
            try:
                data = response.json()
                
                # --- PERBAIKAN DI SINI ---
                # 1. Cek struktur: {'data': {'answer': 'TEKS JAWABAN'}} (Sesuai log error anda)
                if 'data' in data and isinstance(data['data'], dict) and 'answer' in data['data']:
                    return data['data']['answer']
                
                # 2. Cek struktur alternatif: {'content': 'TEKS JAWABAN'}
                elif 'content' in data:
                    return data['content']
                    
                # 3. Cek struktur alternatif: {'message': 'TEKS JAWABAN'}
                elif 'message' in data:
                    return data['message']
                
                # Jika format tidak dikenali, baru tampilkan mentahnya (untuk debugging)
                return str(data) 
                
            except ValueError:
                # Jika returnnya bukan JSON, tapi langsung text
                return response.text
        else:
            return f"Error API: Status Code {response.status_code}"
            
    except Exception as e:
        return f"Error Koneksi: {str(e)}"

def construct_context(method_name, cycle_time, efficiency, stations_data):
    """
    Membuat ringkasan data untuk 'Otak' Chatbot agar dia tahu konteks.
    """
    data_str = ""
    for stn in stations_data:
        data_str += f"- {stn['Stasiun']}: Waktu Terpakai={stn['Waktu Terpakai']}, Eff={stn['Efisiensi (%)']}%, Tugas={stn['Daftar Tugas']}\n"
    
    context = f"""
    [KONTEKS DATA PERHITUNGAN SAAT INI]
    - Metode: {method_name}
    - Cycle Time: {cycle_time}
    - Efisiensi Total: {efficiency:.2f}%
    - Detail Stasiun:
    {data_str}
    """
    return context

def get_ai_suggestions(method_name, cycle_time, efficiency, stations_data):
    """
    Fitur 1: Analisis Satu Arah (Advisor)
    """
    context = construct_context(method_name, cycle_time, efficiency, stations_data)
    
    prompt = f"""
    Anda adalah seorang analis ahli Line Balancing.
    Berikut adalah data hasil perhitungan saya:
    {context}
    
    Tugasmu:
    1. Identifikasi Bottleneck.
    2. Identifikasi Idle Time.
    3. Berikan 3 saran perbaikan singkat.
    4. Apakah perlu penambahan stasiun?
    5. Apakah metode line balancing yang digunakan sudah tepat? Jika tidak, metode apa
    
    Jawab dalam Bahasa Indonesia yang profesional.
    """
    return call_gimita_api(prompt)

def chat_with_data(user_question, context_string):
    """
    Fitur 2: Chatbot Interaktif
    """
    prompt = f"""
    Kamu adalah asisten Line Balancing.
    Gunakan data berikut sebagai acuan jawabanmu:
    {context_string}
    
    Pertanyaan User: {user_question}
    
    Jawablah pertanyaan user berdasarkan data di atas dengan singkat dan jelas.
    """
    return call_gimita_api(prompt)