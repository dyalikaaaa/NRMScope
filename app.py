from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text

app = Flask(__name__)

# Koneksi ke SQLite lokal
engine = create_engine("sqlite:///nrmscope.db")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/filter-options', methods=['GET'])
def get_filter_options():
    with engine.connect() as conn:
        tahun = [row[0] for row in conn.execute(text("SELECT DISTINCT tahun FROM data_pengangguran ORDER BY tahun DESC"))]
        provinsi = [row[0] for row in conn.execute(text("SELECT nama_provinsi FROM wilayah ORDER BY nama_provinsi ASC"))]
        pendidikan = [row[0] for row in conn.execute(text("SELECT DISTINCT tingkat_pendidikan FROM data_pengangguran"))]
        gender = [row[0] for row in conn.execute(text("SELECT DISTINCT jenis_kelamin FROM data_pengangguran"))]
        
    return jsonify({
        'tahun': tahun,
        'provinsi': provinsi,
        'pendidikan': pendidikan,
        'gender': gender
    })

@app.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data():
    p_tahun = request.args.get('tahun', 'All')
    p_provinsi = request.args.get('provinsi', 'All')
    p_pendidikan = request.args.get('pendidikan', 'All')
    p_gender = request.args.get('gender', 'All')

    query = """
        SELECT d.tahun, w.nama_provinsi, d.jenis_kelamin, d.tingkat_pendidikan, d.jumlah_pengangguran, d.tpt_persen
        FROM data_pengangguran d
        JOIN wilayah w ON d.id_provinsi = w.id_provinsi
        WHERE 1=1
    """
    params = {}

    if p_tahun != 'All':
        query += " AND d.tahun = :tahun"
        params['tahun'] = p_tahun
    if p_provinsi != 'All':
        query += " AND w.nama_provinsi = :provinsi"
        params['provinsi'] = p_provinsi
    if p_pendidikan != 'All':
        query += " AND d.tingkat_pendidikan = :pendidikan"
        params['pendidikan'] = p_pendidikan
    if p_gender != 'All':
        query += " AND d.jenis_kelamin = :gender"
        params['gender'] = p_gender

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        data = [dict(row._mapping) for row in result]

    total_pengangguran = sum(item['jumlah_pengangguran'] for item in data) if data else 0
    avg_tpt = round(sum(item['tpt_persen'] for item in data) / len(data), 2) if data else 0

    return jsonify({
        'summary': {
            'total_pengangguran': total_pengangguran,
            'avg_tpt': avg_tpt,
            'total_record': len(data)
        },
        'detail_data': data
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)