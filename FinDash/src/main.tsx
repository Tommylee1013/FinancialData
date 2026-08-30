
  import { createRoot } from "react-dom/client";
  import App from "./app/App.tsx";
  import { loadDashboardData } from "./app/data/mockData.ts";
  import "./styles/index.css";

  loadDashboardData().finally(() => {
    createRoot(document.getElementById("root")!).render(<App />);
  });
  
