import { useEffect, useState } from "react";

function App() {

  const [instances, setInstances] = useState([]);

  useEffect(() => {

    fetch("http://127.0.0.1:5000/")
      .then((response) => response.json())
      .then((data) => {
        setInstances(data);
      });

  }, []);

  return (

    <div>

      <h1>CloudCostIQ</h1>

      {instances.map((instance) => (

        <div key={instance.InstanceId}>

          <h2>{instance.Name}</h2>

          <p>{instance.InstanceType}</p>

          <p>{instance.State}</p>

          <p>
            SSH Open:
            {instance.SSHOpenToPublic ? " Yes" : " No"}
          </p>

        </div>

      ))}

    </div>
  );
}

export default App;