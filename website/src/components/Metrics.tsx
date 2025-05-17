import React, { useEffect, useState } from "react";
import {
  calculateMetrics,
  formatCurrency,
  formatPercentage,
} from "../utils/metrics";
import {
  generatePeriodDates,
  getEarliestDate,
  getLatestDate,
} from "../utils/date";
import { filterHistoricalData } from "../utils/parsing";
import { fetchLSTMAnalysis } from "../utils/apiEndpoints";
import { MetricsProps } from "../utils/interfaces";

const Metrics: React.FC<MetricsProps> = ({
  predictionData,
  historicalData,
  ticker,
}) => {
  const [metrics, setMetrics] = useState<ReturnType<typeof calculateMetrics>>({
    realData: null,
    predictions: null,
    lstm: null,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDataAndCalculateMetrics = async () => {
      setLoading(true);

      try {
        // Convert from (date:number)[] to number[]
        const data = await fetchLSTMAnalysis(ticker);
        const lstmPredictions: number[] = Object.values(data);

        // Process historical data
        let realPrices: number[] = [];
        let allPredictions: number[] = [];

        if (predictionData?.length > 0 && historicalData?.length > 0) {
          const earliestDate = getEarliestDate(predictionData);
          const latestDate = getLatestDate(predictionData);

          if (earliestDate && latestDate) {
            const dates = generatePeriodDates(earliestDate, latestDate, 12);
            realPrices = filterHistoricalData(historicalData, dates);

            // Extract all predictions
            predictionData.forEach((item) => {
              dates.forEach((date) => {
                const pred = item.predictions[date]?.prediction;
                if (pred) allPredictions.push(pred);
              });
            });
          }
        }

        // Calculate metrics
        setMetrics(
          calculateMetrics(realPrices, allPredictions, lstmPredictions),
        );
      } catch (error) {
        console.error("Error calculating metrics:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDataAndCalculateMetrics();
  }, [ticker, predictionData, historicalData]);

  if (loading) {
    return <div>Loading metrics for {ticker}...</div>;
  }

  return (
    <div className="metrics-container">
      <h2>{ticker} Performance Metrics</h2>

      <div className="metrics-grid">
        {metrics.realData ? (
          <div className="metric-card">
            <h3>Real Stock Data</h3>
            <MetricItem
              label="Average Price"
              value={formatCurrency(metrics.realData.average)}
            />
            <MetricItem
              label="Minimum"
              value={formatCurrency(metrics.realData.min)}
            />
            <MetricItem
              label="Maximum"
              value={formatCurrency(metrics.realData.max)}
            />
            <MetricItem
              label="Range"
              value={formatCurrency(metrics.realData.range)}
            />
            <MetricItem
              label="Volatility"
              value={formatCurrency(metrics.realData.volatility)}
            />
            <MetricItem
              label="Data Points"
              value={metrics.realData.dataPoints.toString()}
            />
          </div>
        ) : (
          <div className="metric-card">
            <h3>Couldn't load historical data</h3>
          </div>
        )}

        {metrics.predictions ? (
          <div className="metric-card">
            <h3>Predictions</h3>
            <MetricItem
              label="Average"
              value={formatCurrency(metrics.predictions.average)}
            />
            <MetricItem
              label="Minimum"
              value={formatCurrency(metrics.predictions.min)}
            />
            <MetricItem
              label="Maximum"
              value={formatCurrency(metrics.predictions.max)}
            />
            <MetricItem
              label="Range"
              value={formatCurrency(metrics.predictions.range)}
            />
            <MetricItem
              label="Volatility"
              value={formatCurrency(metrics.predictions.volatility)}
            />
            <MetricItem
              label="Count"
              value={metrics.predictions.count.toString()}
            />
            {metrics.predictions.averageError && (
              <>
                <MetricItem
                  label="Avg Error"
                  value={formatCurrency(metrics.predictions.averageError)}
                />
                <MetricItem
                  label="Error %"
                  value={formatPercentage(metrics.predictions.errorPercentage!)}
                />
              </>
            )}
          </div>
        ) : (
          <div className="metric-card">
            <h3>Couldn't load predictions</h3>
          </div>
        )}

        {metrics.lstm ? (
          <div className="metric-card">
            <h3>LSTM Model</h3>
            <MetricItem
              label="Average"
              value={formatCurrency(metrics.lstm.average)}
            />
            <MetricItem label="Count" value={metrics.lstm.count.toString()} />
            {metrics.lstm.accuracy && (
              <MetricItem
                label="Accuracy"
                value={formatPercentage(metrics.lstm.accuracy)}
              />
            )}
          </div>
        ) : (
          <div className="metric-card">
            <h3>Couldn't load LSTM predictions</h3>
          </div>
        )}
      </div>
    </div>
  );
};

const MetricItem: React.FC<{ label: string; value: string }> = ({
  label,
  value,
}) => (
  <div className="metric-item">
    <span className="metric-label">{label}:</span>
    <span className="metric-value">{value}</span>
  </div>
);

export default Metrics;
