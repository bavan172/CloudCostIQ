import boto3
import json

ec2 = boto3.client("ec2")

        
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
                "MonitoringState": instance.get("Monitoring", {}).get("State")
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


print(json.dumps(get_instances(), indent=4))
