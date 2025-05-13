export interface StockMetrics {
  realData: {
    average: number;
    min: number;
    max: number;
    range: number;
    volatility: number;
    dataPoints: number;
  } | null;
  predictions: {
    average: number;
    min: number;
    max: number;
    range: number;
    volatility: number;
    count: number;
    averageError?: number;
    errorPercentage?: number;
  } | null;
  lstm: {
    average: number;
    count: number;
    accuracy?: number;
  } | null;
}

export const calculateMetrics = (
  realPrices: number[],
  allPredictions: number[],
  lstmPredictions: number[] | null,
): StockMetrics => {
  const metrics: StockMetrics = {
    realData: null,
    predictions: null,
    lstm: null,
  };

  // Calculate real data metrics
  if (realPrices.length > 0) {
    const validRealPrices = realPrices.filter(
      (price) => price !== null && !isNaN(price),
    );
    if (validRealPrices.length > 0) {
      const average =
        validRealPrices.reduce((sum, price) => sum + price, 0) /
        validRealPrices.length;
      const min = Math.min(...validRealPrices);
      const max = Math.max(...validRealPrices);

      metrics.realData = {
        average,
        min,
        max,
        range: max - min,
        volatility: calculateVolatility(validRealPrices),
        dataPoints: validRealPrices.length,
      };
    }
  }

  // Calculate prediction metrics
  if (allPredictions.length > 0) {
    const validPredictions = allPredictions.filter(
      (p) => p !== null && !isNaN(p),
    );
    if (validPredictions.length > 0) {
      const average =
        validPredictions.reduce((sum, p) => sum + p, 0) /
        validPredictions.length;
      const min = Math.min(...validPredictions);
      const max = Math.max(...validPredictions);

      const predictionMetrics: NonNullable<StockMetrics["predictions"]> = {
        average,
        min,
        max,
        range: max - min,
        volatility: calculateVolatility(validPredictions),
        count: validPredictions.length,
      };

      // Calculate error if real data exists
      if (metrics.realData) {
        predictionMetrics.averageError = Math.abs(
          metrics.realData.average - average,
        );
        predictionMetrics.errorPercentage =
          (predictionMetrics.averageError / metrics.realData.average) * 100;
      }

      metrics.predictions = predictionMetrics;
    }
  }

  // Calculate LSTM metrics
  if (lstmPredictions && lstmPredictions.length > 0) {
    const validLSTMPredictions = lstmPredictions.filter(
      (p) => p !== null && !isNaN(p),
    );
    if (validLSTMPredictions.length > 0) {
      const average =
        validLSTMPredictions.reduce((sum, p) => sum + p, 0) /
        validLSTMPredictions.length;

      const lstmMetrics: NonNullable<StockMetrics["lstm"]> = {
        average,
        count: validLSTMPredictions.length,
      };

      // Calculate accuracy if real data exists
      if (metrics.realData) {
        lstmMetrics.accuracy =
          (1 -
            Math.abs(average - metrics.realData.average) /
              metrics.realData.average) *
          100;
      }

      metrics.lstm = lstmMetrics;
    }
  }

  return metrics;
};

const calculateVolatility = (values: number[]): number => {
  const avg = values.reduce((a, b) => a + b, 0) / values.length;
  const variance =
    values.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / values.length;
  return Math.sqrt(variance);
};

export const formatCurrency = (value: number): string => {
  return `$${value.toFixed(2)}`;
};

export const formatPercentage = (value: number): string => {
  return `${value.toFixed(2)}%`;
};
