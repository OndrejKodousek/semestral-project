import React, { useState, useEffect, useMemo } from "react";
import TickerSelect from "./components/TickerSelect";
import ControlPanel from "./components/ControlPanel";
import ModelSelect from "./components/ModelSelect";
import StatisticsField from "./components/StatisticsField";
import { PredictionData } from "./utils/interfaces";
import { fetchAnalysisData, fetchStockNames } from "./utils/apiEndpoints";
import { extractTicker } from "./utils/parsing";
import { motion } from "motion/react";

const App: React.FC = () => {
  const [predictionData, setPredictionData] = useState<PredictionData[] | null>(
    null,
  );
  const [tickerString, setTickerString] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);
  const [minArticles, setMinArticles] = useState<number>(5);
  const [includeConfidence, setIncludeConfidence] = useState<number>(1);
  const [stockNames, setStockNames] = useState<string[]>([]);
  const [mode, setMode] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const extractedTicker = useMemo(
    () => (tickerString ? extractTicker(tickerString) : null),
    [tickerString],
  );

  includeConfidence;

  useEffect(() => {
    // Only fetch with valid ticker and model
    if (extractedTicker && model) {
      const fetchData = async () => {
        setIsLoading(true);
        setPredictionData(null);
        try {
          const data = await fetchAnalysisData(extractedTicker, model);
          setPredictionData(data ?? []);
        } catch (error) {
          console.error("Failed to fetch analysis data:", error);
          setPredictionData([]); // Clear prediction data on error
        } finally {
          setIsLoading(false);
        }
      };

      fetchData();
    } else {
      // Clear data if ticker or model is missing
      setPredictionData(null);
      setIsLoading(false);
    }
  }, [extractedTicker, model]); // Depend on the memoized extractedTicker and model

  // Fetching stock names
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
            <div className="split-cell bg-light">
              <div className="component-container">
                <ModelSelect setModel={setModel} /> {" "}
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

          {/* Middle Column (TickerSelect) */}
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

          {/* Right Column (StatisticsField) */}
          <div className="col-7 grow-vert p-0">
            <div className="full-height-col bg-light">
              <div className="component-container">
                {isLoading ? (
                  <div>Loading data...</div>
                ) : predictionData &&
                  predictionData.length > 0 &&
                  extractedTicker &&
                  model ? (
                  <StatisticsField
                    key={`stats-${extractedTicker}-${model}`}
                    predictionData={predictionData}
                    ticker={extractedTicker}
                    model={model}
                    mode={mode}
                  />
                ) : predictionData === null && !isLoading ? (
                  // Only show select message if not loading and data is null (initial state)
                  <div>Select model and ticker to view data</div>
                ) : (
                  // Data is fetched but empty
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
