// utils/downloadUtils.ts
import {
  fetchAnalysisData,
  fetchHistoricalData,
  fetchSumAnalysis,
} from "./apiEndpoints";
import { getEarliestDate } from "./date";
import { PredictionData, HistoricalData } from "./interfaces";

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
      [key: string]: number;
    };
  };
}

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

  const sumAnalysisResponse = await fetchSumAnalysis(ticker, model);
  if (!sumAnalysisResponse?.analysis) {
    throw new Error(`No sum analysis found for ${ticker}-${model}`);
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

  const data: PredictionExportData = {
    ticker,
    model,
    timestamp: new Date().toISOString(),
    predictionsByArticle: processedArticles,
    sumAnalysis: {
      summary: sumAnalysisResponse.analysis.summary || "No summary available.",
      predictions: Object.fromEntries(
        Object.entries(sumAnalysisResponse.analysis)
          .filter(([key]: [string, unknown]) => key.startsWith("prediction_"))
          .map(([key, value]: [string, unknown]) => [
            key.replace("prediction_", "").replace("_day", ""),
            value as number,
          ]),
      ),
    },
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
