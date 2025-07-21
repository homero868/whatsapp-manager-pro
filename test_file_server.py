# test_file_server.py - Servidor independiente para pruebas

from flask import Flask, send_file, jsonify, abort
import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config

app = Flask(__name__)
UPLOAD_FOLDER = Config.UPLOAD_FOLDER

@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Servidor de archivos funcionando',
        'upload_folder': UPLOAD_FOLDER
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/uploads/<path:filepath>')
def serve_file(filepath):
    """Servir archivo desde la carpeta de uploads"""
    try:
        full_path = os.path.join(UPLOAD_FOLDER, filepath)
        print(f"Sirviendo archivo: {full_path}")
        
        if not os.path.exists(full_path):
            print(f"Archivo no encontrado: {full_path}")
            abort(404)
        
        return send_file(full_path)
        
    except Exception as e:
        print(f"Error: {e}")
        abort(500)

@app.route('/test')
def test():
    """Listar archivos disponibles"""
    files = []
    for root, dirs, filenames in os.walk(UPLOAD_FOLDER):
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(root, filename), UPLOAD_FOLDER)
            files.append(rel_path.replace('\\', '/'))
    
    return jsonify({
        'upload_folder': UPLOAD_FOLDER,
        'files': files
    })

if __name__ == '__main__':
    print(f"Iniciando servidor en puerto 8888...")
    print(f"Carpeta de uploads: {UPLOAD_FOLDER}")
    print(f"Archivos disponibles en: http://localhost:8888/test")
    app.run(host='0.0.0.0', port=8888, debug=True)
