import React, { useEffect, useState, useCallback, useMemo } from "react";
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

// Define the expected structure for analysis data more explicitly
interface AnalysisData {
  summary: string;
  predictions: { [key: string]: any }; // Use 'any' for now, or define prediction structure
}

const CombinedChart: React.FC<CombinedChartProps> = ({
  predictionData,
  historicalData,
  ticker,
  model,
}) => {
  const [labels, setLabels] = useState<string[]>([]);
  const [realData, setRealData] = useState<number[]>([]);
  const [sumAnalysis, setSumAnalysis] = useState<AnalysisData | null>(null);
  const [LSTMAnalysis, setLSTMAnalysis] = useState<AnalysisData | null>(null);
  // State to track if download has occurred for the current ticker/model combination
  const [hasDownloadedForCurrentTicker, setHasDownloadedForCurrentTicker] =
    useState(false);

  // Reset download flag when ticker or model changes
  useEffect(() => {
    setHasDownloadedForCurrentTicker(false);
  }, [ticker, model]);

  // --- Data Fetching useEffect ---
  useEffect(() => {
    // Reset states on new ticker/model before fetching
    setSumAnalysis(null);
    setLSTMAnalysis(null);

    const fetchAnalyses = async () => {
      if (ticker) {
        // Fetch Sum Analysis only if model is also provided
        if (model) {
          try {
            const sumData = await fetchSumAnalysis(ticker, model);
            if (sumData?.analysis) {
              setSumAnalysis({
                summary: sumData.analysis.summary,
                predictions: Object.fromEntries(
                  Object.entries(sumData.analysis).filter(([key]) =>
                    key.startsWith("prediction_"),
                  ),
                ),
              });
            }
            // No 'else' needed, already reset above
          } catch (error) {
            console.error("Failed to fetch Sum Analysis:", error);
            // State already null
          }
        }

        // Fetch LSTM Analysis
        try {
          const lstmData = await fetchLSTMAnalysis(ticker);
          if (lstmData?.analysis) {
            setLSTMAnalysis({
              summary: lstmData.analysis.summary,
              predictions: Object.fromEntries(
                Object.entries(lstmData.analysis).filter(([key]) =>
                  key.startsWith("prediction_"),
                ),
              ),
            });
          }
          // No 'else' needed
        } catch (error) {
          console.error("Failed to fetch LSTM Analysis:", error);
          // State already null
        }
      }
      // No 'else' needed for ticker check, states reset at start
    };

    fetchAnalyses();
  }, [ticker, model]); // Dependencies: ticker and model

  // --- Label and Real Data Processing useEffect ---
  useEffect(() => {
    // Reset states before processing new props
    setLabels([]);
    setRealData([]);

    if (predictionData && predictionData.length > 0 && historicalData) {
      try {
        const earliestDate = getEarliestDate(predictionData);
        const latestDate = getLatestDate(predictionData);

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
        const stockChanges = convertStockPriceToPercentChange(stockPrices);
        setRealData(stockChanges);
      } catch (error) {
        console.error("Error processing historical/prediction data:", error);
        // States already reset
      }
    }
    // No 'else' needed, states reset at start
  }, [predictionData, historicalData]); // Dependencies: predictionData and historicalData

  // --- Color Logic (Memoized) ---
  const getColorForSource = useCallback(
    (source: string) => {
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
      const sources = predictionData
        ? Object.keys(
            predictionData.reduce(
              (acc, item) => {
                acc[item.source] = true;
                return acc;
              },
              {} as { [key: string]: boolean },
            ),
          )
        : [];
      const index = sources.indexOf(source);
      return colors[index % colors.length] || "rgb(100, 100, 100)";
    },
    [predictionData],
  );

  // --- Prediction Value Logic (Memoized) ---
  const getPredictionValue = useCallback(
    (analysis: AnalysisData | null, index: number): number | null => {
      const todayIndex = labels.indexOf(getCurrentDate()); // Find today's index within current labels

      if (
        !analysis ||
        todayIndex === -1 ||
        index < todayIndex ||
        !labels[index]
      ) {
        // No analysis, can't find today, index is in the past, or index out of bounds
        return null;
      }

      // Calculate days from today
      const dayNumber = index - todayIndex + 1;
      const predictionKey = `prediction_${dayNumber}_day`;

      const prediction = analysis.predictions[predictionKey];

      // Check if prediction exists and is a valid number before converting
      if (
        prediction !== undefined &&
        prediction !== null &&
        !isNaN(Number(prediction))
      ) {
        return convertToPercent([Number(prediction)])[0];
      }

      return null; // Return null if no valid prediction exists for this key
    },
    [labels], // Dependency: Recalculate if labels change
  );

  // --- Chart Data Calculation (Memoized) ---
  const chartData = useMemo(() => {
    return {
      labels: labels,
      datasets: [
        // Real Data
        {
          label: "Real Data",
          data: realData.length > 0 ? convertToPercent(realData) : [],
          borderColor: "rgb(255, 0, 0)",
          backgroundColor: "rgba(255, 0, 0, 0.2)", // Match border color with opacity
        },
        // Prediction Data by Source
        ...(predictionData
          ? predictionData.map((item) => {
              const color = getColorForSource(item.source);
              return {
                label: item.source,
                data: labels.map((label) => {
                  const predictionEntry = item.predictions[label];
                  // Ensure prediction exists and is numeric before converting
                  return predictionEntry?.prediction !== undefined &&
                    predictionEntry?.prediction !== null &&
                    !isNaN(Number(predictionEntry.prediction))
                    ? convertToPercent([Number(predictionEntry.prediction)])[0]
                    : null;
                }),
                borderColor: color,
                backgroundColor: color
                  .replace("rgb(", "rgba(")
                  .replace(")", ", 0.2)"),
              };
            })
          : []),
        // Summarized Analysis
        ...(sumAnalysis
          ? [
              {
                label: "Summarized Analysis",
                // Use the common getPredictionValue function
                data: labels.map((_, index) =>
                  getPredictionValue(sumAnalysis, index),
                ),
                borderColor: "rgb(0, 0, 255)",
                backgroundColor: "rgba(0, 0, 255, 0.2)",
                borderDash: [5, 5],
              },
            ]
          : []),
        // LSTM Analysis
        ...(LSTMAnalysis
          ? [
              {
                label: "LSTM Predictions",
                // Use the common getPredictionValue function
                data: labels.map((_, index) =>
                  getPredictionValue(LSTMAnalysis, index),
                ),
                borderColor: "rgb(7, 224, 0)",
                backgroundColor: "rgba(7, 224, 0, 0.2)", // Lighter green
                borderDash: [5, 5],
              },
            ]
          : []),
      ].filter((ds) => ds.data && ds.data.some((point) => point !== null)), // Filter out datasets with no valid data points
    };
  }, [
    labels,
    realData,
    predictionData,
    sumAnalysis,
    LSTMAnalysis,
    getColorForSource,
    getPredictionValue,
  ]); // Add getPredictionValue dependency

  // --- Chart Options Calculation (Memoized) ---
  const chartOptions: ChartOptions<"line"> = useMemo(() => {
    const todayIndex = labels.indexOf(getCurrentDate());
    const annotations: any = {}; // Use 'any' for annotations object or define specific type

    if (todayIndex !== -1) {
      annotations.verticalLine = {
        type: "line",
        xMin: todayIndex,
        xMax: todayIndex,
        borderColor: "red",
        borderWidth: 2,
        borderDash: [5, 5],
        label: {
          content: "Today",
          display: true,
          position: "start",
          backgroundColor: "rgba(255, 0, 0, 0.7)", // Make label clearer
          color: "white",
          font: {
            weight: "bold",
          },
        },
      };
    }

    return {
      responsive: true,
      maintainAspectRatio: false, // Allow chart to fill container height/width
      scales: {
        y: {
          title: {
            display: true,
            text: "Change [%]",
          },
          // beginAtZero: true, // Optionally force y-axis to start at 0
        },
        x: {
          title: {
            display: true,
            text: "Date",
          },
        },
      },
      plugins: {
        annotation: {
          annotations: annotations,
        },
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          enabled: true,
          mode: "index", // Show tooltips for all datasets at that index
          intersect: false, // Tooltip activates even if not directly hovering point
        },
        title: {
          display: true,
          text: `${ticker || "N/A"} - ${model || (LSTMAnalysis ? "LSTM" : "Analysis")} Predictions vs Actual`,
          font: {
            // Customize title font
            size: 16,
          },
        },
      },
      interaction: {
        // Fine-tune hover/interaction
        mode: "index",
        intersect: false,
      },
      // Performance optimizations (uncomment if needed for large data)
      // animation: false,
      // parsing: false, // We pre-parse data into the format chart.js expects
      // pointRadius: 2, // Smaller points for dense charts
    };
  }, [labels, ticker, model, LSTMAnalysis]); // Update if these change

  // --- Core Download Logic (Memoized) ---
  const triggerDownload = useCallback(() => {
    // Add robust checks here, though the calling useEffect should also check
    if (
      !ticker ||
      !predictionData ||
      !historicalData ||
      !labels.length ||
      !realData.length
    ) {
      console.warn("Attempted download trigger with incomplete core data.");
      return; // Prevent download if core data isn't truly ready
    }

    const dataToSave = {
      ticker: ticker,
      modelUsedForSumAnalysis: model || null, // Clarify which model SUM used
      savedAt: new Date().toISOString(),
      labels: labels,
      datasets: {
        // Use converted percent data directly as it's on the chart
        realPercentageChange:
          realData.length > 0 ? convertToPercent(realData) : [],
        // Include raw historical prices used for the calculation (optional)
        // historicalPricesFiltered: filterHistoricalData(historicalData, labels),
        predictionsBySource: predictionData.map((p) => ({
          source: p.source,
          predictionsPercent: Object.fromEntries(
            labels.map((label) => {
              const predictionEntry = p.predictions[label];
              const value =
                predictionEntry?.prediction !== undefined &&
                predictionEntry?.prediction !== null &&
                !isNaN(Number(predictionEntry.prediction))
                  ? convertToPercent([Number(predictionEntry.prediction)])[0]
                  : null;
              return [label, value];
            }),
          ),
        })),
        summarizedAnalysis: sumAnalysis
          ? {
              summary: sumAnalysis.summary,
              predictionsPercent: Object.fromEntries(
                labels
                  .map((_, index) => [
                    labels[index], // Use label as key
                    getPredictionValue(sumAnalysis, index), // Use the common function
                  ])
                  .filter(([_, value]) => value !== null), // Only save dates with actual predictions
              ),
            }
          : null,
        lstmAnalysis: LSTMAnalysis
          ? {
              summary: LSTMAnalysis.summary,
              predictionsPercent: Object.fromEntries(
                labels
                  .map((_, index) => [
                    labels[index], // Use label as key
                    getPredictionValue(LSTMAnalysis, index), // Use the common function
                  ])
                  .filter(([_, value]) => value !== null),
              ),
            }
          : null,
      },
    };

    try {
      const jsonString = JSON.stringify(dataToSave, null, 2);
      const blob = new Blob([jsonString], { type: "application/json" });
      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      // Filename: ticker-(model or LSTM)-timestamp.json
      const analysisType = model ? model : LSTMAnalysis ? "LSTM" : "Analysis";
      link.download = `${ticker}-${analysisType}-${timestamp}.json`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      console.log(
        `Data for ${ticker}-${analysisType} downloaded automatically.`,
      );
    } catch (error) {
      console.error("Error creating or saving JSON file automatically:", error);
      // Optionally alert the user, though automatic downloads might not warrant alerts
      // alert("Failed to automatically save data as JSON.");
    }
  }, [
    ticker,
    model,
    predictionData,
    historicalData,
    labels,
    realData,
    sumAnalysis,
    LSTMAnalysis,
    getPredictionValue,
  ]); // Ensure all dependencies used inside are listed

  // --- useEffect for Automatic Download ---
  useEffect(() => {
    // Define conditions for readiness more strictly
    const isBaseDataReady = !!(
      ticker &&
      predictionData &&
      historicalData &&
      labels.length > 0 &&
      realData.length > 0
    );

    // Determine if expected analyses have loaded (or determined not applicable)
    // Check if sumAnalysis is loaded OR if no model was provided (meaning it wasn't expected)
    const isSumAnalysisReady = !!sumAnalysis || !model;
    // Check if LSTMAnalysis is loaded OR if no ticker was provided (it shouldn't have been fetched) - Ticker check is part of isBaseDataReady
    const isLstmAnalysisReady = !!LSTMAnalysis || !ticker; // Simplified: if ticker exists, LSTM should load eventually if expected

    // We consider "fully loaded" when base data is ready AND required analyses are settled (either loaded or determined not applicable/failed)
    // Modify this logic based on whether you *require* analysis data for download
    const isFullyLoaded =
      isBaseDataReady && isSumAnalysisReady && isLstmAnalysisReady;

    // Log state for debugging
    // console.log(`Checking auto-download: isFullyLoaded=${isFullyLoaded}, hasDownloaded=${hasDownloadedForCurrentTicker}, ticker=${ticker}`);

    // Check if fully loaded AND download hasn't happened for this ticker/model yet
    if (isFullyLoaded && !hasDownloadedForCurrentTicker) {
      console.log(
        `Auto-download condition met for ${ticker}. Triggering download.`,
      );
      triggerDownload();
      setHasDownloadedForCurrentTicker(true); // Mark as downloaded for this set
    }
  }, [
    // Dependencies: trigger re-check when any of these change
    ticker,
    model, // Core inputs
    predictionData,
    historicalData, // Input props
    labels,
    realData, // Derived base data states
    sumAnalysis,
    LSTMAnalysis, // Derived analysis states
    hasDownloadedForCurrentTicker, // Download flag state
    triggerDownload, // Memoized download function
  ]);

  // --- Data Readiness Check for Display ---
  const isBaseChartDataReady = !!(
    predictionData &&
    historicalData &&
    labels.length > 0 &&
    realData.length > 0 &&
    ticker
  );

  return (
    <div
      style={{ padding: "10px", border: "1px solid #ccc", borderRadius: "5px" }}
    >
      {/* Chart Area */}
      <div
        className="combined-chart"
        style={{ minHeight: "300px", position: "relative" }}
      >
        {" "}
        {/* Ensure container has height */}
        {isBaseChartDataReady &&
        chartData.datasets &&
        chartData.datasets.length > 0 ? (
          <Line data={chartData} options={chartOptions} />
        ) : (
          <p style={{ textAlign: "center", paddingTop: "50px" }}>
            {ticker ? "Loading chart data..." : "Enter a ticker symbol."}
          </p>
        )}
      </div>

      {/* NO Download Button */}

      {/* Analysis Summaries Area */}
      <div style={{ marginTop: "20px" }}>
        {/* Display Sum Analysis if available */}
        {sumAnalysis ? (
          <div style={{ marginBottom: "15px" }}>
            <hr />
            <h3>Summarized Analysis ({model})</h3>
            <p>{sumAnalysis.summary || "No summary provided."}</p>
          </div>
        ) : // Show loading only if ticker and model were provided (meaning we expected it)
        ticker && model ? (
          <div>
            <hr />
            <p>Loading Summarized Analysis ({model})...</p>
          </div>
        ) : null}

        {/* Display LSTM Analysis if available */}
        {LSTMAnalysis ? (
          <div style={{ marginBottom: "15px" }}>
            <hr />
            <h3>LSTM Analysis</h3>
            <p>{LSTMAnalysis.summary || "No summary provided."}</p>
          </div>
        ) : // Show loading only if ticker was provided (meaning we expected it)
        ticker ? (
          <div>
            <hr />
            <p>Loading LSTM Analysis...</p>
          </div>
        ) : null}

        {/* Show message if no analysis was loaded/expected */}
        {!sumAnalysis && !LSTMAnalysis && ticker && (
          <div>
            <hr />
            <p>No analysis data available for {ticker}.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CombinedChart;
