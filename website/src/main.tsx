/**
 * @file main.tsx
 * @brief Application entry point
 * @details Renders the root React component with strict mode and global styles
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "bootstrap/dist/css/bootstrap.min.css";
import "./assets/styles/article.scss";
import "./assets/styles/backdrop.scss";
import "./assets/styles/layout.scss";
import "./assets/styles/button.scss";
import App from "./App.tsx";

/**
 * @brief Renders the application root component
 * @details Wraps the App component in StrictMode for development checks
 * and attaches it to the DOM element with id 'root'
 */
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
