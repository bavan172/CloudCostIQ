import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Instances from "./pages/Instances";
import EC2Card from "./components/EC2Card";
import "./App.css";

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

    <BrowserRouter>

      <div style={{ display: "flex" }}>

        <Sidebar />

        <div style={{ padding: "20px", width: "100%" }}>
          <Routes>

            <Route
              path="/"
              element={<Dashboard />}
            />

            <Route
              path="/instances"
              element={<Instances />}
            />

          </Routes>
        </div>

      </div>

    </BrowserRouter>
  );
}

export default App;