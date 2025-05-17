/**
 * @file ArticleChart.tsx
 * @brief Component for displaying stock price charts with predictions
 * @details This component renders a line chart showing:
 * - Historical stock prices
 * - Model predictions
 * - Optional LSTM predictions
 * Uses Chart.js for rendering
 */

import React, { useEffect, useState } from "react";
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
import { ChartProps } from "../utils/interfaces";
import {
  generateDateRange,
  getCurrentDate,
  getDateDifferenceSigned,
} from "../utils/date";
import { filterHistoricalData } from "../utils/parsing";
import { fetchLSTMAnalysis } from "../utils/apiEndpoints";

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
 * @brief Chart component displaying stock data and predictions
 * @param predictions - Object containing prediction data by date
 * @param historicalData - Array of historical stock prices
 * @param published - Publication date of the article
 * @param ticker - Stock ticker symbol
 */
const Chart: React.FC<ChartProps> = ({
  predictions,
  historicalData,
  published,
  ticker,
}) => {
  const [realData, setRealData] = useState<number[]>([]);
  const [labels, setLabels] = useState<(string | null)[]>([]);
  const [lstmPredictions, setLstmPredictions] = useState<{
    [key: string]: number;
  }>();

  // Convert predictions object to array of entries
  const predictionEntries = Object.entries(predictions).map(
    ([date, { prediction }]) => ({
      date,
      prediction,
    }),
  );

  const currentDate = getCurrentDate();
  const currentDayIndex = labels.indexOf(currentDate);

  // Load historical data when it changes
  useEffect(() => {
    if (historicalData && historicalData[0]) {
      const labels = generateDateRange(published, 0);
      const stockPrices = filterHistoricalData(historicalData, labels);
      setRealData(stockPrices);
      setLabels(labels);
    }
  }, [historicalData]);

  // Fetch LSTM predictions when ticker changes
  useEffect(() => {
    const fetchLSTMData = async () => {
      if (ticker) {
        const data = await fetchLSTMAnalysis(ticker);
        if (data && typeof data === "object" && Object.keys(data).length > 0) {
          setLstmPredictions(data);
        }
      }
    };

    fetchLSTMData();
  }, [ticker]);

  // Determine if LSTM predictions should be shown
  let shouldShowLstm;
  const latestLabelDate = labels[labels.length - 1];
  if (latestLabelDate) {
    const lstmDates = lstmPredictions ? Object.keys(lstmPredictions) : [];
    const earliestLstmDate = lstmDates.length > 0 ? lstmDates[0] : null;

    // Calculate if LSTM predictions are in range
    shouldShowLstm =
      earliestLstmDate &&
      getDateDifferenceSigned(latestLabelDate, earliestLstmDate) <= 1;
  }

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
      {
        label: "Prediction",
        data: labels.map((label) => {
          const predictionEntry = predictionEntries.find(
            (entry) => entry.date === label,
          );
          return predictionEntry ? [predictionEntry.prediction][0] : null;
        }),
        borderColor: "rgb(75, 130, 192)",
        borderDash: [5, 5],
      },
      ...(shouldShowLstm && lstmPredictions
        ? [
            {
              label: "LSTM Predictions",
              data: labels.map((label) =>
                label && lstmPredictions[label] !== undefined
                  ? lstmPredictions[label]
                  : null,
              ),
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
    scales: {
      y: {
        title: {
          display: true,
          text: "Change [%]",
        },
      },
    },
    plugins: {
      annotation: {
        annotations: {
          verticalLine: {
            type: "line",
            xMin: currentDayIndex,
            xMax: currentDayIndex,
            borderColor: "rgb(90, 0, 90)",
            borderWidth: 2,
            borderDash: [5, 5],
          },
        },
      },
    },
  };

  return (
    <div className="graph">
      <Line data={chartData} options={chartOptions} />
    </div>
  );
};

export default Chart;
