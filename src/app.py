# Import libraries

from flask import Flask

from flask import (request, jsonify,
    Flask,render_template,

)
import pandas as pd
import json
import requests
# from get_viz_data import get_deciphering_rna_splicing_data
from src.clip_exon import clip_exon 
# Declare application
app = Flask(__name__)

default_options = {
    'teaser':"GCGGCACCUACUACAAUGUCCCCCGCUGCAUACACUCGGAGCCAAUAGGGCGCCUAUAGAGUGUAGUCCU",
    'exon_s1':"GAGUCCCGCUUACCAUUGCAUUUAAGAAAGCGGCCAUACGCCGCUAAGACCCUACUCUUCAGAAUACCAG",
    'exon_s1_comp1':"CCUUCCACGCCUCUCCCACUCGUUACACUCAGUUGCAGUAUGGUUAACACUCCACUAGGCCCCAGGAAUC",
    'exon_s1_comp2':"GUCUGACAGUACUACGCUAAUACUACGUAAACCAAAGCCAUAAUCCAAUUGACCUCCUUUUCAGGAAUUC",
    'exon_s1_34c>a':"GAGUCCCGCUUACCAUUGCAUUUAAGAAAGAGGCCAUACGCCGCUAAGACCCUACUCUUCAGAAUACCAG",
    'exon_s1_34c>a_46g>u':"GAGUCCCGCUUACCAUUGCAUUUAAGAAAGAGGCCAUACGCCUCUAAGACCCUACUCUUCAGAAUACCAG",
    'exon_d1':"GACUAUGAGCCCCAACGAACAAGCUCCUAUCUGGGAACUCUUUUCUGCAGACUUUAACCCUACCCCCAGA"
}

def get_default_exon(option):
    """Get the default exon based on the option, converting 'T' to 'U'."""
    if option in default_options:
        return default_options[option].upper().replace("T", "U")
    return option

def fetch_prediction_from_server(exon):
    """Attempt to fetch the prediction from the server, handle errors gracefully."""
    try:
        # change the http address once the ec2 server is up. 
        response = requests.post('http://18.222.129.149:5000/prediction', data={'exon': exon}, timeout=10)
        response.raise_for_status()  # This will raise an HTTPError for bad responses (4XX, 5XX)
        return response.json()
    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, and bad responses
        print(f"Error contacting server: {e}")
        return None

def read_local_data(option):
    """Read local data file as a fallback."""
    try:
        with open(f'src/data/{option}.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"error": "Data file not found"}
    except json.JSONDecodeError:
        return {"error": "Error decoding JSON data"}


# renders the main page
@app.route("/", methods=["GET", "POST"])
def homepage():

    return render_template("./index.html")

# communicates with the api for the model in the backend and get a prediction. 
# if prediction is not available. it will fetch data from local files. 
@app.route("/get-data", methods=["GET"])
def get_data():
    option = request.args.get('option', 'exon_s1')
    # dataset = request.args.get('dataset', 'ES7')
    print(option)
    # Main logic to decide whether to use server or local file
    if option in default_options: 
        json_response = read_local_data(option)
        clip_exon(json_response)

        return json_response
    exon = get_default_exon(option)
    json_response = fetch_prediction_from_server(exon)
    if json_response is None:  # Server request failed
        json_response = read_local_data(option)
    clip_exon(json_response)
    return jsonify(json_response)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port = 5051, debug=True)