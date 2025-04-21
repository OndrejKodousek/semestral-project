import { HistoricalData } from "./interfaces";
import { calculateDateDifferenceInDays } from "./date";

export const parsePredictions = (predictions: any): number[] => {
  const output = [
    0, // Baseline
    predictions["1_day"]["prediction"],
    predictions["2_day"]["prediction"],
    predictions["3_day"]["prediction"],
    predictions["4_day"]["prediction"],
    predictions["5_day"]["prediction"],
    predictions["6_day"]["prediction"],
  ];
  return output;
};

export const convertToPercent = (array: number[]): number[] => {
  return array.map((value) => {
    if (Number.isNaN(value)) {
      return NaN;
    }
    return value * 100;
  });
};

export const alignHistoricalData = (
  data: HistoricalData[],
  published: string,
): (number | null)[] => {
  // How big is offset between start and first available real data point
  const offset = calculateDateDifferenceInDays(published, data[0]["date"]);

  const output: (number | null)[] = [];

  // Pad the beginning with null values
  for (let i = 0; i < offset; i++) {
    output.push(null);
  }

  for (let i = offset; i < data.length; i++) {
    output.push(data[i]["price"]);
  }

  return output;
};

export const formatStringToCSSClass = (input: string): string => {
  return input
    .toLowerCase() // Convert the string to lowercase
    .replace(/\s+/g, "-") // Replace spaces with a dash
    .replace(/\./g, "-") // Replace dots with a dash
    .replace(/\'/g, "");
};

export const extractTicker = (input: string): string | null => {
  const match = input.match(/^([A-Z0-9.]+)/);
  return match ? match[1] : null;
};

export const filterHistoricalData = (
  data: HistoricalData[],
  labels: string[],
): number[] => {
  const priceByDate = new Map<string, number>();

  data.forEach((item) => {
    priceByDate.set(item.date, item.price);
  });

  // NaN gets ignored in final graph, it just skips it entirely
  const result = labels.map((label) => {
    const price = priceByDate.get(label);
    return price !== undefined ? price : NaN;
  });

  return result;
};
export const convertStockPriceToPercentChange = (
  prices: number[],
): number[] => {
  const result: number[] = [];

  let baseline = 0;
  for (let i = 0; i < prices.length; i++) {
    if (!Number.isNaN(prices[i])) {
      baseline = prices[i];
      break;
    }
  }

  for (let i = 0; i < prices.length; i++) {
    if (Number.isNaN(prices[i])) {
      result.push(NaN);
    } else {
      const change = (prices[i] - baseline) / baseline;
      result.push(change);
    }
  }
  return result;
};
