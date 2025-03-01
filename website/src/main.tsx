import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
//import "./assets/styles/bootstrap.scss";
import "bootstrap/dist/css/bootstrap.min.css";
//import "./assets/styles/scrollbar.scss";
import "./assets/styles/article.scss";
//import "./assets/styles/backdrop.scss";
import "./assets/styles/layout.scss";
import "./assets/styles/button.scss";
import App from "./App.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
