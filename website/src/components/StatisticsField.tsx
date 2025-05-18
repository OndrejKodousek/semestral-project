/**
 * @file StatisticsField.tsx
 * @brief Container component for displaying different statistical views
 * @details Manages the display of different view modes:
 * 1. Article List
 * 2. Combined Chart
 * 3. Metrics
 * 4. Batch Downloader
 */

import React, { useEffect, useState } from "react";
import ArticleList from "./ArticleList";
import BatchDownloader from "./BatchDownloader";
import CombinedChart from "./CombinedChart";
import Metrics from "./Metrics";
import {
  StatisticsFieldProps,
  HistoricalData,
  PredictionData,
} from "../utils/interfaces";
import { fetchHistoricalData } from "../utils/apiEndpoints";
import { getEarliestDate } from "../utils/date";

/**
 * @brief Statistics container component
 * @param predictionData - Array of prediction data from articles
 * @param ticker - Stock ticker symbol
 * @param model - Selected AI model name
 * @param mode - Current view mode (1-4)
 * @param minArticles - Minimum articles filter value
 */
const StatisticsField: React.FC<StatisticsFieldProps> = ({
  predictionData,
  ticker,
  model,
  mode,
  minArticles,
}) => {
  const [historicalData, setHistoricalData] = useState<HistoricalData[]>([]);

  // Fetch historical data when ticker or prediction data changes
  useEffect(() => {
    // Clear previous data when ticker changes
    setHistoricalData([]);
    if (!ticker) {
      return;
    }

    /**
     * @brief Fetches historical stock data
     * @param currentTicker - Stock ticker to fetch data for
     * @param currentPredictionData - Prediction data for date range
     */
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
          setHistoricalData([]); // Clear data on error
        }
      } else {
        setHistoricalData([]);
      }
    };

    fetchData(ticker, predictionData);
  }, [ticker, predictionData]);

  // Filter prediction data for current ticker
  const relevantPredictionData =
    predictionData &&
    predictionData.length > 0 &&
    predictionData[0].ticker === ticker
      ? predictionData
      : null;

  return (
    <div className="h-100">
      {/* Mode 1: Article List View */}
      {mode === 1 && relevantPredictionData && (
        <ArticleList
          key={`article-list-${ticker}-${model}`}
          predictionData={relevantPredictionData}
          historicalData={historicalData}
          ticker={ticker}
        />
      )}

      {/* Mode 2: Combined Chart View */}
      {mode === 2 && (
        <CombinedChart
          key={`combined-chart-${ticker}-${model}`}
          predictionData={relevantPredictionData || []}
          historicalData={historicalData}
          ticker={ticker}
          model={model}
        />
      )}

      {/* Mode 3: Metrics View */}
      {mode === 3 && (
        <Metrics
          key={`metrics-${ticker}-${model}`}
          predictionData={relevantPredictionData || []}
          historicalData={historicalData}
          ticker={ticker}
        />
      )}

      {/* Mode 4: Batch Downloader View */}
      {mode === 4 && (
        <BatchDownloader
          models={[
            // Google AI Studio
            "gemini-2.5-flash-preview-04-17",
            "gemini-2.5-pro-preview-03-25",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-1.5-pro",
            // OpenRouter
            "deepseek/deepseek-chat:free",
            // Groq
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "gemma2-9b-it",
            "distil-whisper-large-v3-en",
            // Groq preview
            "deepseek-r1-distill-llama-70b",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "mistral-saba-24b",
            "qwen-qwq-32b",
          ]}
          minArticles={minArticles}
        />
      )}

      {mode === 1 && !relevantPredictionData && ticker && (
        <p>Loading analysis data for {ticker}...</p>
      )}
    </div>
  );
};

export default StatisticsField;
