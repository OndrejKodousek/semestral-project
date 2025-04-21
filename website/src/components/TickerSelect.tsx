import React from "react";
import { TickerSelectProps } from "../utils/interfaces";

const TickerSelect: React.FC<TickerSelectProps> = ({
  setTicker,
  stockNames,
}) => {
  return (
    <div className="h-100">
      {stockNames && Array.isArray(stockNames) && stockNames.length > 0 ? (
        <select
          className="w-100 h-100"
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
  );
};

export default TickerSelect;
