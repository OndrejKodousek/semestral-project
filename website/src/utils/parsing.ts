import { HistoricalData } from "./interfaces";
import { calculateDateDifferenceInDays } from "./date";

export const parsePredictions = (predictions: any): string[] => {
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

export const convertToPercent = (array: any[]): number[] => {
  return array.map((value) => {
    if (typeof value === "number" && !isNaN(value)) {
      return value * 100;
    }
    return NaN;
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
    output.push(data[i]["change"]);
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