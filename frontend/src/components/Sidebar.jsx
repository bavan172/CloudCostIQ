import "./Sidebar.css";
import { Link } from "react-router-dom";

function Sidebar() {

  return (
    <div className="sidebar">
      <h1 className="logo">CloudCostIQ</h1>
      <ul className="menu">
        <li className="menu-item">
            <Link to="/">Dashboard</Link>
        </li>
        <li className="menu-item">
            <Link to="/instances">EC2 Instances</Link>
        </li>
      </ul>
    </div>

  );
}

export default Sidebar;