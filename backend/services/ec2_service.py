import boto3
import json
from datetime import datetime, timedelta, UTC

ec2 = boto3.client("ec2")

        
def get_instance_summary():

    instances = get_instances()
    total = len(instances)
    running = 0
    stopped = 0

    for instance in instances:
        if instance["State"] == "running":
            running += 1
        elif instance["State"] == "stopped":
            stopped += 1

    return {
        "total_instances": total,
        "running_instances": running,
        "stopped_instances": stopped
    }         

def get_instances():

    response = ec2.describe_instances()
    instance_data = []
    
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            name = instance.get("InstanceId")
            for tag in instance.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]
            
            instance_info = {
                "Name": name,
                "InstanceId": instance.get("InstanceId"),
                "ImageId": instance.get("ImageId"),
                "InstanceType": instance.get("InstanceType"),
                "State": instance.get("State", {}).get("Name"),
                # JSON doesn't understand datetime objects, so we convert it to string
                "LaunchTime": str(instance.get("LaunchTime")),
                "PublicIpAddress": instance.get("PublicIpAddress"),
                "PrivateIpAddress": instance.get("PrivateIpAddress"),
                "AvailabilityZone": instance.get("Placement", {}).get("AvailabilityZone"),
                "SSHOpenToPublic": is_ssh_open(instance),
                "MonitoringState": instance.get("Monitoring", {}).get("State"),
            }
            instance_data.append(instance_info)

    return instance_data


def is_ssh_open(instance):
    security_groups = instance.get("SecurityGroups", [])
    
    for sg in security_groups:
        sg_id = sg["GroupId"]
        response = ec2.describe_security_groups(
            GroupIds=[sg_id]
        )
        
        for sg in response["SecurityGroups"]:
            for permission in sg.get("IpPermissions", []):
                if permission.get("FromPort") == 22 and permission.get("ToPort") == 22:
                    for ip_range in permission.get("IpRanges", []):
                        if ip_range.get("CidrIp") == "0.0.0.0/0":
                            return True
    return False


def stop_instance(instance_id):
    try:
        response = ec2.stop_instances(InstanceIds=[instance_id])
        return response
    except Exception as e:
        print(f"Error stopping instance {instance_id}: {e}")
        return None

def delete_instance(instance_id):
    try:
        response = ec2.terminate_instances(InstanceIds=[instance_id])
        return response
    except Exception as e:
        print(f"Error terminating instance {instance_id}: {e}")
        return None

from datetime import datetime, timedelta, UTC

# Get EC2 CPU utilization for last 24 hours
def get_ec2_cpu_24h(instance_id):
    cloudwatch = boto3.client("cloudwatch")
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=24)

    response = cloudwatch.get_metric_statistics(

        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id
            }
        ],

        StartTime=start_time,
        EndTime=end_time,
        Period=3600,

        Statistics=["Average"]
    )

    return response["Datapoints"]

# Get EC2 CPU utilization for last 7 days
def get_ec2_cpu_7d(instance_id):
    cloudwatch = boto3.client("cloudwatch")
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=7)

    response = cloudwatch.get_metric_statistics(

        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id
            }
        ],

        StartTime=start_time,
        EndTime=end_time,
        Period=86400,
        Statistics=["Average"]
    )

    return response["Datapoints"]


# Get idle EC2 instances
def get_idle_ec2_instances():

    instances = get_instances()
    idle_instances = []

    for instance in instances:
        instance_id = instance["InstanceId"]
        cpu_data = get_ec2_cpu_7d(instance_id)
        if not cpu_data:
            continue

        total_cpu = 0

        for datapoint in cpu_data:
            total_cpu += datapoint.get("Average", 0)
        avg_cpu = total_cpu / len(cpu_data)

        if avg_cpu < 5:
            idle_instances.append({
                "InstanceId": instance_id,
                "Name": instance["Name"],
                "AverageCPU": round(avg_cpu, 2)
            })

    return idle_instances


# Get stopped EC2 instances that still have attached EBS volumes

