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

# Google cloud environment variables
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "credentials/house-prices-267107-005a58e1c145.json"
os.environ['GCS_BUCKET'] = "house-prices-267107"
os.environ['GCS_BLOB'] = "model.joblib"

# Set up logging
client = google.cloud.logging.Client()
client.setup_logging()


# Flask app
app = Flask(__name__)
api = Api(app)

@app.before_first_request
def _load_model():
    """
    """
    # Model is a global variable - exists during the lifetime of the server
    global model

    # Connect to GCP storage bucket
    client = storage.Client()
    bucket = client.bucket(os.environ['GCS_BUCKET'])
    blob = bucket.blob(os.environ['GCS_BLOB'])

    # Load model or initialise to None
    if blob.exists():
        f = io.BytesIO()
        blob.download_to_file(f)
        model = joblib.load(f)
    else:
        model = None

def save_model():
    """
    """
    # Connect to GCP storage bucket
    client = storage.Client()
    bucket = client.bucket(os.environ['GCS_BUCKET'])
    if not bucket.exists():
        bucket = client.create_bucket(os.environ['GCS_BUCKET'])
    blob = bucket.blob(os.environ['GCS_BLOB'])

    # Dump model
    with io.BytesIO() as f:
        joblib.dump(model, f)
        # io.BytesIO() stream cursor has to be at the beginning to use upload_from_file()
        f.seek(0)
        blob.upload_from_file(f)


# curl -X GET http://127.0.0.1:8080/fit
class Fit(Resource):
    """
    """
    def get(self):
        logging.info('/fit received GET request. Training model...')

        # Train model
        model = HousePrices()
        model.fit()
        save_model()

        # Respond with success
        message = "Model succesfully trained and dumped to gs://{}".format(
            os.path.join(os.environ['GCS_BUCKET'], os.environ['GCS_BLOB'])
        )
        logging.info(message)
        return {
                'status': 'success',
                'message': message
                }, 201


# curl -X POST -F file=@data/raw/test.csv http://127.0.0.1:8080/predict
class Predict(Resource):
    """
    """
    def post(self):
        logging.info('/predict received POST request.')

        # Load model
        if not model:
            _load_model()
            if not model:
                message = 'Model not found at gs://{}'.format(
                    os.path.join(os.environ['GCS_BUCKET'], os.environ['GCS_BLOB'])
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
            y_pred = list(model.predict(data))
        elif request.json.get('data'):
            logging.info('JSON data received. Scoring data...')
            data = pd.DataFrame(request.json['data'])
            y_pred = list(model.predict(data))
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

# Add endpoints to RESTful api
api.add_resource(Fit, '/fit')
api.add_resource(Predict, '/predict')


# For debugging only
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
