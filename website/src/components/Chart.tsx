import React, { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { ChartProps } from "../utils/interfaces";
import { generateWeekDates, getCurrentDate } from "../utils/date";
import annotationPlugin from "chartjs-plugin-annotation";

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

const parsePredictions = (predictions: any): string[] => {
  const output = [
    predictions["1_day"]["prediction"],
    predictions["2_day"]["prediction"],
    predictions["3_day"]["prediction"],
    predictions["4_day"]["prediction"],
    predictions["5_day"]["prediction"],
    predictions["6_day"]["prediction"],
    predictions["7_day"]["prediction"],
  ];
  return output;
};

const getDateOnly = (published: string): string => {
  const dateObj = new Date(published);

  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, "0"); // Months are zero-based
  const day = String(dateObj.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
};

const fetchHistoricalData = async (ticker: string, published: string) => {
  try {
    const apiBaseUrl =
      window.location.hostname === "localhost"
        ? "http://localhost:5000"
        : "https://kodousek.cz";

    const response = await fetch(
      `${apiBaseUrl}/api/historical-data?ticker=${ticker}&published=${getDateOnly(published)}`,
    );

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const jsonData = await response.json();
    return jsonData;
  } catch (error) {
    console.error("Error fetching historical data:", error);
    return [];
  }
};

const convertToPercent = (array: any[]): number[] => {
  return array.map((value) => {
    if (typeof value === "number" && !isNaN(value)) {
      return value * 100;
    }
    return NaN;
  });
};

const Chart: React.FC<ChartProps> = ({ published, predictions, ticker }) => {
  const [percentageChanges, setPercentageChanges] = useState<number[]>([]);
  const labels = generateWeekDates(published);

  useEffect(() => {
    const fetchData = async () => {
      if (ticker && published) {
        const changes = await fetchHistoricalData(ticker, published);
        setPercentageChanges(changes);
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
        data: convertToPercent(percentageChanges),
        borderColor: "rgba(153, 102, 255, 1)",
        backgroundColor: "rgba(153, 102, 255, 0.2)",
      },
    ],
  };

  const chartOptions = {
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
