from flask import Blueprint, jsonify, request
from services.ec2_service import (
    get_instance_summary,
    get_instances,
    start_instance,
    stop_instance,
    reboot_instance,
    delete_instance,
    get_ec2_cpu_24h,
    get_ec2_cpu_7d,
    get_ec2_instance_cost,
    get_idle_ec2_instances,
    get_stopped_ec2_with_cost
)

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

@ec2_bp.route("/instances/<instance_id>", methods=["GET"])
def ec2_instance_detail(instance_id):
    try:
        instances = get_instances()
        instance = next((i for i in instances if i["InstanceId"] == instance_id), None)
        if not instance:
            return jsonify({"error": "Instance not found"}), 404
        return jsonify(instance)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ec2_bp.route("/instances/<instance_id>/start", methods=["POST"])
def ec2_start(instance_id):
    try:
        start_instance(instance_id)
        return jsonify({"message": "Instance starting", "instance_id": instance_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ec2_bp.route("/instances/<instance_id>/stop", methods=["POST"])
def ec2_stop(instance_id):
    try:
        stop_instance(instance_id)
        return jsonify({"message": "Instance stopping", "instance_id": instance_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ec2_bp.route("/instances/<instance_id>/reboot", methods=["POST"])
def ec2_reboot(instance_id):
    try:
        reboot_instance(instance_id)
        return jsonify({"message": "Instance rebooting", "instance_id": instance_id})
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

@ec2_bp.route("/instances/<instance_id>/cost", methods=["GET"])
def ec2_cost(instance_id):
    try:
        cost = get_ec2_instance_cost(instance_id)
        return jsonify(cost)
    except Exception as e:
        return jsonify({"error": str(e)}), 500