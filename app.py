from flask import Flask, request, jsonify
import traceback

import cloudinary
import cloudinary.uploader
from music21 import converter, tempo, key, meter, environment, chord, note, pitch
from flask_cors import CORS
import os
import logging
import traceback  # Importación faltante para traceback
from werkzeug.utils import secure_filename

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración de CORS más estricta
CORS(app, resources={
    r"/analyze": {
        "origins": ["https://mozairt-app-git-main-naials-projects.vercel.app"],
        "methods": ["POST"],
        "allow_headers": ["Content-Type"]
    },
    r"/upload-midi": {
        "origins": ["https://mozairt-app-git-main-naials-projects.vercel.app"],
        "methods": ["POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Configuración de Cloudinary (deberías usar variables de entorno en producción)
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'dnj7o6fdq'),
    api_key=os.getenv('CLOUDINARY_API_KEY', '5645396388878616'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', 'Y9HKvWqnjTlUDmbH-xeXNW5uvBE')
)

# Configuración de music21
env = environment.UserSettings()
env['warnings'] = 0

# Extensiones permitidas
ALLOWED_EXTENSIONS = {'mid', 'midi'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/analyze', methods=['POST'])
def analyze_midi():
    """Endpoint para análisis avanzado de archivos MIDI"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    midi_file = request.files['file']
    
    if not midi_file or midi_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(midi_file.filename):
        return jsonify({'error': 'Invalid file type. Only .mid or .midi files are allowed.'}), 400

    try:
        # Usar análisis más robusto de music21
        score = converter.parse(midi_file)

        
        # Análisis de tonalidad mejorado
        key_analysis = score.analyze('key.krumhansl')
        
        # Detección de BPM con manejo de errores
        bpm = 120  # Valor por defecto
        tempos = score.flat.getElementsByClass(tempo.MetronomeMark)
        if tempos and hasattr(tempos[0], 'number'):
            bpm = tempos[0].number

        # Detección de compás
        time_signature = '4/4'  # Valor por defecto
        ts_elements = score.flat.getElementsByClass(meter.TimeSignature)
        if ts_elements:
            ts = ts_elements[0]
            time_signature = f"{ts.numerator}/{ts.denominator}"

        # Análisis de estructura
        measures = len(score.parts[0].getElementsByClass('Measure')) if score.parts else 0
        
        # Extraer información de notas y acordes
        note_info = analyze_notes_and_chords(score)

        return jsonify({
            'status': 'success',
            'analysis': {
                'bpm': bpm,
                'key': {
                    'tonic': str(key_analysis.tonic),
                    'mode': key_analysis.mode,
                    'correlation': round(key_analysis.correlationCoefficient, 3)
                },
                'time_signature': time_signature,
                'measures': measures,
                'note_info': note_info
            }
        })

    except Exception as e:
        logger.error(f"Error analyzing MIDI: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Error processing MIDI file',
            'details': str(e)
        }), 500

def analyze_notes_and_chords(score):
    """Analiza la distribución de notas y acordes en el score"""
    notes = []
    chords = []
    
    for element in score.flat.notes:
        if isinstance(element, note.Note):
            notes.append({
                'pitch': element.pitch.name,
                'octave': element.pitch.octave,
                'midi': element.pitch.midi,
                'duration': element.duration.quarterLength
            })
        elif isinstance(element, chord.Chord):
            chords.append({
                'pitches': [p.nameWithOctave for p in element.pitches],
                'midi_values': [p.midi for p in element.pitches],
                'duration': element.duration.quarterLength
            })
    
    return {
        'total_notes': len(notes),
        'total_chords': len(chords),
        'pitch_range': get_pitch_range(notes + chords),
        'note_distribution': get_note_distribution(notes)
    }

def get_pitch_range(elements):
    """Calcula el rango de notas (mínimo y máximo)"""
    if not elements:
        return None
    
    midi_values = []
    for el in elements:
        if 'midi' in el:
            midi_values.append(el['midi'])
        elif 'midi_values' in el:
            midi_values.extend(el['midi_values'])
    
    if not midi_values:
        return None
    
    return {
        'min': min(midi_values),
        'max': max(midi_values),
        'min_note': pitch.Pitch(min(midi_values)).nameWithOctave,
        'max_note': pitch.Pitch(max(midi_values)).nameWithOctave
    }

def get_note_distribution(notes):
    """Calcula la distribución de notas"""
    distribution = {}
    for n in notes:
        pitch_name = n['pitch']
        distribution[pitch_name] = distribution.get(pitch_name, 0) + 1
    return distribution

@app.route('/upload-midi', methods=['POST'])
def upload_midi():
    """Endpoint para subir archivos MIDI a Cloudinary"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    
    if not file or file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only .mid or .midi files are allowed.'}), 400

    try:
        # Crear directorio temporal si no existe
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Usar nombre seguro para el archivo
        filename = secure_filename(file.filename)
        temp_filepath = os.path.join(temp_dir, filename)
        
        # Guardar el archivo temporalmente
        file.save(temp_filepath)
        
        logger.info(f"Uploading file: {filename}")

        # Subir a Cloudinary con opciones adicionales
        upload_result = cloudinary.uploader.upload(
            temp_filepath,
            resource_type="raw",
            folder="mozairt/midi_uploads/",
            public_id=f"mozairt_{os.path.splitext(filename)[0]}",
            overwrite=True,
            use_filename=True,
            unique_filename=False
        )

        # Eliminar archivo temporal
        os.remove(temp_filepath)

        if not upload_result.get('secure_url'):
            raise Exception("Cloudinary upload failed")

        return jsonify({
            'status': 'success',
            'url': upload_result['secure_url'],
            'public_id': upload_result['public_id'],
            'format': upload_result['format']
        })

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Asegurarse de eliminar el archivo temporal en caso de error
        if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
            os.remove(temp_filepath)
            
        return jsonify({
            'error': 'File upload failed',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get('DEBUG', False))