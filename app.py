from flask import Flask, request, jsonify
from music21 import converter, tempo, meter, key, note, chord
import tempfile

app = Flask(__name__)

@app.route("/", methods=["GET"])
def ping():
    return "MozAIrt backend funcionando 🎵"

@app.route("/analizar-midi", methods=["POST"])
def analizar_midi():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No se envió archivo"}), 400

        file = request.files['file']

        # Guardar archivo temporal
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            file.save(tmp.name)
            midi = converter.parse(tmp.name)

        # Análisis básico
        bpm = None
        ts = None
        tonalidad = None
        total_notas = 0

        # Tempo
        for el in midi.recurse().getElementsByClass(tempo.MetronomeMark):
            bpm = int(el.number)
            break

        # Compás
        ts_el = midi.recurse().getElementsByClass(meter.TimeSignature)
        ts = str(ts_el[0].ratioString) if ts_el else None

        # Tonalidad
        tonalidad = str(midi.analyze("key"))

        # Conteo de notas
        for n in midi.recurse().notes:
            if isinstance(n, (note.Note, chord.Chord)):
                total_notas += 1

        return jsonify({
            "bpm": bpm,
            "compas": ts,
            "tonalidad": tonalidad,
            "notas_totales": total_notas
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
