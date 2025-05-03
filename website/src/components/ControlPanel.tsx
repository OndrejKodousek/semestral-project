import React from "react";
import { ControlPanelProps } from "../utils/interfaces";

const ControlPanel: React.FC<ControlPanelProps> = ({
  mode,
  setMode,
  setMinArticles,
}) => {
  const handleModeChange = (selectedMode: number) => {
    setMode(selectedMode);
  };

  const handleMinArticlesChange = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    setMinArticles(Number(event.target.value));
  };

  return (
    <div className="h-100 d-flex flex-column justify-content-between">
      <div className="subcomponent-container mb-3 d-flex flex-column align-items-start">
        <span className="mb-2">Minimum articles:</span>

        <input
          type="number"
          min="1"
          max="99"
          defaultValue={5}
          onChange={handleMinArticlesChange}
          className="mb-2"
        />

        <button
          className={`mb-2 button ${mode === 1 ? "active" : ""}`}
          onClick={() => handleModeChange(1)}
        >
          Individual articles
        </button>

        <button
          className={`mb-2 button ${mode === 2 ? "active" : ""}`}
          onClick={() => handleModeChange(2)}
        >
          Aggregated graph
        </button>

        <button
          className={`button ${mode === 3 ? "active" : ""}`}
          onClick={() => handleModeChange(3)}
        >
          Show metrics
        </button>
      </div>
    </div>
  );
};

export default ControlPanel;
