/**
 * @file TickerSelect.tsx
 * @brief Component for selecting a stock ticker from available options
 * @details Displays a scrollable list of stock tickers that meet the
 * minimum articles requirement for the selected model.
 */

import React from "react";
import { TickerSelectProps } from "../utils/interfaces";

/**
 * @brief Ticker selection dropdown component
 * @param setTicker - Callback function to update selected ticker
 * @param stockNames - Array of available stock names/tickers
 */
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
        <div className="bold-text">Select model to show available stocks</div>
      )}
    </div>
  );
};

export default TickerSelect;
