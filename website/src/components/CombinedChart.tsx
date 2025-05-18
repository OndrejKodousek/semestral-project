/**
 * @file CombinedChart.tsx
 * @brief Component for displaying a combined chart of multiple predictions
 * @details Shows real stock data alongside predictions from:
 * - Multiple articles
 * - Summarized analysis
 * - LSTM model
 * Includes functionality to download the chart as PNG
 */

import React, { useEffect, useState, useRef } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ChartOptions,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import annotationPlugin from "chartjs-plugin-annotation";
import { CombinedChartProps } from "../utils/interfaces";
import {
  generatePeriodDates,
  getCurrentDate,
  getEarliestDate,
  getLatestDate,
} from "../utils/date";
import { filterHistoricalData } from "../utils/parsing";
import { fetchSumAnalysis, fetchLSTMAnalysis } from "../utils/apiEndpoints";
import html2canvas from "html2canvas";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  annotationPlugin,
);

/**
 * @brief Combined chart component showing multiple prediction sources
 * @param predictionData - Array of prediction data from articles
 * @param historicalData - Array of historical stock prices
 * @param ticker - Stock ticker symbol
 * @param model - Model name used for predictions
 */
const CombinedChart: React.FC<CombinedChartProps> = ({
  predictionData,
  historicalData,
  ticker,
  model,
}) => {
  const [labels, setLabels] = useState<string[]>([]);
  const [realData, setRealData] = useState<number[]>([]);
  const [sumAnalysis, setSumAnalysis] = useState<{
    summary: string;
    predictions: { [key: string]: any };
  } | null>(null);
  const [sumAnalysisDate, setSumAnalysisDate] = useState<string | null>(null);
  const [lstmPredictions, setLstmPredictions] = useState<{
    [key: string]: number;
  } | null>(null);

  // Reset state when ticker changes
  useEffect(() => {
    setLabels([]);
    setRealData([]);
    setSumAnalysis(null);
    setSumAnalysisDate(null);
    setLstmPredictions(null);
  }, [ticker]);

  const chartRef = useRef<HTMLDivElement>(null);

  /**
   * @brief Handles downloading the chart as PNG
   * @async
   */
  const handleDownloadPNG = async () => {
    if (!chartRef.current) return;

    try {
      // Quality settings
      const scale = 4; // 4x scaling = ~384 DPI
      const quality = 1; // Maximum quality (0-1)

      // Create high-res canvas
      const canvas = await html2canvas(chartRef.current, {
        scale,
        logging: false,
        useCORS: true,
        allowTaint: true,
        backgroundColor: "#FFFFFF",
        windowWidth: chartRef.current.scrollWidth * scale,
        windowHeight: chartRef.current.scrollHeight * scale,
      });

      // Create download link
      const link = document.createElement("a");
      link.download = `${ticker}_stock_analysis_${new Date().toISOString().split("T")[0]}.png`;
      link.href = canvas.toDataURL("image/png", quality);
      link.click();

      // Clean up
      URL.revokeObjectURL(link.href);
    } catch (error) {
      console.error("Error generating image:", error);
    }
  };

  // Fetch summarized analysis and LSTM predictions
  useEffect(() => {
    /**
     * @brief Fetches summarized analysis data
     * @async
     */
    const fetchSumData = async () => {
      if (ticker && model) {
        const data = await fetchSumAnalysis(ticker, model);
        if (data && data.analysis) {
          setSumAnalysis({
            summary: data.analysis.summary || "No summary available.",
            predictions: {
              ...Object.fromEntries(
                Object.entries(data.analysis).filter(([key]) =>
                  key.startsWith("prediction_"),
                ),
              ),
            },
          });
          setSumAnalysisDate(data.analysis.analysis_date || getCurrentDate());
        } else {
          setSumAnalysis(null);
          setSumAnalysisDate(null);
        }
      } else {
        setSumAnalysis(null);
        setSumAnalysisDate(null);
      }
    };

    /**
     * @brief Fetches LSTM predictions
     * @async
     */
    const fetchLSTMData = async () => {
      if (ticker) {
        const data = await fetchLSTMAnalysis(ticker);
        if (data && typeof data === "object" && Object.keys(data).length > 0) {
          setLstmPredictions(data);
        } else {
          setLstmPredictions(null);
        }
      } else {
        setLstmPredictions(null);
      }
    };

    fetchSumData();
    fetchLSTMData();
  }, [ticker, model]);

  // Process prediction and historical data
  useEffect(() => {
    if (
      predictionData &&
      historicalData &&
      ticker &&
      predictionData.length > 0
    ) {
      const earliestDate = getEarliestDate(predictionData);
      const latestDate = getLatestDate(predictionData);

      if (earliestDate && latestDate) {
        const generatedLabels = generatePeriodDates(
          earliestDate,
          latestDate,
          12,
        );
        setLabels(generatedLabels);
        const stockPrices = filterHistoricalData(
          historicalData,
          generatedLabels,
        );
        setRealData(stockPrices);
      } else {
        setLabels([]);
        setRealData([]);
      }
    }
  }, [predictionData, historicalData, ticker]);

  /**
   * @brief Gets a unique color for each prediction source
   * @param source - Name of the prediction source
   * @returns RGB color string
   */
  const getColorForSource = (source: string) => {
    const colors = [
      "rgb(165, 118, 56)",
      "rgb(56, 165, 110)",
      "rgb(56, 103, 165)",
      "rgb(72, 56, 165)",
      "rgb(165, 56, 150)",
      "rgb(114, 165, 56)",
      "rgb(56, 165, 141)",
      "rgb(56, 85, 165)",
      "rgb(130, 56, 165)",
    ];
    if (!predictionData) return colors[0];
    const uniqueSources = Object.keys(
      predictionData.reduce(
        (acc, item) => {
          acc[item.source] = true;
          return acc;
        },
        {} as { [key: string]: boolean },
      ),
    );
    const index = uniqueSources.indexOf(source);
    return colors[index % colors.length];
  };

  // Prepare chart data
  const chartData = {
    labels: labels,
    datasets: [
      {
        label: "Real Data",
        data: realData,
        borderColor: "rgb(255, 0, 0)",
        borderDash: [5, 5],
      },
      ...(predictionData?.map((item) => ({
        label: item.source,
        data: labels.map((label) => {
          const predictionEntry = item.predictions[label];
          return predictionEntry ? predictionEntry.prediction : null;
        }),
        borderColor: getColorForSource(item.source),
        backgroundColor: getColorForSource(item.source)
          .replace(")", ", 0.2)")
          .replace("rgb(", "rgba("),
        tension: 0.1,
      })) ?? []),
      ...(sumAnalysis
        ? [
            {
              label: "Summarized Analysis",
              data: labels.map((_, index) => {
                if (!sumAnalysisDate) return null;
                const analysisIndex = labels.indexOf(sumAnalysisDate);
                if (analysisIndex === -1 || index < analysisIndex) {
                  return null;
                }
                const dayNumber = index - analysisIndex + 1;
                const predictionKey = `prediction_${dayNumber}_day`;
                return sumAnalysis.predictions[predictionKey] !== undefined
                  ? sumAnalysis.predictions[predictionKey]
                  : null;
              }),
              borderColor: "rgb(75, 130, 192)",
              borderDash: [5, 5],
            },
          ]
        : []),
      ...(lstmPredictions
        ? [
            {
              label: "LSTM Predictions",
              data: labels.map((label) => {
                const predictionValue = lstmPredictions[label];
                return predictionValue !== undefined ? predictionValue : null;
              }),
              borderColor: "rgb(32, 160, 28)",
              borderDash: [5, 5],
            },
          ]
        : []),
    ],
  };

  // Chart configuration options
  const chartOptions: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        title: {
          display: true,
          text: "Stock Price [$]",
          font: {
            size: 14,
            weight: "bold",
          },
        },
        ticks: {
          font: {
            size: 14,
          },
        },
      },
      x: {
        ticks: {
          font: {
            size: 14,
          },
        },
      },
    },
    plugins: {
      annotation: {
        annotations: {
          verticalLine: {
            type: "line",
            xMin: labels.indexOf(getCurrentDate()),
            xMax: labels.indexOf(getCurrentDate()),
            borderColor: "rgb(90, 0, 90)",
            borderWidth: 2,
            borderDash: [5, 5],
          },
        },
      },
      legend: {
        position: "top",
        labels: {
          font: {
            size: 14,
          },
          filter: (legendItem) => {
            const keepLegends = [
              "Real Data",
              "Summarized Analysis",
              "LSTM Predictions",
            ];
            return keepLegends.includes(legendItem.text);
          },
        },
      },
      title: {
        display: true,
        text: `${ticker} Stock Price and Predictions`,
        font: {
          size: 14,
          weight: "bold",
        },
      },
      tooltip: {
        mode: "index",
        intersect: false,
      },
    },
    interaction: {
      mode: "index",
      intersect: false,
    },
  };

  return (
    <div className="combined-chart">
      {/* <button onClick={handleDownloadPNG}>Download</button> */}
      {labels && labels.length > 0 ? (
        <div
          ref={chartRef}
          style={{
            width: "100%",
            minHeight: "400px",
            position: "relative",
          }}
        >
          <Line data={chartData} options={chartOptions} />
        </div>
      ) : (
        <p>Loading chart data for {ticker}...</p>
      )}
      {sumAnalysis && (
        <div className="analysis-summary">
          <h3>Summarized Analysis ({model})</h3>
          <p>{sumAnalysis.summary}</p>
          {sumAnalysisDate && (
            <p className="mb-0">Analysis date: {sumAnalysisDate}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default CombinedChart;
