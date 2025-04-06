from flask import Flask, request, jsonify
import cloudinary
import cloudinary.uploader
from music21 import converter, tempo, key, meter

app = Flask(__name__)

# Configuración de Cloudinary
cloudinary.config(
    cloud_name='dnj7o6fdq',
    api_key='5645396388878616',
    api_secret='Y9HKvWqnjTlUDmbH-xeXNW5uvBE'
)

@app.route('/analyze', methods=['POST'])
def analyze_midi():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    midi_file = request.files['file']
    try:
        # Parsear el archivo MIDI usando music21
        score = converter.parse(midi_file)
        
        # Analizar la tonalidad utilizando el algoritmo Krumhansl-Schmuckler
        key_estimated = score.analyze('key')
        
        # Calcular BPM
        bpm = 120
        tempos = score.flat.getElementsByClass(tempo.MetronomeMark)
        if tempos:
            bpm = tempos[0].number

        # Calcular Time Signature
        ts = score.recurse().getElementsByClass(meter.TimeSignature)

        # Devolver los datos analizados
        return jsonify({
            'bpm': bpm,
            'key': f"{key_estimated.tonic} {key_estimated.mode}",  # Tonalidad: tónica + modo (mayor o menor)
            'time_signature': str(ts[0]) if ts else 'Unknown',
            'measures': len(score.parts[0].getElementsByClass('Measure')) if score.parts else 'Unknown'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Manejo de errores

@app.route('/upload-midi', methods=['POST'])
def upload_midi():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    try:
        # Subir archivo MIDI a Cloudinary
        result = cloudinary.uploader.upload_large(request.files['file'], resource_type="raw")
        return jsonify({'url': result['secure_url']})  # Devuelve la URL del archivo subido
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Si el script se ejecuta directamente (y no importado)
if __name__ == '__main__':
    app.run(debug=True)  # Inicia la aplicación en modo debug
