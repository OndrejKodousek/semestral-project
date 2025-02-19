import React, { useState, useEffect } from "react";
import TickerSelect from "./components/TickerSelect";
import TimeSelect from "./components/TimeSelect";
import ModelSelect from "./components/ModelSelect";
import StatisticsField from "./components/StatisticsField";

interface PredictionData {
  title: string;
  source: string;
  link: string;
  predictions: {
    [key: string]: {
      prediction: number;
      confidence: number;
    };
  };
}

const App: React.FC = () => {
  const [data, setData] = useState<PredictionData[] | null>(null);
  const [ticker, setTicker] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);
  const [time, setTime] = useState<string | null>(null);
  const [stockNames, setStockNames] = useState<string[]>([]);

  time;

  // Fetch stock names when model changes
  useEffect(() => {
    const fetchStockNames = async () => {
      if (model) {
        try {
          const apiBaseUrl =
            window.location.hostname === "localhost"
              ? "http://localhost:5000"
              : "https://kodousek.cz";

          const response = await fetch(
            `${apiBaseUrl}/api/stocks?model=${model}`,
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
        setStockNames([]); // Clear stock names if no model is selected
      }
    };

    fetchStockNames();
  }, [model]);

  // Fetch data when ticker or model changes
  useEffect(() => {
    const fetchData = async () => {
      if (ticker && model) {
        try {
          const apiBaseUrl =
            window.location.hostname === "localhost"
              ? "http://localhost:5000"
              : "https://kodousek.cz";
          const response = await fetch(
            `${apiBaseUrl}/api/analysis?ticker=${ticker}&model=${model}`,
          );
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          const jsonData = await response.json();
          console.log("Fetched data:", jsonData); // Log the fetched data
          setData(jsonData);
        } catch (error) {
          console.error("Error fetching analysis data:", error);
          setData(null);
        }
      }
    };

    fetchData();
  }, [ticker, model]);

  return (
    <div className="container-fluid vh-100 vw-100 d-flex flex-column">
      <div className="row flex-grow-1">
        <div className="col-lg-2 col-md-5 d-flex flex-column">
          <div className="flex-grow-1 d-flex flex-column gap-3">
            <ModelSelect setModel={setModel} />
            <TimeSelect setTime={setTime} />
          </div>
        </div>

        <div className="col-lg-3 col-md-7 d-flex flex-column">
          <TickerSelect setTicker={setTicker} stockNames={stockNames} />
        </div>

        <div className="col-lg-7 col-md-12 d-flex flex-column">
          <div className="inset-container">
            <StatisticsField data={data} />
          </div>
        </div>
        <div className="hidden">read/tmhmtznrmnyp#986b8b</div>
      </div>
    </div>
  );
};

export default App;
