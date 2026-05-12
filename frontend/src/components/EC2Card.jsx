import "./EC2Card.css";

function EC2Card({ instance }) {

  return (

    <div className="ec2-card">

      <h2>{instance.Name}</h2>

      <p>
        <strong>Instance Type:</strong> {instance.InstanceType}
      </p>

      <p>

        <strong>State:</strong>

        <span
            className={
            instance.State === "running"
                ? "status-running"
                : "status-stopped"
            }
        >

            {instance.State}

        </span>

      </p>

      <p>
        <strong>Public IP:</strong> {instance.PublicIpAddress}
      </p>

      <p>
        <strong>Availability Zone:</strong> {instance.AvailabilityZone}
      </p>

      <p>
        <strong>SSH Status:</strong>

        <span
            className={
            instance.SSHOpenToPublic
                ? "ssh-public"
                : "ssh-safe"
            }
        >

            {instance.SSHOpenToPublic
            ? " ⚠ Public SSH"
            : " ✅ Secure"}

        </span>
      </p>

    </div>

  );
}

export default EC2Card;