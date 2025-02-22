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
    <div className="inset-container p-3 h-100">
      <div className="control-panel d-flex flex-column h-100 justify-content-between">
        <div className="d-flex justify-content-between align-items-center">
          <label className="me-2">Minimum Articles:</label>
          <input
            type="number"
            min="1"
            max="99"
            defaultValue={5}
            className="form-control"
            style={{ width: "80px" }}
            onChange={handleMinArticlesChange}
          />
        </div>

        <div className="mode-buttons">
          <button
            className={`mode-button ${mode === 1 ? "active" : ""}`}
            onClick={() => handleModeChange(1)}
          >
            Show individual articles
          </button>
          <button
            className={`mode-button ${mode === 2 ? "active" : ""}`}
            onClick={() => handleModeChange(2)}
          >
            Show large aggregated graph
          </button>
          <button
            className={`mode-button ${mode === 3 ? "active" : ""}`}
            onClick={() => handleModeChange(3)}
          >
            Show metrics
          </button>
        </div>

        <div>
          <button
            className={`mode-button ${isChecked ? "active" : ""}`}
            onClick={handleIncludeConfidenceChange} // Call the handler directly
          >
            Use Confidence
          </button>
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;
