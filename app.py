from flask import Flask, request, jsonify
import cloudinary
import cloudinary.uploader
from music21 import converter, tempo, key, meter, environment
from flask_cors import CORS, cross_origin
import os
import traceback

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
        # Validar extensión del archivo
        if not midi_file.filename.lower().endswith(('.mid', '.midi')):
            return jsonify({'error': 'Invalid file type. Only .mid or .midi files are allowed.'}), 400

        # Analizar el archivo MIDI
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
        # Validar extensión del archivo
        if not file.filename.lower().endswith(('.mid', '.midi')):
            return jsonify({'error': 'Invalid file type. Only .mid or .midi files are allowed.'}), 400

        # Guardar el archivo temporalmente
        temp_filepath = f"uploaded_{file.filename}"
        file.save(temp_filepath)

        # Subir el archivo a Cloudinary
        upload_result = cloudinary.uploader.upload(
            temp_filepath,
            resource_type="raw",
            public_id=f"midi/{file.filename}",
            overwrite=True
        )

        # Eliminar el archivo temporal
        os.remove(temp_filepath)

        # Devolver la URL del archivo subido
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': file.filename,
            'url': upload_result.get('secure_url')
        }), 200

    except Exception as e:
        import traceback
        return jsonify({
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)