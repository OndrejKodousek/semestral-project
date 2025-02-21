import React from "react";

interface TickerSelectProps {
  setTicker: (ticker: string) => void;
  stockNames: string[];
}

const TickerSelect: React.FC<TickerSelectProps> = ({
  setTicker,
  stockNames,
}) => {
  return (
    <div className="inset-container p-3 h-100">
      <div className="d-flex flex-column h-100">
        <h3 className="no-select">Choose company</h3>

        {stockNames ? (
          <select
            className="form-select flex-grow-1 overflow-y-auto"
            size={10}
            aria-label="Select item"
            onChange={(e) => setTicker(e.target.value)}
          >
            {stockNames.map((item, index) => (
              <option key={index} value={item}>
                {item}
              </option>
            ))}
          </select>
        ) : (
          <div className="bold-text">Loading stock names...</div>
        )}
      </div>
    </div>
  );
};

export default TickerSelect;
