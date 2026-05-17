import boto3
from datetime import datetime, timedelta, UTC

ec2 = boto3.client("ec2")
cloudwatch = boto3.client("cloudwatch")


# ----NAT GATEWAY------------------------------------------

def get_all_nat_gateways():
    response = ec2.describe_nat_gateways()
    gateways = []

    for nat in response.get("NatGateways", []):
        try:
            name = nat.get("NatGatewayId")
            for tag in nat.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]

            gateways.append({
                "NatGatewayId": nat.get("NatGatewayId"),
                "Name": name,
                "State": nat.get("State"),
                "VpcId": nat.get("VpcId"),
                "SubnetId": nat.get("SubnetId"),
                "CreateTime": str(nat.get("CreateTime")),
                "Tags": nat.get("Tags", [])
            })
        except Exception as e:
            print(f"Error processing NAT gateway {nat.get('NatGatewayId')}: {e}")
            continue

    return gateways


def get_idle_nat_gateways():
    gateways = get_all_nat_gateways()
    idle = []

    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=7)

    for nat in gateways:
        try:
            nat_id = nat["NatGatewayId"]

            if nat["State"] != "available":
                continue

            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/NATGateway",
                MetricName="BytesOutToDestination",
                Dimensions=[
                    {
                        "Name": "NatGatewayId",
                        "Value": nat_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=["Sum"]
            )

            total_bytes = sum(
                d.get("Sum", 0) for d in response.get("Datapoints", [])
            )

            if total_bytes == 0:
                idle.append({
                    "NatGatewayId": nat_id,
                    "Name": nat.get("Name"),
                    "VpcId": nat.get("VpcId"),
                    "SubnetId": nat.get("SubnetId"),
                    "TotalBytesProcessed": total_bytes,
                    "Reason": "Zero bytes processed in last 7 days"
                })
        except Exception as e:
            print(f"Error checking NAT {nat.get('NatGatewayId')}: {e}")
            continue

    return idle


# --- VPC ----------------------------------

def get_all_vpcs():
    response = ec2.describe_vpcs()
    vpcs = []

    for vpc in response.get("Vpcs", []):
        try:
            name = vpc.get("VpcId")
            for tag in vpc.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]

            vpcs.append({
                "VpcId": vpc.get("VpcId"),
                "Name": name,
                "State": vpc.get("State"),
                "CidrBlock": vpc.get("CidrBlock"),
                "IsDefault": vpc.get("IsDefault"),
                "Tags": vpc.get("Tags", [])
            })
        except Exception as e:
            print(f"Error processing VPC {vpc.get('VpcId')}: {e}")
            continue

    return vpcs


def get_empty_vpcs():
    vpcs = get_all_vpcs()
    empty = []

    for vpc in vpcs:
        try:
            vpc_id = vpc["VpcId"]

            # Skip default VPC — AWS creates this automatically
            if vpc.get("IsDefault"):
                continue

            # Check running EC2 instances in VPC
            instances_response = ec2.describe_instances(
                Filters=[
                    {"Name": "vpc-id", "Values": [vpc_id]},
                    {"Name": "instance-state-name", "Values": ["running", "stopped"]}
                ]
            )
            instance_count = sum(
                len(r["Instances"])
                for r in instances_response.get("Reservations", [])
            )

            # Check RDS instances in VPC
            rds_client = boto3.client("rds")
            rds_response = rds_client.describe_db_instances()
            rds_count = sum(
                1 for db in rds_response.get("DBInstances", [])
                if db.get("DBSubnetGroup", {}).get("VpcId") == vpc_id
            )

            # Check NAT gateways in VPC
            nat_response = ec2.describe_nat_gateways(
                Filters=[
                    {"Name": "vpc-id", "Values": [vpc_id]},
                    {"Name": "state", "Values": ["available"]}
                ]
            )
            nat_count = len(nat_response.get("NatGateways", []))

            total_resources = instance_count + rds_count + nat_count

            if total_resources == 0:
                empty.append({
                    "VpcId": vpc_id,
                    "Name": vpc.get("Name"),
                    "CidrBlock": vpc.get("CidrBlock"),
                    "IsDefault": vpc.get("IsDefault"),
                    "EC2Instances": instance_count,
                    "RDSInstances": rds_count,
                    "NatGateways": nat_count,
                    "Reason": "VPC has no running resources review it and consider deleting if not needed"
                })

        except Exception as e:
            print(f"Error checking VPC {vpc.get('VpcId')}: {e}")
            continue

    return empty


# ─── FACADE ──────────────────────────────────────────

def get_wasteful_network_resources():
    return {
        "idle_nat_gateways": len(get_idle_nat_gateways()),
        "empty_vpcs": len(get_empty_vpcs())
    }