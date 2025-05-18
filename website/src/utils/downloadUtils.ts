/**
 * @file downloadUtils.ts
 * @brief Utilities for downloading and exporting prediction data
 * @details Provides functions for downloading stock prediction data in JSON format
 * with proper formatting and error handling.
 */

import {
  fetchAnalysisData,
  fetchHistoricalData,
  fetchSumAnalysis,
} from "./apiEndpoints";
import { getEarliestDate } from "./date";
import { PredictionData, HistoricalData } from "./interfaces";

/**
 * @interface PredictionExportData
 * @brief Structure for exported prediction data
 * @property ticker - Stock ticker symbol
 * @property model - AI model name
 * @property timestamp - Export timestamp
 * @property predictionsByArticle - Array of article predictions
 * @property sumAnalysis - Summarized analysis data
 */
export interface PredictionExportData {
  ticker: string;
  model: string;
  timestamp: string;
  predictionsByArticle: Array<{
    source: string;
    articleDate: string;
    predictions: {
      [date: string]: {
        prediction: number;
        real: number | null;
        predictionDay: number;
      };
    };
  }>;
  sumAnalysis: {
    summary: string;
    predictions: {
      [key: string]: number | null;
    };
  };
}
/**
 * @brief Downloads all prediction data for a ticker-model combination
 * @param ticker - Stock ticker symbol
 * @param model - AI model name
 * @returns Promise that resolves when download is complete
 * @throws Error if no prediction data is found
 */
export async function downloadTickerModelData(
  ticker: string,
  model: string,
): Promise<void> {
  // Fetch all required data
  const predictionData = await fetchAnalysisData(ticker, model);
  if (!predictionData || predictionData.length === 0) {
    throw new Error(`No prediction data found for ${ticker}-${model}`);
  }

  const startDate = getEarliestDate(predictionData);
  const historicalData = await fetchHistoricalData(ticker, startDate);

  // Initialize sumAnalysis with null values in case fetching fails
  let sumAnalysis = {
    summary: "No summary available",
    predictions: {} as Record<string, number | null>,
  };

  try {
    const sumAnalysisResponse = await fetchSumAnalysis(ticker, model);
    if (sumAnalysisResponse?.analysis) {
      sumAnalysis = {
        summary: sumAnalysisResponse.analysis.summary || "No summary available",
        predictions: Object.fromEntries(
          Object.entries(sumAnalysisResponse.analysis)
            .filter(([key]: [string, unknown]) => key.startsWith("prediction_"))
            .map(([key, value]: [string, unknown]) => [
              key.replace("prediction_", "").replace("_day", ""),
              value as number | null,
            ]),
        ),
      };
    }
  } catch (error) {
    console.error(
      `Failed to fetch sum analysis for ${ticker}-${model}:`,
      error,
    );
    // Continue with null values for predictions
    sumAnalysis = {
      summary: "Failed to fetch analysis summary",
      predictions: {},
    };
  }

  // Create type-safe historical price map
  const historicalPriceMap: Record<string, number> = {};
  historicalData.forEach((item: HistoricalData) => {
    historicalPriceMap[item.date] = item.price;
  });

  // Process each article's predictions
  const processedArticles = predictionData.map((article: PredictionData) => {
    const predictionDates = Object.keys(article.predictions).sort();

    const predictions: Record<
      string,
      { prediction: number; real: number | null; predictionDay: number }
    > = {};
    predictionDates.forEach((date: string, index: number) => {
      const predictionDay = index + 1;
      predictions[date] = {
        prediction: article.predictions[date].prediction,
        real: historicalPriceMap[date] || null,
        predictionDay,
      };
    });

    return {
      source: article.source,
      articleDate: article.published,
      predictions,
    };
  });

  // Prepare final export data
  const data: PredictionExportData = {
    ticker,
    model,
    timestamp: new Date().toISOString(),
    predictionsByArticle: processedArticles,
    sumAnalysis,
  };

  // Trigger download
  const dataStr = JSON.stringify(data, null, 2);
  const blob = new Blob([dataStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = `${ticker}_${model}_${
    new Date().toISOString().split("T")[0]
  }.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
