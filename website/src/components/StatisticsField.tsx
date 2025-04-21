import React, { useEffect, useState } from "react";
import ArticleList from "./ArticleList";
import CombinedChart from "./CombinedChart";
import { StatisticsFieldProps, HistoricalData } from "../utils/interfaces";
import { fetchHistoricalData } from "../utils/apiEndpoints";
import { getEarliestDate } from "../utils/date";

const StatisticsField: React.FC<StatisticsFieldProps> = ({
  predictionData,
  ticker,
  model,
  mode,
}) => {
  const [historicalData, setHistoricalData] = useState<HistoricalData[]>([]);

  useEffect(() => {
    if (predictionData) {
      const start = getEarliestDate(predictionData);
      const ticker = predictionData[0]["ticker"];

      const fetchData = async () => {
        if (ticker && start) {
          const historicalData = await fetchHistoricalData(ticker, start);
          setHistoricalData(historicalData);
        }
      };

      fetchData();
    }
  }, [predictionData]);

  return (
    <>
      {mode === 1 && (
        <ArticleList
          key={`combined-chart-<span class="math-inline">\{ticker\}\-</span>{model}`}
          predictionData={predictionData}
          historicalData={historicalData}
        />
      )}
      {mode === 2 && (
        <CombinedChart
          key={`combined-chart-<span class="math-inline">\{ticker\}\-</span>{model}`}
          predictionData={predictionData}
          historicalData={historicalData}
          ticker={ticker}
          model={model}
        />
      )}
    </>
  );
};

export default StatisticsField;
