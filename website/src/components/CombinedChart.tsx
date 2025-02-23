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
import annotationPlugin from "chartjs-plugin-annotation";
import { CombinedChartProps } from "../utils/interfaces";
import { generateWeekDates, getEarliestPublishedDate } from "../utils/date";
import { convertToPercent } from "../utils/metricsCalculator";
import { fetchHistoricalData } from "../utils/apiEndpoints";

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

const CombinedChart: React.FC<CombinedChartProps> = ({ data }) => {
  const [historicalData, setHistoricalData] = useState<number[]>([]);

  useEffect(() => {
    if (data) {
      if (data.length > 0) {
        const ticker = data[0].ticker;
        const published = getEarliestPublishedDate(data);
        fetchHistoricalData(ticker, published).then((result) => {
          setHistoricalData(result);
        });
      }
    }
  }, [data]);

  var chartData;
  var chartOptions;
  if (data) {
    const labels = generateWeekDates(data[0]?.published);

    chartData = {
      labels: labels,
      datasets: [
        {
          label: "Historical Data",
          data: convertToPercent(historicalData),
          borderColor: "rgba(75, 192, 192, 1)",
          backgroundColor: "rgba(75, 192, 192, 0.2)",
          borderDash: [5, 5],
        },
        ...data.map((article) => ({
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

    chartOptions = {
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
  }

  return (
    <div className="combined-graph">
      {data && chartData && chartOptions && (
        <Line data={chartData} options={chartOptions} />
      )}
    </div>
  );
};

export default CombinedChart;
