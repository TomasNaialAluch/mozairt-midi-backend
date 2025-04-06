from flask import Flask, request, jsonify
import cloudinary
import cloudinary.uploader
from music21 import converter, tempo, key, meter, environment
from flask_cors import CORS, cross_origin
import os

app = Flask(__name__)
CORS(app)

# Configuración de Cloudinary
cloudinary.config(
    cloud_name='dnj7o6fdq',
    api_key='5645396388878616',
    api_secret='Y9HKvWqnjTlUDmbH-xeXNW5uvBE'
)

# Configuración de music21
env = environment.UserSettings()
env['warnings'] = 0

@app.route('/analyze', methods=['POST'])
@cross_origin()
def analyze_midi():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    midi_file = request.files['file']
    try:
        score = converter.parse(midi_file)
        key_estimated = score.analyze('key')

        bpm = 120
        tempos = score.flat.getElementsByClass(tempo.MetronomeMark)
        if tempos:
            bpm = tempos[0].number

        ts = score.recurse().getElementsByClass(meter.TimeSignature)
        time_signature = str(ts[0]) if ts else 'Unknown'

        measures = 'Unknown'
        if score.parts:
            measures = len(score.parts[0].getElementsByClass('Measure'))

        return jsonify({
            'bpm': bpm,
            'key': f"{key_estimated.tonic} {key_estimated.mode}",
            'time_signature': time_signature,
            'measures': measures
        })
    except Exception as e:
        print(f"Error al analizar MIDI: {str(e)}")
        return jsonify({'error': 'Error en el análisis MIDI. Revisa la consola para más detalles.'}), 500

@app.route('/upload-midi', methods=['POST'])
@cross_origin()
def upload_midi():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    try:
        if file:
            file.save(f"uploaded_{file.filename}")
            return jsonify({'message': 'File uploaded successfully', 'filename': file.filename}), 200
        else:
            return jsonify({'error': 'No file content'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
