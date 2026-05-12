import { useEffect, useState } from "react";
import "./Instances.css";
import EC2Card from "../components/EC2Card";

function Instances() {

  const [instances, setInstances] = useState([]);

  useEffect(() => {

    fetch("http://127.0.0.1:5000/")
      .then((response) => response.json())
      .then((data) => {
        setInstances(data);
      });

  }, []);

  return (

    <div className="instances-container" >

      {instances.map((instance) => (

        <EC2Card
          key={instance.InstanceId}
          instance={instance}
        />

      ))}

    </div>
  );
}

export default Instances;