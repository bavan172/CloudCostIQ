import { useEffect, useState } from "react";
import "./Dashboard.css";

function Dashboard() {

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

      <h1>CloudCostIQ Dashboard</h1>

      <div className="dashboard-cards">

        <div className="dashboard-card">
          <h2>Total Instances</h2>
          <p>{instances.length}</p>
        </div>

        <div className="dashboard-card">
          <h2>second card</h2>
          <p>pass</p>
        </div>

        <div className="dashboard-card">
          <h2>third card</h2>
          <p>pass</p>
        </div>

      </div>

    </div>
  );
}

export default Dashboard;