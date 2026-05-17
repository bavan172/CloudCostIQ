import boto3
from datetime import datetime, timedelta, UTC

rds = boto3.client("rds")
cloudwatch = boto3.client("cloudwatch")


# ─── CORE ───────────────────────────────────────────

def get_all_rds_instances():
    response = rds.describe_db_instances()
    instances = []

    for instance in response.get("DBInstances", []):
        try:
            # Get tags
            tags_response = rds.list_tags_for_resource(
                ResourceName=instance["DBInstanceArn"]
            )
            tags = tags_response.get("TagList", [])

            instances.append({
                "DBInstanceIdentifier": instance.get("DBInstanceIdentifier"),
                "DBInstanceClass": instance.get("DBInstanceClass"),
                "Engine": instance.get("Engine"),
                "EngineVersion": instance.get("EngineVersion"),
                "DBInstanceStatus": instance.get("DBInstanceStatus"),
                "MultiAZ": instance.get("MultiAZ"),
                "StorageType": instance.get("StorageType"),
                "AllocatedStorage": instance.get("AllocatedStorage"),
                "StorageEncrypted": instance.get("StorageEncrypted"),
                "AvailabilityZone": instance.get("AvailabilityZone"),
                "InstanceCreateTime": str(instance.get("InstanceCreateTime")),
                "Tags": tags
            })
        except Exception as e:
            print(f"Error processing RDS instance: {e}")
            continue

    return instances


def get_rds_summary():
    instances = get_all_rds_instances()
    total = len(instances)
    running = sum(1 for i in instances if i["DBInstanceStatus"] == "available")
    stopped = sum(1 for i in instances if i["DBInstanceStatus"] == "stopped")

    return {
        "total_instances": total,
        "running_instances": running,
        "stopped_instances": stopped
    }


# ─── CLOUDWATCH METRICS ──────────────────────────────

def get_rds_cpu_7d(db_instance_id):
    try:
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=7)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName="CPUUtilization",
            Dimensions=[
                {
                    "Name": "DBInstanceIdentifier",
                    "Value": db_instance_id
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=["Average"]
        )
        return response.get("Datapoints", [])
    except Exception as e:
        print(f"Error getting CPU for {db_instance_id}: {e}")
        return []


def get_rds_connections_7d(db_instance_id):
    try:
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=7)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName="DatabaseConnections",
            Dimensions=[
                {
                    "Name": "DBInstanceIdentifier",
                    "Value": db_instance_id
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=["Average"]
        )
        return response.get("Datapoints", [])
    except Exception as e:
        print(f"Error getting connections for {db_instance_id}: {e}")
        return []


# ─── WASTEFUL RESOURCE FUNCTIONS ─────────────────────

def get_idle_rds_instances():
    instances = get_all_rds_instances()
    idle = []

    for instance in instances:
        try:
            db_id = instance["DBInstanceIdentifier"]

            # Only check available instances
            if instance["DBInstanceStatus"] != "available":
                continue

            cpu_data = get_rds_cpu_7d(db_id)
            conn_data = get_rds_connections_7d(db_id)

            if not cpu_data or not conn_data:
                continue

            avg_cpu = sum(d["Average"] for d in cpu_data) / len(cpu_data)
            avg_connections = sum(d["Average"] for d in conn_data) / len(conn_data)

            if avg_cpu < 5 and avg_connections == 0:
                idle.append({
                    "DBInstanceIdentifier": db_id,
                    "DBInstanceClass": instance.get("DBInstanceClass"),
                    "Engine": instance.get("Engine"),
                    "AvailabilityZone": instance.get("AvailabilityZone"),
                    "AverageCPU": round(avg_cpu, 2),
                    "AverageConnections": round(avg_connections, 2),
                    "Reason": "CPU < 5% and zero connections for 7 days"
                })
        except Exception as e:
            print(f"Error checking idle for {instance.get('DBInstanceIdentifier')}: {e}")
            continue

    return idle


def get_stopped_rds_instances():
    instances = get_all_rds_instances()
    stopped = []

    for instance in instances:
        try:
            if instance["DBInstanceStatus"] == "stopped":
                stopped.append({
                    "DBInstanceIdentifier": instance.get("DBInstanceIdentifier"),
                    "DBInstanceClass": instance.get("DBInstanceClass"),
                    "Engine": instance.get("Engine"),
                    "AllocatedStorage": instance.get("AllocatedStorage"),
                    "AvailabilityZone": instance.get("AvailabilityZone"),
                    "Reason": "Instance is stopped — AWS will auto-start after 7 days and resume billing"
                })
        except Exception as e:
            print(f"Error checking stopped for {instance.get('DBInstanceIdentifier')}: {e}")
            continue

    return stopped


def get_unencrypted_rds_instances():
    instances = get_all_rds_instances()
    unencrypted = []

    for instance in instances:
        try:
            if not instance.get("StorageEncrypted", False):
                unencrypted.append({
                    "DBInstanceIdentifier": instance.get("DBInstanceIdentifier"),
                    "DBInstanceClass": instance.get("DBInstanceClass"),
                    "Engine": instance.get("Engine"),
                    "AvailabilityZone": instance.get("AvailabilityZone"),
                    "Reason": "Storage encryption is disabled — security risk"
                })
        except Exception as e:
            print(f"Error checking encryption for {instance.get('DBInstanceIdentifier')}: {e}")
            continue

    return unencrypted


def get_untagged_rds_instances():
    instances = get_all_rds_instances()
    untagged = []

    for instance in instances:
        try:
            tags = instance.get("Tags", [])

            if not tags:
                untagged.append({
                    "DBInstanceIdentifier": instance.get("DBInstanceIdentifier"),
                    "DBInstanceClass": instance.get("DBInstanceClass"),
                    "Engine": instance.get("Engine"),
                    "AvailabilityZone": instance.get("AvailabilityZone"),
                    "Reason": "No tags found — owner and purpose unknown"
                })
        except Exception as e:
            print(f"Error checking tags for {instance.get('DBInstanceIdentifier')}: {e}")
            continue

    return untagged


# ─── ACTIONS ─────────────────────────────────────────

def stop_rds_instance(db_instance_id):
    try:
        rds.stop_db_instance(DBInstanceIdentifier=db_instance_id)
        return {
            "success": True,
            "message": f"{db_instance_id} is stopping"
        }
    except Exception as e:
        return {"success": False, "message": str(e)}



