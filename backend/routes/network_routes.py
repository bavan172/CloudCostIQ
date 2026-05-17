from flask import Blueprint, jsonify
from services.network_service import (
    get_idle_nat_gateways,
    get_empty_vpcs,
    get_wasteful_network_resources
)

network_bp = Blueprint("network", __name__)


@network_bp.route("/summary", methods=["GET"])
def network_wasteful_all():
    try:
        return jsonify(get_wasteful_network_resources())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@network_bp.route("/nat/idle", methods=["GET"])
def network_nat_idle():
    try:
        return jsonify(get_idle_nat_gateways())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@network_bp.route("/vpc/empty", methods=["GET"])
def network_vpc_empty():
    try:
        return jsonify(get_empty_vpcs())
    except Exception as e:
        return jsonify({"error": str(e)}), 500