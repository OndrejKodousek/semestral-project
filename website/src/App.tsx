/**
 * @file App.tsx
 * @brief Main application component
 * @details The root component that manages application state and renders the main layout
 * including model selection, ticker selection, and statistics display components.
 */

import React, { useState, useEffect, useMemo } from "react";
import TickerSelect from "./components/TickerSelect";
import ControlPanel from "./components/ControlPanel";
import ModelSelect from "./components/ModelSelect";
import StatisticsField from "./components/StatisticsField";
import { PredictionData } from "./utils/interfaces";
import { fetchAnalysisData, fetchStockNames } from "./utils/apiEndpoints";
import { extractTicker } from "./utils/parsing";
import { motion } from "motion/react";

/**
 * @brief Main App component
 * @returns The root application component with all subcomponents
 */
const App: React.FC = () => {
  // State management for application data
  const [predictionData, setPredictionData] = useState<PredictionData[]>([]);
  const [tickerString, setTickerString] = useState<string>("");
  const [model, setModel] = useState<string>("");
  const [minArticles, setMinArticles] = useState<number>(3);
  const [includeConfidence, setIncludeConfidence] = useState<number>(1);
  const [stockNames, setStockNames] = useState<string[]>([]);
  const [mode, setMode] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Extract ticker symbol from ticker string (e.g., "AAPL - Apple Inc" -> "AAPL")
  const extractedTicker = useMemo(
    () => extractTicker(tickerString),
    [tickerString],
  );

  // Currently unused but kept for future functionality
  includeConfidence;

  // Fetch prediction data when ticker or model changes
  useEffect(() => {
    if (extractedTicker && model) {
      const fetchData = async () => {
        setIsLoading(true);
        setPredictionData([]);
        try {
          const data = await fetchAnalysisData(extractedTicker, model);
          setPredictionData(data ?? []);
        } catch (error) {
          console.error("Failed to fetch analysis data:", error);
          setPredictionData([]);
        } finally {
          setIsLoading(false);
        }
      };

      fetchData();
    } else {
      setPredictionData([]);
      setIsLoading(false);
    }
  }, [extractedTicker, model]);

  // Fetch available stock names when model or minArticles changes
  useEffect(() => {
    const fetchNames = async () => {
      if (model) {
        try {
          const names = await fetchStockNames(model, minArticles);
          setStockNames(names);
        } catch (error) {
          console.error("Failed to fetch stock names:", error);
          setStockNames([]);
        }
      } else {
        setStockNames([]);
      }
    };
    fetchNames();
  }, [model, minArticles]);

  return (
    <motion.div
      initial={{ opacity: 0, y: -50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="container-fluid">
        <div className="row">
          {/* Left Column - Model Selection and Control Panel */}
          <div className="col-2 grow-vert p-0">
            <div className="split-cell bg-light">
              <div className="component-container">
                <ModelSelect setModel={setModel} />
              </div>
            </div>
            <div className="split-cell bg-light">
              <div className="component-container">
                <ControlPanel
                  mode={mode}
                  setMode={setMode}
                  setMinArticles={setMinArticles}
                  setIncludeConfidence={setIncludeConfidence}
                />
              </div>
            </div>
          </div>

          {/* Middle Column - Ticker Selection */}
          <div className="col-3 grow-vert p-0">
            <div className="full-height-col bg-light">
              <div className="component-container">
                <TickerSelect
                  setTicker={setTickerString}
                  stockNames={stockNames}
                />
              </div>
            </div>
          </div>

          {/* Right Column - Statistics Display */}
          <div className="col-7 grow-vert p-0">
            <div className="full-height-col bg-light">
              <div className="component-container">
                {isLoading ? (
                  <div>Loading data...</div>
                ) : (predictionData &&
                    predictionData.length > 0 &&
                    extractedTicker &&
                    model) ||
                  mode == 4 ? (
                  <StatisticsField
                    key={`stats-${extractedTicker}-${model}`}
                    predictionData={predictionData}
                    ticker={extractedTicker || ""}
                    model={model}
                    mode={mode}
                    minArticles={minArticles}
                  />
                ) : predictionData === null && !isLoading ? (
                  <div>Select both model and ticker to view data</div>
                ) : (
                  <div>
                    No analysis data found for the selected ticker/model.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default App;
