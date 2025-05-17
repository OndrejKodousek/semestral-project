/**
 * @file parsing.ts
 * @brief Data parsing and transformation utilities
 * @details Provides various functions for processing and converting
 * stock prediction data between different formats.
 */

import { HistoricalData } from "./interfaces";
import { calculateDateDifferenceInDays } from "./date";

/**
 * @brief Parses raw prediction data into array format
 * @param predictions - Raw prediction data object
 * @returns Array of parsed prediction values
 */
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

/**
 * @brief Converts array of decimal values to percentages
 * @param array - Array of decimal values (0-1)
 * @returns Array of percentage values (0-100)
 */
export const convertToPercent = (array: number[]): number[] => {
  return array.map((value) => {
    if (Number.isNaN(value)) {
      return NaN;
    }
    return value * 100;
  });
};

/**
 * @brief Aligns historical data with prediction dates
 * @param data - Array of historical stock prices
 * @param published - Article publication date
 * @returns Array aligned with prediction dates (null for missing data)
 */
export const alignHistoricalData = (
  data: HistoricalData[],
  published: string,
): (number | null)[] => {
  // Calculate offset between start and first available data point
  const offset = calculateDateDifferenceInDays(published, data[0]["date"]);

  const output: (number | null)[] = [];

  // Pad the beginning with null values
  for (let i = 0; i < offset; i++) {
    output.push(null);
  }

  // Add actual data points
  for (let i = offset; i < data.length; i++) {
    output.push(data[i]["price"]);
  }

  return output;
};

/**
 * @brief Converts string to CSS-friendly class name
 * @param input - Original string
 * @returns Sanitized string suitable for CSS classes
 */
export const formatStringToCSSClass = (input: string): string => {
  return input
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/\./g, "-")
    .replace(/\'/g, "");
};

/**
 * @brief Extracts ticker symbol from stock name string
 * @param input - Stock name string (e.g., "AAPL - Apple Inc")
 * @returns Ticker symbol or null if not found
 */
export const extractTicker = (input: string): string | null => {
  const match = input.match(/^([A-Z0-9.]+)/);
  return match ? match[1] : null;
};

/**
 * @brief Filters historical data to match specific dates
 * @param data - Array of historical stock prices
 * @param labels - Array of date strings to filter by
 * @returns Array of prices corresponding to the labels
 */
export const filterHistoricalData = (
  data: HistoricalData[],
  labels: string[],
): number[] => {
  const priceByDate = new Map<string, number>();

  // Create map of date to price
  data.forEach((item) => {
    priceByDate.set(item.date, item.price);
  });

  // Return array with prices for each label (NaN if missing)
  const result = labels.map((label) => {
    const price = priceByDate.get(label);
    return price !== undefined ? price : NaN;
  });

  return result;
};

/**
 * @brief Converts stock prices to percentage changes
 * @param prices - Array of stock prices
 * @returns Array of percentage changes from baseline
 */
export const convertStockPriceToPercentChange = (
  prices: number[],
): number[] => {
  const result: number[] = [];

  // Find first valid price as baseline
  let baseline = 0;
  for (let i = 0; i < prices.length; i++) {
    if (!Number.isNaN(prices[i])) {
      baseline = prices[i];
      break;
    }
  }

  // Calculate percentage change for each price
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
