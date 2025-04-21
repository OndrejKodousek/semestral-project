import React, { useState, useEffect, useMemo } from "react"; // Added useMemo
import TickerSelect from "./components/TickerSelect";
import ControlPanel from "./components/ControlPanel";
import ModelSelect from "./components/ModelSelect";
import StatisticsField from "./components/StatisticsField";
import { PredictionData } from "./utils/interfaces";
import { fetchAnalysisData, fetchStockNames } from "./utils/apiEndpoints";
import { extractTicker } from "./utils/parsing";
import { motion } from "motion/react";

const App: React.FC = () => {
  // Keep existing states
  const [predictionData, setPredictionData] = useState<PredictionData[] | null>(
    null,
  ); // Initialize as null
  const [tickerString, setTickerString] = useState<string | null>(null); // Renamed for clarity
  const [model, setModel] = useState<string | null>(null);
  const [minArticles, setMinArticles] = useState<number>(5);
  const [includeConfidence, setIncludeConfidence] = useState<number>(1);
  const [stockNames, setStockNames] = useState<string[]>([]);
  const [mode, setMode] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(false); // Added loading state

  // Memoize extracted ticker to avoid recalculation and ensure consistency
  const extractedTicker = useMemo(
    () => (tickerString ? extractTicker(tickerString) : null),
    [tickerString],
  );

  includeConfidence; // If this is unused, consider removing it

  // Effect for fetching analysis data
  useEffect(() => {
    // Only fetch if we have a valid ticker and model
    if (extractedTicker && model) {
      const fetchData = async () => {
        setIsLoading(true); // Start loading
        setPredictionData(null); // Clear previous data immediately
        try {
          // Fetch with the current extractedTicker and model
          const data = await fetchAnalysisData(extractedTicker, model);
          setPredictionData(data ?? []); // Set new data, ensure it's an array even if null returned
        } catch (error) {
          console.error("Failed to fetch analysis data:", error);
          setPredictionData([]); // Clear prediction data on error
        } finally {
          setIsLoading(false); // Stop loading
        }
      };

      fetchData();
    } else {
      // Clear data if ticker or model is missing
      setPredictionData(null);
      setIsLoading(false);
    }
  }, [extractedTicker, model]); // Depend on the memoized extractedTicker and model

  // Effect for fetching stock names (remains the same)
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
          {/* Left Column (ModelSelect, ControlPanel) */}
          <div className="col-2 grow-vert p-0">
            {/* ... ModelSelect and ControlPanel sections ... */}
            <div className="split-cell bg-light">
                           {" "}
              <div className="component-container">
                                <ModelSelect setModel={setModel} /> {" "}
              </div>
                        {" "}
            </div>
                       {" "}
            <div className="split-cell bg-light">
                           {" "}
              <div className="component-container">
                               {" "}
                <ControlPanel
                  mode={mode}
                  setMode={setMode}
                  setMinArticles={setMinArticles}
                  setIncludeConfidence={setIncludeConfidence}
                />
                             {" "}
              </div>
                         {" "}
            </div>
          </div>

          {/* Middle Column (TickerSelect) */}
          <div className="col-3 grow-vert p-0">
            <div className="full-height-col bg-light">
              <div className="component-container">
                {/* Pass setTickerString to TickerSelect */}
                <TickerSelect
                  setTicker={setTickerString}
                  stockNames={stockNames}
                />
              </div>
            </div>
          </div>

          {/* Right Column (StatisticsField) */}
          <div className="col-7 grow-vert p-0">
            <div className="full-height-col bg-light">
              <div className="component-container">
                {/* Conditional rendering based on loading and data state */}
                {isLoading ? (
                  <div>Loading data...</div>
                ) : predictionData &&
                  predictionData.length > 0 &&
                  extractedTicker &&
                  model ? (
                  // Pass extractedTicker directly
                  <StatisticsField
                    // Add the key prop here to fix the second issue (chart residuals)
                    key={`stats-${extractedTicker}-${model}`}
                    predictionData={predictionData}
                    ticker={extractedTicker}
                    model={model}
                    mode={mode}
                  />
                ) : predictionData === null && !isLoading ? (
                  // Only show select message if not loading and data is truly null (initial state)
                  <div>Select model and ticker to view data</div>
                ) : (
                  // Handle case where data is fetched but empty
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
