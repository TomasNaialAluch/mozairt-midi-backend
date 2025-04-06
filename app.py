from flask import Flask, request, jsonify
import cloudinary
import cloudinary.uploader
from music21 import converter, tempo, key, meter, environment

app = Flask(__name__)

# Configuración de Cloudinary
cloudinary.config(
    cloud_name='dnj7o6fdq',
    api_key='5645396388878616',
    api_secret='Y9HKvWqnjTlUDmbH-xeXNW5uvBE'
)

# Opcional: Configurar logging de music21 para ver detalles en la consola
env = environment.UserSettings()
env['warnings'] = 0

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
        
        # Calcular BPM a partir de MetronomeMark (si está disponible)
        bpm = 120  # Valor por defecto
        tempos = score.flat.getElementsByClass(tempo.MetronomeMark)
        if tempos:
            bpm = tempos[0].number

        # Calcular Time Signature
        ts = score.recurse().getElementsByClass(meter.TimeSignature)
        time_signature = str(ts[0]) if ts else 'Unknown'

        # Obtener la cantidad de compases (asegúrate de que el score tenga parts)
        measures = 'Unknown'
        if score.parts:
            measures = len(score.parts[0].getElementsByClass('Measure'))

        # Retornar los datos extraídos
        return jsonify({
            'bpm': bpm,
            'key': f"{key_estimated.tonic} {key_estimated.mode}",
            'time_signature': time_signature,
            'measures': measures
        })
    except Exception as e:
        # Imprimir el error completo para facilitar la depuración
        print(f"Error al analizar MIDI: {str(e)}")
        return jsonify({'error': 'Error en el análisis MIDI. Revisa la consola para más detalles.'}), 500

@app.route('/upload-midi', methods=['POST'])
def upload_midi():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    try:
        if file:
            # Guarda temporalmente el archivo en el servidor local (opcional)
            file.save(f"uploaded_{file.filename}")
            return jsonify({'message': 'File uploaded successfully', 'filename': file.filename}), 200
        else:
            return jsonify({'error': 'No file content'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
