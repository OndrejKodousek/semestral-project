export const calculateMedian = (sortedValues: number[]): number => {
  const mid = Math.floor(sortedValues.length / 2);
  return sortedValues.length % 2 !== 0
    ? sortedValues[mid]
    : (sortedValues[mid - 1] + sortedValues[mid]) / 2;
};

export const calculateVariance = (values: number[], mean: number): number => {
  return (
    values.reduce((sum, value) => sum + Math.pow(value - mean, 2), 0) /
    values.length
  );
};

export const calculateIQR = (sortedValues: number[]): number => {
  const q1 = calculateMedian(
    sortedValues.slice(0, Math.floor(sortedValues.length / 2)),
  );
  const q3 = calculateMedian(
    sortedValues.slice(Math.ceil(sortedValues.length / 2)),
  );
  return q3 - q1;
};

export const calculateConfidenceIntervalRange = (
  values: number[],
  standardDeviation: number,
): number => {
  const zScore = 1.96; // For 95% confidence interval
  return zScore * (standardDeviation / Math.sqrt(values.length));
};

export const calculateSkewness = (
  values: number[],
  mean: number,
  standardDeviation: number,
): number => {
  const n = values.length;
  return (
    (values.reduce(
      (sum, value) => sum + Math.pow((value - mean) / standardDeviation, 3),
      0,
    ) *
      n) /
    ((n - 1) * (n - 2))
  );
};

export const calculateKurtosis = (
  values: number[],
  mean: number,
  standardDeviation: number,
): number => {
  const n = values.length;
  return (
    (values.reduce(
      (sum, value) => sum + Math.pow((value - mean) / standardDeviation, 4),
      0,
    ) *
      (n * (n + 1))) /
      ((n - 1) * (n - 2) * (n - 3)) -
    (3 * Math.pow(n - 1, 2)) / ((n - 2) * (n - 3))
  );
};

export const calculateMetrics = (
  values: number[],
): {
  average: string;
  min: string;
  max: string;
  median: string;
  variance: string;
  standardDeviation: string;
  iqr: string;
  confidenceIntervalRange: string;
  skewness: string;
  kurtosis: string;
} => {
  if (values.length === 0) {
    return {
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
    };
  }

  const sortedValues = values.slice().sort((a, b) => a - b);
  const average = values.reduce((sum, value) => sum + value, 0) / values.length;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const median = calculateMedian(sortedValues);
  const variance = calculateVariance(values, average);
  const standardDeviation = Math.sqrt(variance);
  const iqr = calculateIQR(sortedValues);
  const confidenceIntervalRange = calculateConfidenceIntervalRange(
    values,
    standardDeviation,
  );
  const skewness = calculateSkewness(values, average, standardDeviation);
  const kurtosis = calculateKurtosis(values, average, standardDeviation);

  const formatValue = (value: number, isPercentage: boolean = true): string => {
    const formattedValue = (value * (isPercentage ? 100 : 1)).toFixed(3);
    return isPercentage ? `${formattedValue}%` : formattedValue;
  };

  return {
    average: formatValue(average),
    min: formatValue(min),
    max: formatValue(max),
    median: formatValue(median),
    variance: formatValue(variance, false),
    standardDeviation: formatValue(standardDeviation, false),
    iqr: formatValue(iqr),
    confidenceIntervalRange: formatValue(confidenceIntervalRange),
    skewness: formatValue(skewness, false),
    kurtosis: formatValue(kurtosis, false),
  };
};
