import React, { useState } from "react";
import { ControlPanelProps } from "../utils/interfaces";

const ControlPanel: React.FC<ControlPanelProps> = ({
  mode,
  setMode,
  setMinArticles,
  setIncludeConfidence,
}) => {
  const [isChecked, setIsChecked] = useState(false);

  const handleModeChange = (selectedMode: number) => {
    setMode(selectedMode); // Update the selected mode
  };

  const handleMinArticlesChange = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    setMinArticles(Number(event.target.value));
  };

  const handleIncludeConfidenceChange = () => {
    const newCheckedState = !isChecked; // Toggle the state
    setIsChecked(newCheckedState);
    setIncludeConfidence(newCheckedState ? 1 : 0); // Update the parent state
  };

  return (
    <div className="h-100 d-flex flex-column justify-content-between">
      <div className="subcomponent-container mb-3">
        <span className="mx-1">Minimum articles:</span>
        <input
          type="number"
          min="1"
          max="99"
          defaultValue={5}
          onChange={handleMinArticlesChange}
        />
      </div>

      {/* Buttons for modes */}
      <div className="subcomponent-container mb-3">
        <div className="d-flex flex-column align-items-center">
          <button
            className={`m-1 button ${mode === 1 ? "active" : ""}`}
            onClick={() => handleModeChange(1)}
          >
            Individual articles
          </button>
          <button
            className={`m-1 button ${mode === 2 ? "active" : ""}`}
            onClick={() => handleModeChange(2)}
          >
            Aggregated graph
          </button>
          <button
            className={`m-1 button ${mode === 3 ? "active" : ""}`}
            onClick={() => handleModeChange(3)}
          >
            Show metrics
          </button>
        </div>
      </div>

      {/* Use Confidence button */}
      <div className="subcomponent-container">
        <div className="d-flex flex-column align-items-center">
          <button
            className={`m-1 button ${isChecked ? "active" : ""}`}
            onClick={handleIncludeConfidenceChange}
          >
            Use Confidence
          </button>
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;
