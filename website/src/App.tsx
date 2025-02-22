import React, { useState, useEffect } from "react";
import TickerSelect from "./components/TickerSelect";
import ControlPanel from "./components/ControlPanel";
import ModelSelect from "./components/ModelSelect";
import StatisticsField from "./components/StatisticsField";
import { PredictionData } from "./utils/interfaces";

const extractTicker = (input: string): string | null => {
  const match = input.match(/^([A-Z0-9.]+)/);
  return match ? match[1] : null;
};

const App: React.FC = () => {
  const [data, setData] = useState<PredictionData[] | null>(null);
  const [ticker, setTicker] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);
  const [minArticles, setMinArticles] = useState<number>(5);
  const [includeConfidence, setIncludeConfidence] = useState<number>(1);
  const [stockNames, setStockNames] = useState<string[]>([]);

  // Switch in control panel
  // 1 = Show individual articles
  // 2 = Show large aggregated graph
  // 3 = Show metrics
  const [mode, setMode] = useState<number>(1);

  useEffect(() => {
    // Main API call that fetches article data, with mode switch
    const fetchData = async () => {
      if (ticker && model) {
        try {
          const apiBaseUrl =
            window.location.hostname === "localhost"
              ? "http://localhost:5000"
              : "https://kodousek.cz";
          const extractedTicker = extractTicker(ticker);
          const response = await fetch(
            `${apiBaseUrl}/api/analysis?ticker=${extractedTicker}&model=${model}`,
          );
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          const jsonData = await response.json();
          setData(jsonData);
        } catch (error) {
          console.error("Error fetching analysis data:", error);
          setData(null);
        }
      }
    };

    fetchData();
  }, [ticker, model]);

  useEffect(() => {
    const fetchStockNames = async () => {
      if (model) {
        try {
          const apiBaseUrl =
            window.location.hostname === "localhost"
              ? "http://localhost:5000"
              : "https://kodousek.cz";

          const response = await fetch(
            `${apiBaseUrl}/api/stocks?model=${model}&min_articles=${minArticles}`,
          );
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          const jsonData: string[] = await response.json();
          setStockNames(jsonData);
        } catch (error) {
          console.error("Error fetching stock names:", error);
          setStockNames([]);
        }
      } else {
        setStockNames([]);
      }
    };

    fetchStockNames();
  }, [model, minArticles]);

  return (
    <div className="container-fluid vh-100 vw-100 d-flex flex-column">
      <div className="row flex-grow-1">
        <div className="col-lg-2 col-md-5 d-flex flex-column">
          <div className="flex-grow-1 d-flex flex-column gap-3">
            <ModelSelect setModel={setModel} />
            <ControlPanel
              mode={mode}
              setMode={setMode}
              setMinArticles={setMinArticles}
              setIncludeConfidence={setIncludeConfidence}
            />
          </div>
        </div>

        <div className="col-lg-3 col-md-7 d-flex flex-column">
          <TickerSelect setTicker={setTicker} stockNames={stockNames} />
        </div>

        <div className="col-lg-7 col-md-12 d-flex flex-column vh-100">
          <StatisticsField data={data} mode={mode} />
        </div>
        <div className="hidden">read/tmhmtznrmnyp#986b8b</div>
      </div>
    </div>
  );
};

export default App;
