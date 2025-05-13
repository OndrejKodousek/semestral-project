import React, { useEffect, useState } from "react";
import { fetchSumAnalysis } from "../utils/apiEndpoints";
import { getCurrentDate } from "../utils/date";
import { CombinedChartProps } from "../utils/interfaces";

interface PredictionExportData {
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

const CombinedChart: React.FC<CombinedChartProps> = ({
  predictionData,
  historicalData,
  ticker,
  model,
}) => {
  const [sumAnalysis, setSumAnalysis] = useState<{
    summary: string;
    predictions: { [key: string]: any };
  } | null>(null);
  const [exportData, setExportData] = useState<PredictionExportData | null>(
    null,
  );

  useEffect(() => {
    const fetchSumData = async () => {
      if (ticker && model) {
        const data = await fetchSumAnalysis(ticker, model);
        if (data && data.analysis) {
          setSumAnalysis({
            summary: data.analysis.summary || "No summary available.",
            predictions: Object.fromEntries(
              Object.entries(data.analysis)
                .filter(([key]) => key.startsWith("prediction_"))
                .map(([key, value]) => [
                  key.replace("prediction_", "").replace("_day", ""),
                  value,
                ]),
            ),
          });
        }
      }
    };

    fetchSumData();
  }, [ticker, model]);

  useEffect(() => {
    if (predictionData && historicalData && ticker && sumAnalysis) {
      // Create a map of date to real price for quick lookup
      const historicalPriceMap = historicalData.reduce<Record<string, number>>(
        (acc, item) => {
          acc[item.date] = item.price;
          return acc;
        },
        {},
      );

      // Process each article's predictions
      const processedArticles = predictionData.map((article) => {
        const predictionDates = Object.keys(article.predictions).sort();

        const predictions = predictionDates.reduce<{
          [date: string]: {
            prediction: number;
            real: number | null;
            predictionDay: number;
          };
        }>((acc, date, index) => {
          const predictionDay = index + 1;
          acc[date] = {
            prediction: article.predictions[date].prediction,
            real: historicalPriceMap[date] || null,
            predictionDay,
          };
          return acc;
        }, {});

        return {
          source: article.source,
          articleDate: article.published,
          predictions,
        };
      });

      // Prepare the final export data
      const data: PredictionExportData = {
        ticker,
        model,
        timestamp: new Date().toISOString(),
        predictionsByArticle: processedArticles,
        sumAnalysis: {
          summary: sumAnalysis.summary,
          predictions: sumAnalysis.predictions,
        },
      };

      setExportData(data);
    }
  }, [predictionData, historicalData, ticker, sumAnalysis]);

  useEffect(() => {
    if (exportData) {
      const dataStr = JSON.stringify(exportData, null, 2);
      const blob = new Blob([dataStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = `${ticker}_${model}_2025-05-12.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  }, [exportData]);

  return (
    <div className="data-exporter">
      <h2>
        Data Export for {ticker} ({model})
      </h2>
      {exportData ? (
        <p>Download started automatically...</p>
      ) : (
        <p>Preparing data for download...</p>
      )}
    </div>
  );
};

export default CombinedChart;
