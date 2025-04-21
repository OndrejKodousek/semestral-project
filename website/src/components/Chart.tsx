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
import { generateDateRange, getCurrentDate } from "../utils/date";
import {
  convertToPercent,
  filterHistoricalData,
  convertStockPriceToPercentChange,
} from "../utils/parsing";

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

const Chart: React.FC<ChartProps> = ({
  predictions,
  historicalData,
  published,
}) => {
  const [realData, setRealData] = useState<number[]>([]);
  const [labels, setLabels] = useState<(string | null)[]>([]);

  // Convert predictions to an array of { date, prediction }
  const predictionEntries = Object.entries(predictions).map(
    ([date, { prediction }]) => ({
      date,
      prediction,
    }),
  );

  const currentDate = getCurrentDate();
  const currentDayIndex = labels.indexOf(currentDate);

  useEffect(() => {
    if (historicalData && historicalData[0]) {
      const labels = generateDateRange(published, 3);
      const stockPrices = filterHistoricalData(historicalData, labels);
      const stockChanges = convertStockPriceToPercentChange(stockPrices);
      setRealData(stockChanges);
      setLabels(labels);
    }
  }, [historicalData]);

  const chartData = {
    labels: labels,
    datasets: [
      {
        label: "Real Data",
        data: convertToPercent(realData),
        borderColor: "rgba(153, 102, 255, 1)",
        backgroundColor: "rgba(153, 102, 255, 0.2)",
      },
      {
        label: "Prediction",
        data: labels.map((label) => {
          const predictionEntry = predictionEntries.find(
            (entry) => entry.date === label,
          );
          return predictionEntry
            ? convertToPercent([predictionEntry.prediction])[0]
            : null;
        }),
        borderColor: "rgba(75, 192, 192, 1)",
        backgroundColor: "rgba(75, 192, 192, 0.2)",
      },
    ],
  };

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
            borderColor: "red",
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
