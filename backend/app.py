from flask import Flask, jsonify
from routes.ec2_routes import ec2_bp
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.register_blueprint(ec2_bp, url_prefix="/api/ec2")

if __name__ == "__main__":
    app.run(debug=True)