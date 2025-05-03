import React, { useEffect, useState } from "react";
import ArticleList from "./ArticleList";
import CombinedChart from "./CombinedChart";
import {
  StatisticsFieldProps,
  HistoricalData,
  PredictionData,
} from "../utils/interfaces";
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
    // Clear previous data and set loading state when ticker changes to prevent error with mixed data
    setHistoricalData([]);
    if (!ticker) {
      return;
    }

    const fetchData = async (
      currentTicker: string,
      currentPredictionData: PredictionData[] | null,
    ) => {
      let start: string | null = null;
      if (
        currentPredictionData &&
        currentPredictionData.length > 0 &&
        currentPredictionData[0].ticker === currentTicker
      ) {
        try {
          start = getEarliestDate(currentPredictionData);
        } catch (e) {
          console.error("Could not get earliest date from prediction data:", e);
        }
      }

      if (currentTicker && start) {
        try {
          const fetchedHistoricalData = await fetchHistoricalData(
            currentTicker,
            start,
          );

          setHistoricalData(fetchedHistoricalData);
        } catch (error) {
          console.error("Failed to fetch historical data:", error);
          setHistoricalData([]); // Clear data
        } finally {
        }
      } else {
        setHistoricalData([]);
      }
    };

    fetchData(ticker, predictionData);
  }, [ticker, predictionData]);

  const relevantPredictionData =
    predictionData &&
    predictionData.length > 0 &&
    predictionData[0].ticker === ticker
      ? predictionData
      : null;

  return (
    <>
      {mode === 1 && relevantPredictionData && (
        <ArticleList
          key={`article-list-${ticker}-${model}`}
          predictionData={relevantPredictionData}
          historicalData={historicalData}
        />
      )}
      {mode === 2 && (
        <CombinedChart
          key={`combined-chart-${ticker}-${model}`}
          predictionData={relevantPredictionData || []}
          historicalData={historicalData}
          ticker={ticker}
          model={model}
        />
      )}
      {mode === 1 && !relevantPredictionData && ticker && (
        <p>Loading analysis data for {ticker}...</p>
      )}
    </>
  );
};

export default StatisticsField;
