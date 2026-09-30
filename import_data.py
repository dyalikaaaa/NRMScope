import random
import pandas as pd
from sqlalchemy import create_engine, text

# Menggunakan SQLite lokal
engine = create_engine("sqlite:///nrmscope.db")

# Daftar Lengkap 38 Provinsi di Indonesia
DAFTAR_PROVINSI = [
    "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Jambi", "Sumatera Selatan", 
    "Bengkulu", "Lampung", "Kepulauan Bangka Belitung", "Kepulauan Riau", "DKI Jakarta", 
    "Jawa Barat", "Jawa Tengah", "DI Yogyakarta", "Jawa Timur", "Banten", "Bali", 
    "Nusa Tenggara Barat", "Nusa Tenggara Timur", "Kalimantan Barat", "Kalimantan Tengah", 
    "Kalimantan Selatan", "Kalimantan Timur", "Kalimantan Utara", "Sulawesi Utara", 
    "Sulawesi Tengah", "Sulawesi Selatan", "Sulawesi Tenggara", "Gorontalo", "Sulawesi Barat", 
    "Maluku", "Maluku Utara", "Papua", "Papua Barat", "Papua Selatan", "Papua Tengah", 
    "Papua Pegunungan", "Papua Barat Daya"
]

TAHUN_LIST = list(range(2010, 2027)) # 2010 sampai 2026
PENDIDIKAN_LIST = ["SD/SMP", "SMA/SMK", "Diploma (D3)", "Sarjana (S1)"]
GENDER_LIST = ["Laki-laki", "Perempuan"]

def generate_dataset():
    data = []
    random.seed(42) # Agar angka konsisten setiap kali di-generate
    
    for prov in DAFTAR_PROVINSI:
        # Faktor skala populasi tiap provinsi
        skala = 10 if prov in ["DKI Jakarta", "Jawa Barat", "Jawa Tengah", "Jawa Timur"] else (3 if "Sulawesi" in prov or "Sumatera" in prov else 1)
        
        for thn in TAHUN_LIST:
            for edu in PENDIDIKAN_LIST:
                for gen in GENDER_LIST:
                    # Estimasi jumlah pengangguran & TPT (%) berdasar tren realistis
                    dasar_pengangguran = random.randint(3000, 25000) * skala
                    # Tren dampak pandemi 2020-2021 sedikit meningkat
                    faktor_tahun = 1.25 if thn in [2020, 2021] else 1.0
                    
                    jumlah_pengangguran = int(dasar_pengangguran * faktor_tahun)
                    tpt_persen = round(random.uniform(2.5, 9.8), 2)
                    
                    data.append({
                        "provinsi": prov,
                        "tahun": thn,
                        "jenis_kelamin": gen,
                        "tingkat_pendidikan": edu,
                        "jumlah_pengangguran": jumlah_pengangguran,
                        "tpt_persen": tpt_persen
                    })
    return pd.DataFrame(data)

def init_db_and_import():
    print("Membuat struktur database...")
    with engine.connect() as conn:
        # Hapus tabel lama jika ada agar bersih
        conn.execute(text("DROP TABLE IF EXISTS data_pengangguran;"))
        conn.execute(text("DROP TABLE IF EXISTS wilayah;"))
        
        # Buat Tabel Wilayah
        conn.execute(text("""
            CREATE TABLE wilayah (
                id_provinsi INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_provinsi VARCHAR(100) NOT NULL UNIQUE
            );
        """))
        
        # Buat Tabel Data Pengangguran
        conn.execute(text("""
            CREATE TABLE data_pengangguran (
                id_data INTEGER PRIMARY KEY AUTOINCREMENT,
                id_provinsi INT NOT NULL,
                tahun INT NOT NULL,
                jenis_kelamin VARCHAR(20) NOT NULL,
                tingkat_pendidikan VARCHAR(50) NOT NULL,
                jumlah_pengangguran BIGINT DEFAULT 0,
                tpt_persen FLOAT DEFAULT 0.0,
                FOREIGN KEY (id_provinsi) REFERENCES wilayah(id_provinsi) ON DELETE CASCADE
            );
        """))
        conn.commit()

    print("Menggenerate data untuk 38 Provinsi (Tahun 2010 - 2026)...")
    df = generate_dataset()

    # Insert Wilayah
    prov_df = df[['provinsi']].drop_duplicates()
    prov_df.columns = ['nama_provinsi']
    with engine.connect() as conn:
        for p in prov_df['nama_provinsi']:
            conn.execute(text("INSERT INTO wilayah (nama_provinsi) VALUES (:p)"), {"p": p})
        conn.commit()

    # Ambil Map ID Wilayah
    wilayah_map = pd.read_sql("SELECT id_provinsi, nama_provinsi FROM wilayah", con=engine)
    df = df.merge(wilayah_map, left_on='provinsi', right_on='nama_provinsi')

    # Insert Data Utama
    final_df = df[['id_provinsi', 'tahun', 'jenis_kelamin', 'tingkat_pendidikan', 'jumlah_pengangguran', 'tpt_persen']]
    final_df.to_sql('data_pengangguran', con=engine, if_exists='append', index=False)
    
    print(f"BERHASIL! Sebanyak {len(final_df)} baris data telah dimasukkan ke database.")

if __name__ == "__main__":
    init_db_and_import()