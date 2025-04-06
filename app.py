import cloudinary
import cloudinary.uploader
from flask import Flask, request, jsonify
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
        score = converter.parse(midi_file)
        bpm = 120

        tempos = score.flat.getElementsByClass(tempo.MetronomeMark)
        if tempos:
            bpm = tempos[0].number

        keys = score.analyze('key')
        ts = score.recurse().getElementsByClass(meter.TimeSignature)

        return jsonify({
            'bpm': bpm,
            'key': str(keys),
            'time_signature': str(ts[0]) if ts else 'Unknown',
            'measures': len(score.parts[0].getElementsByClass('Measure')) if score.parts else 'Unknown'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload-midi', methods=['POST'])
def upload_midi():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    try:
        result = cloudinary.uploader.upload_large(request.files['file'], resource_type="raw")
        return jsonify({'url': result['secure_url']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
