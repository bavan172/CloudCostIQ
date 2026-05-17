from flask import Blueprint, jsonify, request
from services.ec2_service import *

ec2_bp = Blueprint("ec2", __name__)

@ec2_bp.route("/summary", methods=["GET"])
def ec2_summary():
    try:
        summary = get_instance_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ec2_bp.route("/instances", methods=["GET"])
def ec2_instances():
    try:
        instances = get_instances()
        return jsonify(instances)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ec2_bp.route("/instances/idle", methods=["GET"])
def ec2_idle():
    try:
        idle = get_idle_ec2_instances()
        return jsonify(idle)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ec2_bp.route("/instances/stopped-with-cost", methods=["GET"])
def ec2_stopped_with_cost():
    try:
        stopped = get_stopped_ec2_with_cost()
        return jsonify(stopped)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ec2_bp.route("/instances/<instance_id>/stop", methods=["POST"])
def ec2_stop(instance_id):
    try:
        stop_instance(instance_id)
        return jsonify({"message": "Instance stopping", "instance_id": instance_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ec2_bp.route("/instances/<instance_id>", methods=["DELETE"])
def ec2_delete(instance_id):
    try:
        delete_instance(instance_id)
        return jsonify({"message": "Instance terminated", "instance_id": instance_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ec2_bp.route("/instances/<instance_id>/cpu", methods=["GET"])
def ec2_cpu_24h(instance_id):
    try:
        cpu = get_ec2_cpu_24h(instance_id)
        return jsonify(cpu)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ec2_bp.route("/instances/<instance_id>/cpu/7d", methods=["GET"])
def ec2_cpu_7d(instance_id):
    try:
        cpu = get_ec2_cpu_7d(instance_id)
        return jsonify(cpu)
    except Exception as e:
        return jsonify({"error": str(e)}), 500 
    
@ec2_bp.route("/instances/idle-volumes", methods=["GET"])
def ec2_unattached_volumes():
    try:
        volumes = get_unattached_ebs_volumes()
        return jsonify(volumes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@ec2_bp.route("/instances/idle-eips", methods=["GET"])
def ec2_unused_eips():
    try:
        eips = get_unused_elastic_ips()
        return jsonify(eips)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# ─── UNTAGGED EC2 --------------------------------------

@ec2_bp.route("/instances/untagged", methods=["GET"])
def ec2_untagged():
    try:
        return jsonify(get_untagged_ec2_instances())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── SNAPSHOTS ───────────────────────────────────────

@ec2_bp.route("/snapshots/summary", methods=["GET"])
def ec2_snapshots_wasteful_all():
    try:
        return jsonify(get_wasteful_snapshots())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ec2_bp.route("/snapshots/old", methods=["GET"])
def ec2_snapshots_old():
    try:
        return jsonify(get_old_snapshots())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ec2_bp.route("/snapshots/unencrypted", methods=["GET"])
def ec2_snapshots_unencrypted():
    try:
        return jsonify(get_unencrypted_snapshots())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ec2_bp.route("/snapshots/untagged", methods=["GET"])
def ec2_snapshots_untagged():
    try:
        return jsonify(get_untagged_snapshots())
    except Exception as e:
        return jsonify({"error": str(e)}), 500