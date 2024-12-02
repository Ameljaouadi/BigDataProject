from flask import Flask, render_template, request, redirect, url_for
import os
import json
import csv

app = Flask(__name__)

LOGS_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'logstash', 'logs')

# Vérifier que le dossier 'logs' existe
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)


@app.route('/')
def index():
    error_message = request.args.get('error_message')
    return render_template('index.html', error_message=error_message)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index', error_message="Aucun fichier sélectionné"))

    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('index', error_message="Aucun fichier sélectionné"))

    if file and allowed_file(file.filename):
        filename = os.path.join(LOGS_DIR, file.filename)
        file.save(filename)

        # Vérifier Si le fichier est un JSON ou CSV
        try:
            if filename.endswith('.json'):
                process_json(filename)
            elif filename.endswith('.csv'):
                process_csv(filename)
        except Exception as e:
            return redirect(url_for('index', error_message=f"Erreur lors du traitement du fichier: {str(e)}"))

        return redirect(url_for('index'))

    return redirect(url_for('index', error_message="Fichier non autorisé, uniquement JSON ou CSV."))

# Vérifier si le fichier est un JSON ou un CSV


def allowed_file(filename):
    return filename.endswith('.json') or filename.endswith('.csv')

# Traiter le fichier JSON


def process_json(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
        print(f"Fichier JSON traité: {filename}")

# Traiter le fichier CSV


def process_csv(filename):
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            print(f"Ligne CSV: {row}")


if __name__ == '__main__':
    app.run(debug=True)