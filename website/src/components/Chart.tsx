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
import { ChartProps, HistoricalData } from "../utils/interfaces";
import { generateWeekDates, getCurrentDate } from "../utils/date";
import {
  parsePredictions,
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

  const predictionData = parsePredictions(predictions);

  const currentDate = getCurrentDate();
  const currentDayIndex = labels.indexOf(currentDate);

  useEffect(() => {
    if (historicalData && historicalData[0]) {
      const labels = generateWeekDates(published);
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
        data: convertToPercent(predictionData),
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
