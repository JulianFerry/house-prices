import os

from flask import Flask, request
from flask_restful import Api, Resource

import pandas as pd
from model import HousePrices
import joblib
import io

from google.cloud import storage
import google.cloud.logging
import logging

# Google Cloud -----

## Google cloud environment variables
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "credentials/house-prices-267107-005a58e1c145.json"
GCS_BUCKET = "house-prices-267107.appspot.com"
GCS_BLOB = "model.joblib"

## Set up logging
client = google.cloud.logging.Client()
client.setup_logging()


# Flask app -----

## Start RESTful app
app = Flask(__name__)
api = Api(app)

def load_model(id_bucket, id_blob):
    """
    """
    # Connect to GCP storage bucket
    client = storage.Client()
    bucket = client.bucket(id_bucket)
    #if not bucket.exists():
        # TODO: Throw error

    # Load model or initialise to None
    blob = bucket.blob(id_blob)
    if blob.exists():
        f = io.BytesIO()
        blob.download_to_file(f)
        app.model = joblib.load(f)
    else:
        app.model = None

def save_model(id_bucket, id_blob):
    """
    """
    # Connect to GCP storage bucket
    client = storage.Client()
    bucket = client.bucket(id_bucket)
    #if not bucket.exists():
        # TODO: Throw error

    # Dump model
    blob = bucket.blob(id_blob)
    with io.BytesIO() as f:
        joblib.dump(app.model, f)
        # io.BytesIO() stream cursor has to be at the beginning to use upload_from_file()
        f.seek(0)
        blob.upload_from_file(f)


class Fit(Resource):
    """
    """
    # curl -X GET http://127.0.0.1:8080/fit
    def get(self):
        logging.info('/fit received GET request. Training model...')

        # Train model
        app.model = HousePrices()
        app.model.fit()
        save_model(GCS_BUCKET, GCS_BLOB)

        # Respond with success
        message = "Model succesfully trained and dumped to gs://{}".format(
            os.path.join(GCS_BUCKET, GCS_BLOB)
        )
        logging.info(message)
        return {
                'status': 'success',
                'message': message
                }, 201


class Predict(Resource):
    """
    """
    # curl -X POST -F data=@data/raw/test.csv http://127.0.0.1:8080/predict
    def post(self):
        logging.info('/predict received POST request.')

        # Load model
        if not app.model:
            load_model(GCS_BUCKET, GCS_BLOB)
            if not app.model:
                message = 'Model not found at gs://{}'.format(
                    os.path.join(GCS_BUCKET, GCS_BLOB)
                )
                logging.error(message)
                return {
                    'status': 'error',
                    'message': message,
                    }, 503

        # Score data
        if request.files.get('data'):
            logging.info('File received. Scoring data...')
            f = request.files['data']
            data = pd.read_csv(f)
            y_pred = list(app.model.predict(data))
        elif request.json.get('data'):
            logging.info('JSON data received. Scoring data...')
            data = pd.DataFrame(request.json['data'])
            y_pred   = list(app.model.predict(data))
        else:
            return {
                    'status': 'error',
                    'message': 'Send data as file or json in a POST request'
                    }, 400

        # Respond with model predictions
        logging.info('Successfully scored data using model.')
        return {
                'status': 'success',
                'data': y_pred
                }, 200


## Try to load model on startup
load_model(GCS_BUCKET, GCS_BLOB)

## Add endpoints to RESTful api
api.add_resource(Fit, '/fit')
api.add_resource(Predict, '/predict')


# For debugging only
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
