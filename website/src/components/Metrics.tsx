import React, { useEffect, useState } from "react";
import { calculateMetrics } from "../utils/metricsCalculator";
import { MetricsProps, MetricsStats } from "../utils/interfaces";

const Metrics: React.FC<MetricsProps> = ({ data }) => {
  const [predictionMetrics, setPredictionMetrics] = useState<MetricsStats>({
    average: "N/A",
    min: "N/A",
    max: "N/A",
    median: "N/A",
    variance: "N/A",
    standardDeviation: "N/A",
    iqr: "N/A",
    confidenceIntervalRange: "N/A",
    skewness: "N/A",
    kurtosis: "N/A",
  });

  const [confidenceMetrics, setConfidenceMetrics] = useState<MetricsStats>({
    average: "N/A",
    min: "N/A",
    max: "N/A",
    median: "N/A",
    variance: "N/A",
    standardDeviation: "N/A",
    iqr: "N/A",
    confidenceIntervalRange: "N/A",
    skewness: "N/A",
    kurtosis: "N/A",
  });

  useEffect(() => {
    if (data) {
      const predictionValues = data
        .map((item) => item.predictions["1_day"].prediction)
        .filter((num) => !isNaN(num));
      const confidenceValues = data
        .map((item) => item.predictions["1_day"].confidence)
        .filter((num) => !isNaN(num));

      setPredictionMetrics(calculateMetrics(predictionValues));
      setConfidenceMetrics(calculateMetrics(confidenceValues));
    }
  }, [data]);

  return (
    <div className="scrollable-container mt-3">
      <div className="grid-table">
        <div className="grid-header">
          <div>Metric</div>
          <div>Prediction</div>
          <div>Confidence</div>
        </div>
        <div className="grid-body">
          <div className="grid-row">
            <div className="bold-text">Average</div>
            <div className="bold-text">{predictionMetrics.average}</div>
            <div className="bold-text">{confidenceMetrics.average}</div>
          </div>
          <div className="explanation-row">
            <div className="explanation-content">Arithmetic average.</div>
          </div>
          <div className="grid-row">
            <div className="bold-text">Minimum</div>
            <div className="bold-text">{predictionMetrics.min}</div>
            <div className="bold-text">{confidenceMetrics.min}</div>
          </div>
          <div className="explanation-row">
            <div className="explanation-content">Lowest value.</div>
          </div>
          <div className="grid-row">
            <div className="bold-text">Maximum</div>
            <div className="bold-text">{predictionMetrics.max}</div>
            <div className="bold-text">{confidenceMetrics.max}</div>
          </div>
          <div className="explanation-row">
            <div className="explanation-content">Highest value.</div>
          </div>
          <div className="grid-row">
            <div className="bold-text">Median</div>
            <div className="bold-text">{predictionMetrics.median}</div>
            <div className="bold-text">{confidenceMetrics.median}</div>
          </div>
          <div className="explanation-row">
            <div className="explanation-content">
              The middle value when the data is sorted
            </div>
          </div>
          <div className="grid-row">
            <div className="bold-text">Variance</div>
            <div className="bold-text">{predictionMetrics.variance}</div>
            <div className="bold-text">{confidenceMetrics.variance}</div>
          </div>
          <div className="explanation-row">
            <div className="explanation-content">
              The measure of data dispersion; average squared deviation from the
              mean.
            </div>
          </div>
          <div className="grid-row">
            <div className="bold-text">Standard Deviation</div>
            <div className="bold-text">
              {predictionMetrics.standardDeviation}
            </div>
            <div className="bold-text">
              {confidenceMetrics.standardDeviation}
            </div>
          </div>
          <div className="explanation-row">
            <div className="explanation-content">
              A measure of spread; the square root of variance.
            </div>
          </div>
          <div className="grid-row">
            <div className="bold-text">IQR</div>
            <div className="bold-text">{predictionMetrics.iqr}</div>
            <div className="bold-text">{confidenceMetrics.iqr}</div>
          </div>
          <div className="explanation-row">
            <div className="explanation-content">
              Interquartile Range (IQR); the range between the first and third
              quartile (Q3 - Q1).
            </div>
          </div>
          <div className="grid-row">
            <div className="bold-text">Confidence Interval Range</div>
            <div className="bold-text">
              {predictionMetrics.confidenceIntervalRange}
            </div>
            <div className="bold-text">
              {confidenceMetrics.confidenceIntervalRange}
            </div>
          </div>
          <div className="explanation-row">
            <div className="explanation-content">
              The range of the confidence interval, indicating uncertainty in
              the estimate.
            </div>
          </div>
          <div className="grid-row">
            <div className="bold-text">Skewness</div>
            <div className="bold-text">{predictionMetrics.skewness}</div>
            <div className="bold-text">{confidenceMetrics.skewness}</div>
          </div>
          <div className="explanation-row">
            <div className="explanation-content">
              A measure of asymmetry in the data distribution.
            </div>
          </div>
          <div className="grid-row">
            <div className="bold-text">Kurtosis</div>
            <div className="bold-text">{predictionMetrics.kurtosis}</div>
            <div className="bold-text">{confidenceMetrics.kurtosis}</div>
          </div>
          <div className="explanation-row">
            <div className="explanation-content">
              A measure of whether the data has heavy or light tails compared to
              a normal distribution.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Metrics;