def get_stopped_ec2_with_cost():

    instances = get_instances()
    stopped_instances = []

    for instance in instances:
        if instance["State"] == "stopped":
            instance_id = instance["InstanceId"]

            # Get attached EBS volumes for this instance
            volumes_response = ec2.describe_volumes(
                Filters=[
                    {
                        "Name": "attachment.instance-id",
                        "Values": [instance_id]
                    }
                ]
            )

            total_size_gb = 0
            volumes = []

            for volume in volumes_response["Volumes"]:
                size = volume["Size"]  # in GB
                vol_type = volume["VolumeType"]  # gp2, gp3, io1 etc
                total_size_gb += size
                volumes.append({
                    "VolumeId": volume["VolumeId"],
                    "SizeGB": size,
                    "VolumeType": vol_type
                })

            # Estimate monthly EBS cost
            # gp2/gp3 = $0.10/GB/month (approximate)
            estimated_monthly_cost = round(total_size_gb * 0.10, 2)

            stopped_instances.append({
                "InstanceId": instance_id,
                "Name": instance["Name"],
                "State": instance["State"],
                "Volumes": volumes,
                "TotalEBSSizeGB": total_size_gb,
                "EstimatedMonthlyCost": f"${estimated_monthly_cost}"
            })

    return stopped_instances


# Get EC2 uptime in days
def get_ec2_uptime(launch_time):
    
    current_time = datetime.now(UTC)
    uptime = current_time - launch_time
    return uptime.days

def get_untagged_ec2_instances():
    instances = get_instances()
    untagged = []

    for instance in instances:
        try:
            # get_instances() already parses tags
            # if Name == InstanceId it means no Name tag was found
            # but we want to check ALL tags not just Name
            response = ec2.describe_instances(
                InstanceIds=[instance["InstanceId"]]
            )
            raw_tags = response["Reservations"][0]["Instances"][0].get("Tags", [])

            if not raw_tags:
                untagged.append({
                    "InstanceId": instance["InstanceId"],
                    "InstanceType": instance.get("InstanceType"),
                    "State": instance.get("State"),
                    "AvailabilityZone": instance.get("AvailabilityZone"),
                    "Reason": "No tags found, please tag this resource to improve organization and management",
                })
        except Exception as e:
            print(f"Error checking tags for {instance.get('InstanceId')}: {e}")
            continue

    return untagged


# Get unattached EBS volumes
def get_unattached_ebs_volumes():
    response = ec2.describe_volumes(
        Filters=[
            {
                "Name": "status",
                "Values": ["available"]  # available = not attached to any instance
            }
        ]
    )

    volumes = []
    for volume in response["Volumes"]:
        
        name = volume.get("VolumeId")
        for tag in volume.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]

        estimated_cost = round(volume.get("Size") * 0.10, 2)

        volumes.append({
            "VolumeId": volume.get("VolumeId"),
            "Name": name,
            "SizeGB": volume.get("Size"),
            "VolumeType": volume.get("VolumeType"),
            "AvailabilityZone": volume.get("AvailabilityZone"),
            "CreateTime": str(volume.get("CreateTime")),
            "Encrypted": volume.get("Encrypted"),
            "EstimatedMonthlyCost": f"${estimated_cost}"
        })

    return volumes


def get_unused_elastic_ips():
    response = ec2.describe_addresses()
    
    unused = []
    for address in response["Addresses"]:

        # If no InstanceId and no NetworkInterfaceId it's unused
        is_associated = (
            address.get("InstanceId") or 
            address.get("NetworkInterfaceId")
        )
        
        if not is_associated:
            unused.append({
                "AllocationId": address.get("AllocationId"),
                "PublicIp": address.get("PublicIp"),
                "Domain": address.get("Domain"),  # vpc or standard
                "CreateTime": str(address.get("CreateTime"))
            })
    
    return unused


#----Snapshots

import boto3
from datetime import datetime, timedelta, UTC

ec2 = boto3.client("ec2")


