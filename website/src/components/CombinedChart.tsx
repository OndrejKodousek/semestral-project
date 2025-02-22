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
import { generateWeekDates } from "../utils/date";
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

// Define interfaces for the data structures
interface Article {
  title: string;
  ticker: string;
  published: string;
  predictions: {
    [key: string]: { prediction: number };
  };
}

interface CombinedChartProps {
  articles: Article[];
}

const getDateOnly = (published: string): string => {
  const dateObj = new Date(published);

  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, "0"); // Months are zero-based
  const day = String(dateObj.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
};

// Fetch historical data for the ticker
const fetchHistoricalData = async (
  ticker: string,
  published: string,
): Promise<number[]> => {
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

// Convert array values to percentages
const convertToPercent = (array: (number | null)[]): number[] => {
  return array.map((value) => {
    if (typeof value === "number" && !isNaN(value)) {
      return value * 100;
    }
    return NaN;
  });
};

const getEarliestPublishedDate = (articles: Article[]): string => {
  if (articles.length === 0) {
    throw new Error("Articles array is empty");
  }

  const publishedDates = articles.map((article) => new Date(article.published));

  const earliestDate = new Date(
    Math.min(...publishedDates.map((date) => date.getTime())),
  );

  const year = earliestDate.getFullYear();
  const month = String(earliestDate.getMonth() + 1).padStart(2, "0");
  const day = String(earliestDate.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
};

const CombinedChart: React.FC<CombinedChartProps> = ({ articles }) => {
  const [historicalData, setHistoricalData] = useState<number[]>([]);

  useEffect(() => {
    if (articles.length > 0) {
      const ticker = articles[0].ticker;
      const published = getEarliestPublishedDate(articles);
      fetchHistoricalData(ticker, published).then((data) => {
        setHistoricalData(data);
      });
    }
  }, [articles]);

  const labels = generateWeekDates(articles[0]?.published);

  // Prepare datasets for the chart
  const chartData = {
    labels: labels,
    datasets: [
      {
        label: "Historical Data",
        data: convertToPercent(historicalData),
        borderColor: "rgba(75, 192, 192, 1)",
        backgroundColor: "rgba(75, 192, 192, 0.2)",
        borderDash: [5, 5],
      },
      ...articles.map((article, index) => ({
        label: article.source,
        data: convertToPercent(
          Object.values(article.predictions).map((p) => p.prediction),
        ),
        borderColor: `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(
          Math.random() * 255,
        )}, ${Math.floor(Math.random() * 255)}, 1)`,
        backgroundColor: `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(
          Math.random() * 255,
        )}, ${Math.floor(Math.random() * 255)}, 0.2)`,
      })),
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
      legend: {
        display: false,
      },
    },
  };

  return (
    <div className="combined-graph">
      <Line data={chartData} options={chartOptions} />
    </div>
  );
};

export default CombinedChart;
