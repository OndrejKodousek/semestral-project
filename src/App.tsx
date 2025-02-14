import React, { useState, useEffect } from "react";
import TickerSelect from "./components/TickerSelect";
import TimeSelect from "./components/TimeSelect";
import ModelSelect from "./components/ModelSelect";
import StatisticsField from "./components/StatisticsField";
import UpdateButton from "./components/UpdateButton";

interface PredictionData {
  title: string;
  source: string;
  prediction: string;
  confidence: string;
  link: string;
}

const App: React.FC = () => {
  const [data, setData] = useState<PredictionData[] | null>(null);

  const [ticker, setTicker] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);
  const [time, setTime] = useState<string | null>(null);

  const [stockNames, setStockNames] = useState<string[]>([]);

  useEffect(() => {
    const fetchStockNames = async () => {
      try {
        const response = await fetch("https://kodousek.cz/api/stocks");
        if (!response.ok) { 
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const jsonData: string[] = await response.json();
        setStockNames(jsonData);
      } catch (error) {
        console.error("Error fetching stock names:", error);
      }
    };

    fetchStockNames();
  }, []);

  return (
    <div className="container-fluid vh-100 d-flex flex-column">
      <div className="row flex-grow-1">
        <div className="col-3 d-flex flex-column">
          <TickerSelect setTicker={setTicker} stockNames={stockNames} />
        </div>
        <div className="hidden">read/tmhmtznrmnyp#986b8b</div>
        <div className="col-2 d-flex flex-column">
          <div className="flex-grow-1 d-flex flex-column gap-3">
            <ModelSelect setModel={setModel} />
            <TimeSelect setTime={setTime} />
            <UpdateButton
              ticker={ticker}
              model={model}
              time={time}
              setData={setData}
            />
          </div>
        </div>

        <div className="col-7 d-flex flex-column">
          <div className="inset-container">
            <StatisticsField data={data} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
