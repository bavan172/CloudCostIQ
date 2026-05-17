from flask import Blueprint, jsonify
from services.rds_service import (
    get_all_rds_instances,
    get_rds_summary,
    get_idle_rds_instances,
    get_stopped_rds_instances,
    get_unencrypted_rds_instances,
    get_untagged_rds_instances,
    stop_rds_instance,
)

rds_bp = Blueprint("rds", __name__)


@rds_bp.route("/instances", methods=["GET"])
def rds_instances():
    try:
        return jsonify(get_all_rds_instances())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rds_bp.route("/summary", methods=["GET"])
def rds_summary():
    try:
        return jsonify(get_rds_summary())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rds_bp.route("/idle", methods=["GET"])
def rds_idle():
    try:
        return jsonify(get_idle_rds_instances())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rds_bp.route("/stopped", methods=["GET"])
def rds_stopped():
    try:
        return jsonify(get_stopped_rds_instances())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rds_bp.route("/unencrypted", methods=["GET"])
def rds_unencrypted():
    try:
        return jsonify(get_unencrypted_rds_instances())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rds_bp.route("/untagged", methods=["GET"])
def rds_untagged():
    try:
        return jsonify(get_untagged_rds_instances())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rds_bp.route("/instances/<db_instance_id>/stop", methods=["POST"])
def rds_stop(db_instance_id):
    try:
        result = stop_rds_instance(db_instance_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
