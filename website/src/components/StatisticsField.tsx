import React, { useEffect, useState } from "react";
import ArticleList from "./ArticleList";
import CombinedChart from "./CombinedChart";
import { StatisticsFieldProps,  HistoricalData } from "../utils/interfaces";
import { fetchHistoricalData } from "../utils/apiEndpoints";
import { getEarliestDate } from "../utils/date";

const StatisticsField: React.FC<StatisticsFieldProps> = ({
  predictionData,
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
          predictionData={predictionData}
          historicalData={historicalData}
        />
      )}
      {mode === 2 && (
        <CombinedChart
          predictionData={predictionData}
          historicalData={historicalData}
        />
      )}
    </>
  );
};

export default StatisticsField;
