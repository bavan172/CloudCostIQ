from flask import Flask, jsonify
from flask_cors import CORS
from services.ec2_service import get_instances

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route("/")
def home():
    instances = get_instances()
    return jsonify(instances)
    
if __name__ == "__main__":
    app.run(debug=True)