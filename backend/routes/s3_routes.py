from flask import Blueprint, jsonify
from services.s3_service import get_all_s3_buckets, get_empty_s3_buckets, get_s3_buckets_not_accessed, delete_s3_bucket, get_s3_bucket_summary, get_s3_buckets_without_tags

s3_bp = Blueprint("s3", __name__)

@s3_bp.route("/buckets", methods=["GET"])
def s3_buckets():
    try:
        buckets = get_all_s3_buckets()
        return jsonify(buckets)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@s3_bp.route("/summary", methods=["GET"])
def s3_summary():
    try:
        return jsonify(get_s3_bucket_summary())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@s3_bp.route("/empty", methods=["GET"])
def s3_empty_buckets():
    try:
        return jsonify(get_empty_s3_buckets())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@s3_bp.route("/not-accessed", methods=["GET"])
def s3_not_accessed_buckets():
    try:
        return jsonify(get_s3_buckets_not_accessed())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@s3_bp.route("/bucket/<bucket_name>", methods=["DELETE"])
def s3_delete_bucket(bucket_name):
    try:
        result = delete_s3_bucket(bucket_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@s3_bp.route("/untagged", methods=["GET"])
def s3_untagged_buckets():
    try:
        return jsonify(get_s3_buckets_without_tags())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
