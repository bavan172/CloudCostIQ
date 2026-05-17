import boto3
from datetime import datetime, timedelta, UTC

s3 = boto3.client("s3")

def get_all_s3_buckets():
    response = s3.list_buckets()
    buckets = []

    for bucket in response.get("Buckets", []):
        try:
            bucket_name = bucket["Name"]
            creation_date = bucket["CreationDate"]

            location = s3.get_bucket_location(Bucket=bucket_name)
            region = location.get("LocationConstraint") or "us-east-1"

            buckets.append({
                "BucketName": bucket_name,
                "CreationDate": str(creation_date),
                "BucketAgeDays": (datetime.now(UTC) - creation_date).days,
                "Region": region
            })
        except Exception as e:
            print(f"Error processing bucket {bucket.get('Name')}: {e}")
            continue

    return buckets

def get_empty_s3_buckets():
    buckets = get_all_s3_buckets()
    empty = []

    for bucket in buckets:
        try:
            bucket_name = bucket["BucketName"]
            response = s3.list_objects_v2(Bucket=bucket_name)

            if response.get("KeyCount", 0) == 0:
                empty.append({
                    "BucketName": bucket_name,
                    "CreationDate": bucket.get("CreationDate", "Unknown"),
                    "BucketAgeDays": bucket.get("BucketAgeDays", 0),
                    "Region": bucket.get("Region", "Unknown"),
                    "Reason": "Empty bucket with no objects, consider reviewing if this bucket is needed or can be deleted",
                })
        except Exception as e:
            print(f"Error checking {bucket.get('BucketName')}: {e}")
            continue

    return empty


def get_s3_buckets_not_accessed():
    cloudwatch = boto3.client("cloudwatch")
    buckets = get_all_s3_buckets()
    not_accessed = []

    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=30)

    for bucket in buckets:
        try:
            bucket_name = bucket["BucketName"]
            bucket_age = bucket.get("BucketAgeDays", 0)

            if bucket_age < 30:
                continue

            # List ALL metrics configurations — don't assume the name
            try:
                configs = s3.list_bucket_metrics_configurations(Bucket=bucket_name)
                metrics_list = configs.get("MetricsConfigurationList", [])
                metrics_enabled = len(metrics_list) > 0
                # Use whatever filter ID the user created
                filter_id = metrics_list[0]["Id"] if metrics_list else None
            except Exception:
                metrics_enabled = False
                filter_id = None

            if not metrics_enabled or not filter_id:
                not_accessed.append({
                    "BucketName": bucket_name,
                    "CreationDate": bucket.get("CreationDate", "Unknown"),
                    "BucketAgeDays": bucket_age,
                    "Region": bucket.get("Region", "Unknown"),
                    "MetricsEnabled": False,
                    "Note": "S3 request metrics not enabled, enable in S3 console for accurate access tracking"
                })
                continue

            # Use the actual filter ID from the bucket config
            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="NumberOfRequests",
                Dimensions=[
                    {"Name": "BucketName", "Value": bucket_name},
                    {"Name": "FilterId", "Value": filter_id}  # ← dynamic now
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=2592000,
                Statistics=["Sum"]
            )

            if not response.get("Datapoints"):
                objects_response = s3.list_objects_v2(Bucket=bucket_name)
                object_count = objects_response.get("KeyCount", 0)
                total_size_bytes = sum(
                    obj["Size"] for obj in objects_response.get("Contents", [])
                )
                total_size_gb = round(total_size_bytes / (1024**3), 4)
                estimated_cost = round(total_size_gb * 0.023, 4)

                not_accessed.append({
                    "BucketName": bucket_name,
                    "CreationDate": bucket.get("CreationDate", "Unknown"),
                    "BucketAgeDays": bucket_age,
                    "Region": bucket.get("Region", "Unknown"),
                    "HasObjects": object_count > 0,
                    "ObjectCount": object_count,
                    "TotalSizeGB": total_size_gb,
                    "EstimatedMonthlyCost": f"${estimated_cost}",
                    "Reason": f"No requests in last 30 days, the bucket is {bucket_age} days old",
                    "MetricsEnabled": True,
                    "FilterId": filter_id,
                    "Note": None
                })

        except Exception as e:
            print(f"Error checking {bucket.get('BucketName')}: {e}")
            continue

    return not_accessed


def delete_s3_bucket(bucket_name):
    try:
        objects = s3.list_objects_v2(Bucket=bucket_name)

        if objects.get("KeyCount", 0) > 0:
            return {
                "success": False,
                "message": "Bucket is not empty — delete objects first"
            }

        s3.delete_bucket(Bucket=bucket_name)
        return {
            "success": True,
            "message": f"Bucket {bucket_name} deleted successfully"
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    
    

def get_s3_bucket_summary():
    buckets = get_all_s3_buckets()
    empty = get_empty_s3_buckets()
    not_accessed = get_s3_buckets_not_accessed()

    return {
        "total_buckets": len(buckets),
        "empty_buckets": len(empty),
        "not_accessed_buckets": len(not_accessed),
        "total_zombie_buckets": len(empty) + len(not_accessed)
    }
    
    
def get_s3_buckets_without_tags():
    buckets = get_all_s3_buckets()
    untagged = []

    for bucket in buckets:
        try:
            bucket_name = bucket["BucketName"]

            try:
                response = s3.get_bucket_tagging(Bucket=bucket_name)
                tags = response.get("TagSet", [])
            except s3.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchTagSet":
                    tags = []  # no tags at all
                else:
                    raise

            if not tags:
                untagged.append({
                    "BucketName": bucket_name,
                    "CreationDate": bucket.get("CreationDate", "Unknown"),
                    "BucketAgeDays": bucket.get("BucketAgeDays", 0),
                    "Region": bucket.get("Region", "Unknown"),
                    "Reason": "Bucket has no tags, consider adding tags for better organization and cost allocation",
                })

        except Exception as e:
            print(f"Error checking tags for {bucket.get('BucketName')}: {e}")
            continue

    return untagged