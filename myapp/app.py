from flask import Flask, render_template, request, redirect, url_for
import os
import json
import csv
import requests
from elasticsearch import Elasticsearch
app = Flask(__name__)

es = Elasticsearch(["http://localhost:9200"])
LOGS_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'logstash', 'logs')

# Vérifier que le dossier 'logs' existe
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# define kibana url and visualisation Id
KIBANA_URL = "https://symmetrical-meme-gw996g9jwvx3vpr4-5601.app.github.dev"
# /  # URL complète de votre instance Kibana
VISUALISATION_ID = ""
ALLOWED_EXTENSIONS = {'json', 'csv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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


# def process_csv(filename):
#     with open(filename, 'r') as file:
#         reader = csv.reader(file)
#         for row in reader:
#             print(f"Ligne CSV: {row}")

def process_csv(filename):
    with open(filename, 'r') as file:
        # Utilisation de DictReader pour lire le CSV en tant que dictionnaire
        reader = csv.DictReader(file)
        for row in reader:
            try:
                # Indexer chaque ligne dans Elasticsearch
                es.index(index="logs-index", body=row)
            except Exception as e:
                print(f"Erreur lors de l'indexation dans Elasticsearch : {e}")
        print(f"Fichier CSV importé dans Elasticsearch : {filename}")

    # Rafraîchir l'index pour que les données soient immédiatement disponibles
    es.indices.refresh(index="logs-index")


@app.route('/search', methods=['GET', 'POST'])
def search_logs():
    results = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            # elasticsearc search query
            es_query = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["LogLevel", "Message", "ClientIP", "Service", "TimeTaken", "User",
                                   "WARNING", "RequestID", "Timestamp"]
                    }
                }


            }
            response = es.search(index="csv3-2024.12.08", body=es_query)
            results = response.get('hits', {}).get('hits', [])
            # Remove duplicates based on 'LineId'
            results = {result['_source']['LineId']
                : result for result in results}.values()
            return render_template('search.html', results=results, query=query)


@app.route('/dashbord')
def dashboard():
    return render_template('dashbord.html')


if __name__ == '__main__':
    app.run(debug=True)
