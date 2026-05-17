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


# print(json.dumps(get_instances(), indent=4, default=str))

def start_instance(instance_id):
    try:
        response = ec2.start_instances(InstanceIds=[instance_id])
        return response
    except Exception as e:
        print(f"Error starting instance {instance_id}: {e}")
        return None

def stop_instance(instance_id):
    try:
        response = ec2.stop_instances(InstanceIds=[instance_id])
        return response
    except Exception as e:
        print(f"Error stopping instance {instance_id}: {e}")
        return None

def reboot_instance(instance_id):
    try:
        response = ec2.reboot_instances(InstanceIds=[instance_id])
        return response
    except Exception as e:
        print(f"Error rebooting instance {instance_id}: {e}")
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


# Get monthly EC2 cost for one instance
def get_ec2_instance_cost(instance_id):
    cost_explorer = boto3.client("ce")

    end_date = datetime.today().date()
    start_date = end_date.replace(day=1)  # Start of current month, not just 30 days

    response = cost_explorer.get_cost_and_usage(
        TimePeriod={
            "Start": str(start_date),
            "End": str(end_date)
        },
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        Filter={
            "And": [
                {
                    "Dimensions": {
                        "Key": "SERVICE",
                        "Values": ["Amazon Elastic Compute Cloud - Compute"]
                    }
                },
                {
                    "Tags": {
                        "Key": "aws:ec2:instance-id",  
                        "Values": [instance_id]
                    }
                }
            ]
        }
    )
    return response


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