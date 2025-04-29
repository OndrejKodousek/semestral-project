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
import { CombinedChartProps } from "../utils/interfaces";
import {
  generatePeriodDates,
  getCurrentDate,
  getEarliestDate,
  getLatestDate,
} from "../utils/date";
import {
  filterHistoricalData,
  convertStockPriceToPercentChange,
} from "../utils/parsing";
import { fetchSumAnalysis, fetchLSTMAnalysis } from "../utils/apiEndpoints";

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

  const [lstmPredictions, setLstmPredictions] = useState<{
    [key: string]: number;
  } | null>(null);

  useEffect(() => {
    setLabels([]);
    setRealData([]);
    setSumAnalysis(null);
    setLstmPredictions(null);
  }, [ticker]);

  useEffect(() => {
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
        } else {
          setSumAnalysis(null);
        }
      } else {
        setSumAnalysis(null);
      }
    };

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

  const chartData = {
    labels: labels,
    datasets: [
      {
        label: "Real Data",
        data: realData,
        borderColor: "rgb(255, 0, 0)",
        backgroundColor: "rgba(0, 0, 0, 0.2)",
        borderDash: [5, 5],
        tension: 0.1,
      },
      ...(predictionData?.map((item) => ({
        label: item.source,
        data: labels.map((label) => {
          const predictionEntry = item.predictions[label];
          return predictionEntry ? predictionEntry.prediction : null; // Simplified access
        }),
        borderColor: getColorForSource(item.source),
        backgroundColor: getColorForSource(item.source)
          .replace(")", ", 0.2)")
          .replace("rgb(", "rgba("), // Safer replace
        tension: 0.1,
      })) ?? []),
      ...(sumAnalysis
        ? [
            {
              label: "Summarized Analysis",
              data: labels.map((label, index) => {
                const todayIndex = labels.indexOf(getCurrentDate());
                if (todayIndex === -1 || index < todayIndex) {
                  return null;
                }
                const dayNumber = index - todayIndex + 1;
                const predictionKey = `prediction_${dayNumber}_day`;
                return sumAnalysis.predictions[predictionKey] !== undefined
                  ? sumAnalysis.predictions[predictionKey]
                  : null;
              }),
              borderColor: "rgb(0, 0, 255)",
              backgroundColor: "rgba(0, 0, 255, 0.2)",
              borderDash: [5, 5],
              tension: 0.1,
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
              borderColor: "rgb(7, 224, 0)",
              backgroundColor: "rgba(17, 102, 0, 0.69)",
              borderDash: [5, 5],
              tension: 0.1,
            },
          ]
        : []),
    ],
  };

  const chartOptions: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        title: {
          display: true,
          text: "Stock Price [$]", // Assuming absolute price now
        },
      },
    },
    plugins: {
      annotation: {
        annotations: labels.includes(getCurrentDate())
          ? {
              // Check if current date exists in labels
              verticalLine: {
                type: "line",
                xMin: labels.indexOf(getCurrentDate()),
                xMax: labels.indexOf(getCurrentDate()),
                borderColor: "rgb(255, 99, 132)",
                borderWidth: 2,
                borderDash: [5, 5],
                label: {
                  content: "Today",
                  enabled: true,
                  position: "start",
                },
              },
            }
          : {}, // Provide empty object if date not found
      },
      legend: {
        position: "top" as const,
      },
      title: {
        display: true,
        text: `${ticker} Stock Price and Predictions`,
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
      {labels && labels.length > 0 ? (
        <Line data={chartData} options={chartOptions} />
      ) : (
        <p>Loading chart data for {ticker}...</p>
      )}
      {sumAnalysis && (
        <div
          style={{
            marginTop: "20px",
            padding: "10px",
            border: "1px solid #ccc",
            borderRadius: "5px",
          }}
        >
          <h3>Summarized Analysis ({model})</h3>
          <p>{sumAnalysis.summary}</p>
        </div>
      )}
    </div>
  );
};

export default CombinedChart;
