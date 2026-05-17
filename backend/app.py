from flask import Flask, jsonify
from routes.ec2_routes import ec2_bp
from routes.s3_routes import s3_bp
from routes.rds_routes import rds_bp
from routes.network_routes import network_bp
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

app.register_blueprint(ec2_bp, url_prefix = "/api/ec2")
app.register_blueprint(s3_bp, url_prefix = "/api/s3")
app.register_blueprint(rds_bp, url_prefix = "/api/rds")
app.register_blueprint(network_bp, url_prefix = "/api/network")

if __name__ == "__main__":
    app.run(debug=True)