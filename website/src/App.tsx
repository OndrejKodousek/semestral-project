import React, { useState, useEffect } from "react";
import TickerSelect from "./components/TickerSelect";
import ControlPanel from "./components/ControlPanel";
import ModelSelect from "./components/ModelSelect";
import StatisticsField from "./components/StatisticsField";
import { PredictionData } from "./utils/interfaces";
import { fetchAnalysisData, fetchStockNames } from "./utils/apiEndpoints";
import { extractTicker } from "./utils/parsing";
import { motion } from "motion/react";

const App: React.FC = () => {
  const [predictionData, setPredictionData] = useState<PredictionData[]>([]);
  const [ticker, setTicker] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);
  const [minArticles, setMinArticles] = useState<number>(5);
  const [includeConfidence, setIncludeConfidence] = useState<number>(1);
  const [stockNames, setStockNames] = useState<string[]>([]);
  const [mode, setMode] = useState<number>(1);
  const [extractedTicker, setExtractedTicker] = useState<string | null>(null);

  includeConfidence;

  useEffect(() => {
    const fetchData = async () => {
      if (ticker && model) {
        setExtractedTicker(extractTicker(ticker));
        if (extractedTicker) {
          try {
            const data = await fetchAnalysisData(extractedTicker, model);
            setPredictionData(data);
          } catch (error) {
            console.error("Failed to fetch analysis data:", error);
            setPredictionData([]); // Clear prediction data on error
          }
        }
      }
    };

    fetchData();
  }, [ticker, model]);

  useEffect(() => {
    const fetchNames = async () => {
      if (model) {
        try {
          const stockNames = await fetchStockNames(model, minArticles);
          setStockNames(stockNames);
        } catch (error) {
          console.error("Failed to fetch stock names:", error);
          setStockNames([]); // Clear stock names on error
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

          <div className="col-3 grow-vert p-0">
            <div className="full-height-col bg-light">
              <div className="component-container">
                <TickerSelect setTicker={setTicker} stockNames={stockNames} />
              </div>
            </div>
          </div>

          <div className="col-7 grow-vert p-0">
            <div className="full-height-col bg-light">
              <div className="component-container">
                {predictionData.length > 0 &&
                ticker &&
                model &&
                extractedTicker ? (
                  <StatisticsField
                    predictionData={predictionData}
                    ticker={extractedTicker}
                    model={model}
                    mode={mode}
                  />
                ) : (
                  <div>Select model and ticker to view data</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div style={{ display: "none" }}>read/tmhmtznrmnyp#986b8b</div>
    </motion.div>
  );
};

export default App;
