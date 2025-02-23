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
import { generateWeekDates, getCurrentDate } from "../utils/date";
import { fetchHistoricalData } from "../utils/apiEndpoints";
import {
  parsePredictions,
  alignHistoricalData,
  convertToPercent,
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

const Chart: React.FC<ChartProps> = ({ published, predictions, ticker }) => {
  const [realData, setRealData] = useState<(number | null)[]>([]);
  const labels = generateWeekDates(published);

  useEffect(() => {
    const fetchData = async () => {
      if (ticker && published) {
        const data = await fetchHistoricalData(ticker, published);
        if (data && data.length > 0) {
          const alignedData = alignHistoricalData(data, published);
          setRealData(alignedData);
        }
      }
    };
    fetchData();
  }, [ticker, published]);

  const predictionData = parsePredictions(predictions);

  const currentDate = getCurrentDate();
  const currentDayIndex = labels.indexOf(currentDate);

  const chartData = {
    labels: labels,
    datasets: [
      {
        label: "Prediction",
        data: convertToPercent(predictionData),
        borderColor: "rgba(75, 192, 192, 1)",
        backgroundColor: "rgba(75, 192, 192, 0.2)",
      },
      {
        label: "Real Data",
        data: convertToPercent(realData),
        borderColor: "rgba(153, 102, 255, 1)",
        backgroundColor: "rgba(153, 102, 255, 0.2)",
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
            type: "line" as const,
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
