import React, { useState, useEffect } from "react";
import TickerSelect from "./components/TickerSelect";
import ControlPanel from "./components/ControlPanel";
import ModelSelect from "./components/ModelSelect";
import StatisticsField from "./components/StatisticsField";
import { PredictionData } from "./utils/interfaces";
import { fetchAnalysisData, fetchStockNames } from "./utils/apiEndpoints";
import { extractTicker } from "./utils/parsing";

const App: React.FC = () => {
  const [data, setData] = useState<PredictionData[] | null>(null);
  const [ticker, setTicker] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);
  const [minArticles, setMinArticles] = useState<number>(5);
  const [includeConfidence, setIncludeConfidence] = useState<number>(1);
  const [stockNames, setStockNames] = useState<string[]>([]);
  const [mode, setMode] = useState<number>(1);

  useEffect(() => {
    const fetchData = async () => {
      if (ticker && model) {
        const extractedTicker = extractTicker(ticker);
        if (extractedTicker) {
          const data = await fetchAnalysisData(extractedTicker, model);
          setData(data);
        }
      }
    };

    fetchData();
  }, [ticker, model]);

  useEffect(() => {
    const fetchNames = async () => {
      if (model) {
        const stockNames = await fetchStockNames(model, minArticles);
        setStockNames(stockNames);
      } else {
        setStockNames([]);
      }
    };

    fetchNames();
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
