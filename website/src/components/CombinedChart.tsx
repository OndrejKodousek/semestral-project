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
  convertToPercent,
  filterHistoricalData,
  convertStockPriceToPercentChange,
} from "../utils/parsing";
import { fetchSumAnalysis } from "../utils/apiEndpoints"; // Import the new function

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
    predictions: { [key: string]: number };
  } | null>(null);

  // Fetch summarized analysis data
  useEffect(() => {
    const fetchData = async () => {
      if (ticker && model) {
        const data = await fetchSumAnalysis(ticker, model);
        console.log("DATA:", data);
        if (data) {
          setSumAnalysis({
            summary: data.analysis.summary,
            predictions: {
              ...Object.fromEntries(
                Object.entries(data.analysis).filter(([key]) =>
                  key.startsWith("prediction_"),
                ),
              ),
            },
          });
        }
      }
      console.log(sumAnalysis);
    };

    fetchData();
  }, [ticker, model]);

  // Generate labels and real data
  useEffect(() => {
    if (predictionData && historicalData) {
      const earliestDate = getEarliestDate(predictionData);
      const latestDate = getLatestDate(predictionData);

      const labels = generatePeriodDates(earliestDate, latestDate, 12);
      setLabels(labels);

      const stockPrices = filterHistoricalData(historicalData, labels);
      const stockChanges = convertStockPriceToPercentChange(stockPrices);
      setRealData(stockChanges);
    }
  }, [predictionData, historicalData]);

  // Get color for source
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
    const index = Object.keys(
      predictionData.reduce(
        (acc, item) => {
          acc[item.source] = true;
          return acc;
        },
        {} as { [key: string]: boolean },
      ),
    ).indexOf(source);
    return colors[index % colors.length];
  };

  // Chart data
  const chartData = {
    labels: labels,
    datasets: [
      {
        label: "Real Data",
        data: convertToPercent(realData),
        borderColor: "rgb(255, 0, 0)",
        backgroundColor: "rgba(0, 0, 0, 0.2)",
      },
      ...predictionData.map((item) => ({
        label: item.source,
        data: labels.map((label) => {
          const predictionEntry = item.predictions[label];
          return predictionEntry
            ? convertToPercent([predictionEntry.prediction])[0]
            : null;
        }),
        borderColor: getColorForSource(item.source),
        backgroundColor: getColorForSource(item.source).replace(
          ", 1)",
          ", 0.2)",
        ),
      })),
      // Add summarized analysis data as a new dataset
      ...(sumAnalysis
        ? [
            {
              label: "Summarized Analysis",
              data: labels.map((label) => {
                const predictionKey = `prediction_${labels.indexOf(label) + 1}_day`;
                return sumAnalysis.predictions[predictionKey]
                  ? convertToPercent([
                      sumAnalysis.predictions[predictionKey],
                    ])[0]
                  : null;
              }),
              borderColor: "rgb(0, 0, 255)",
              backgroundColor: "rgba(0, 0, 255, 0.2)",
              borderDash: [5, 5],
            },
          ]
        : []),
    ],
  };

  // Chart options
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
            xMin: labels.indexOf(getCurrentDate()),
            xMax: labels.indexOf(getCurrentDate()),
            borderColor: "red",
            borderWidth: 2,
            borderDash: [5, 5],
          },
        },
      },
      legend: {
        display: false,
      },
    },
  };

  return (
    <div>
      <div className="combined-chart">
        <Line data={chartData} options={chartOptions} />
      </div>
      <div>
        {sumAnalysis ? (
          <div>
            <hr />
            <h3>Summarized Analysis</h3>
            <p>{sumAnalysis.summary}</p>
          </div>
        ) : (
          <p>Loading summarized analysis...</p>
        )}
      </div>
    </div>
  );
};

export default CombinedChart;