def get_all_snapshots():
    response = ec2.describe_snapshots(OwnerIds=["self"])
    snapshots = []

    for snapshot in response.get("Snapshots", []):
        try:
            name = snapshot.get("SnapshotId")
            for tag in snapshot.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]

            start_time = snapshot.get("StartTime")
            age_days = (datetime.now(UTC) - start_time).days if start_time else 0

            snapshots.append({
                "SnapshotId": snapshot.get("SnapshotId"),
                "Name": name,
                "VolumeId": snapshot.get("VolumeId"),
                "VolumeSize": snapshot.get("VolumeSize"),
                "State": snapshot.get("State"),
                "Encrypted": snapshot.get("Encrypted"),
                "StartTime": str(start_time),
                "AgeDays": age_days,
                "Tags": snapshot.get("Tags", [])
            })
        except Exception as e:
            print(f"Error processing snapshot {snapshot.get('SnapshotId')}: {e}")
            continue

    return snapshots


def get_old_snapshots():
    snapshots = get_all_snapshots()
    old = []

    # Get all existing volume IDs for comparison
    volumes_response = ec2.describe_volumes()
    existing_volume_ids = {
        v["VolumeId"] for v in volumes_response.get("Volumes", [])
    }

    for snapshot in snapshots:
        try:
            age_days = snapshot.get("AgeDays", 0)
            volume_id = snapshot.get("VolumeId")

            if age_days < 90:
                continue

            # Check if source volume still exists
            source_volume_deleted = volume_id not in existing_volume_ids


            old.append({
                "SnapshotId": snapshot.get("SnapshotId"),
                "Name": snapshot.get("Name"),
                "VolumeId": volume_id,
                "VolumeSize": snapshot.get("VolumeSize"),
                "AgeDays": age_days,
                "StartTime": snapshot.get("StartTime"),
                "SourceVolumeDeleted": source_volume_deleted,
                "Reason": f"Snapshot is {age_days} days old" + 
                          (" and source volume no longer exists" if source_volume_deleted else "")
            })
        except Exception as e:
            print(f"Error checking old snapshot {snapshot.get('SnapshotId')}: {e}")
            continue

    return old


def get_unencrypted_snapshots():
    snapshots = get_all_snapshots()
    unencrypted = []

    for snapshot in snapshots:
        try:
            if not snapshot.get("Encrypted", False):
                unencrypted.append({
                    "SnapshotId": snapshot.get("SnapshotId"),
                    "Name": snapshot.get("Name"),
                    "VolumeId": snapshot.get("VolumeId"),
                    "VolumeSize": snapshot.get("VolumeSize"),
                    "AgeDays": snapshot.get("AgeDays", 0),
                    "Reason": "Snapshot is not encrypted, which can be a security risk if it contains sensitive data. Consider encrypting this snapshot or deleting it if it's no longer needed."
                })
        except Exception as e:
            print(f"Error checking encryption for {snapshot.get('SnapshotId')}: {e}")
            continue

    return unencrypted


def get_untagged_snapshots():
    snapshots = get_all_snapshots()
    untagged = []

    for snapshot in snapshots:
        try:
            if not snapshot.get("Tags"):
                untagged.append({
                    "SnapshotId": snapshot.get("SnapshotId"),
                    "Name": snapshot.get("Name"),
                    "VolumeId": snapshot.get("VolumeId"),
                    "VolumeSize": snapshot.get("VolumeSize"),
                    "AgeDays": snapshot.get("AgeDays", 0),
                    "Reason": "No tags found, please tag this resource to improve organization and management. Untagged resources can lead to confusion and difficulty in tracking costs."
                })
        except Exception as e:
            print(f"Error checking tags for {snapshot.get('SnapshotId')}: {e}")
            continue

    return untagged


def get_wasteful_snapshots():
    return {
        "old_snapshots": len(get_old_snapshots()),
        "unencrypted_snapshots": len(get_unencrypted_snapshots()),
        "untagged_snapshots": len(get_untagged_snapshots())
    }