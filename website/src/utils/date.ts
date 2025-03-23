import { PredictionData } from "../utils/interfaces"; // Import the correct interface

const formatDate = (date: Date): string => {
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${year}-${month}-${day}`;
  //return `${day}-${month}`;
};

export const generateDateRange = (
  startDate: string,
  daysBeforeStart: number = 7,
  totalDays: number = 12, // Don't touch if possible, predictions are hardcoded to 12 days
): string[] => {
  const inputDate = new Date(startDate);

  const actualStartDate = new Date(inputDate);
  actualStartDate.setDate(inputDate.getDate() - daysBeforeStart);

  const dates: string[] = [];

  // Generate dates starting from the calculated start date
  for (let i = 0; i < totalDays; i++) {
    const currentDate = new Date(actualStartDate);
    currentDate.setDate(actualStartDate.getDate() + i);
    dates.push(formatDate(currentDate));
  }

  return dates;
};

export const generatePeriodDates = (
  startDate: string,
  endDate: string,
  extraDays: number,
): string[] => {
  const dates: string[] = [];
  const currentDate = new Date(startDate);
  const end = new Date(endDate);

  end.setDate(end.getDate() + extraDays);

  while (currentDate <= end) {
    dates.push(formatDate(currentDate));
    currentDate.setDate(currentDate.getDate() + 1);
  }

  return dates;
};

export const getCurrentDate = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0"); // Months are 0-indexed
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export const getDateOnly = (published: string): string => {
  const dateObj = new Date(published);

  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, "0"); // Months are zero-based
  const day = String(dateObj.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
};

export const calculateDateDifferenceInDays = (
  date1: string,
  date2: string,
): number => {
  // YYYY-MM-DD
  const date1Formatted = getDateOnly(date1);
  const date2Formatted = getDateOnly(date2);

  const d1 = new Date(date1Formatted);
  const d2 = new Date(date2Formatted);

  const timeDifference = d2.getTime() - d1.getTime();

  const dayDifference = Math.abs(timeDifference / (1000 * 60 * 60 * 24));

  return dayDifference;
};

export const getEarliestDate = (articles: PredictionData[]): string => {
  if (articles.length === 0) {
    return "0000-00-00";
    throw new Error("Articles array is empty");
  }

  const dates = articles.map((article) => new Date(article.published));

  const earliestDate = new Date(
    Math.min(...dates.map((date) => date.getTime())),
  );

  const year = earliestDate.getFullYear();
  const month = String(earliestDate.getMonth() + 1).padStart(2, "0");
  const day = String(earliestDate.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
};

export const getLatestDate = (articles: PredictionData[]): string => {
  if (articles.length === 0) {
    throw new Error("Articles array is empty");
  }

  const dates = articles.map((article) => new Date(article.published));

  const latestDate = new Date(Math.max(...dates.map((date) => date.getTime())));

  const year = latestDate.getFullYear();
  const month = String(latestDate.getMonth() + 1).padStart(2, "0");
  const day = String(latestDate.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};
