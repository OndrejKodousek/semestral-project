/**
 * @file date.ts
 * @brief Date utility functions
 * @details Provides various date manipulation and formatting functions
 * used throughout the application.
 */

import { PredictionData } from "../utils/interfaces";

/**
 * @brief Formats a Date object to YYYY-MM-DD string
 * @param date - Date object to format
 * @returns Formatted date string
 */
const formatDate = (date: Date): string => {
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${year}-${month}-${day}`;
};

/**
 * @brief Generates a date range around a start date
 * @param startDate - Base date for the range
 * @param daysBeforeStart - Number of days to include before start date
 * @param totalDays - Total number of days in the range
 * @returns Array of formatted date strings
 */
export const generateDateRange = (
  startDate: string,
  daysBeforeStart: number = 7,
  totalDays: number = 12,
): string[] => {
  const inputDate = new Date(startDate);
  const actualStartDate = new Date(inputDate);
  actualStartDate.setDate(inputDate.getDate() - daysBeforeStart);

  const dates: string[] = [];

  for (let i = 0; i < totalDays; i++) {
    const currentDate = new Date(actualStartDate);
    currentDate.setDate(actualStartDate.getDate() + i);
    dates.push(formatDate(currentDate));
  }

  return dates;
};

/**
 * @brief Generates dates between two dates with extra days
 * @param startDate - Range start date
 * @param endDate - Range end date
 * @param extraDays - Additional days to extend beyond end date
 * @returns Array of formatted date strings
 */
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

/**
 * @brief Gets current date in YYYY-MM-DD format
 * @returns Current date string
 */
export const getCurrentDate = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

/**
 * @brief Extracts date part from datetime string
 * @param published - Datetime string to parse
 * @returns Date string in YYYY-MM-DD format
 */
export const getDateOnly = (published: string): string => {
  const dateObj = new Date(published);

  const year = dateObj.getFullYear();
  const month = String(dateObj.getMonth() + 1).padStart(2, "0");
  const day = String(dateObj.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
};

/**
 * @brief Calculates difference between two dates in days
 * @param date1 - First date string
 * @param date2 - Second date string
 * @returns Absolute difference in days
 */
export const calculateDateDifferenceInDays = (
  date1: string,
  date2: string,
): number => {
  const date1Formatted = getDateOnly(date1);
  const date2Formatted = getDateOnly(date2);

  const d1 = new Date(date1Formatted);
  const d2 = new Date(date2Formatted);

  const timeDifference = d2.getTime() - d1.getTime();
  const dayDifference = Math.abs(timeDifference / (1000 * 60 * 60 * 24));

  return dayDifference;
};

/**
 * @brief Calculates signed difference between two dates in days
 * @param date1 - First date string
 * @param date2 - Second date string
 * @returns Signed difference in days (positive or negative)
 */
export const getDateDifferenceSigned = (
  date1: string,
  date2: string,
): number => {
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  const timeDifference = d2.getTime() - d1.getTime();
  return timeDifference / (1000 * 60 * 60 * 24);
};

/**
 * @brief Finds earliest date from array of prediction data
 * @param articles - Array of prediction data
 * @returns Earliest date string or default "0000-00-00" if empty
 */
export const getEarliestDate = (articles: PredictionData[]): string => {
  if (articles.length === 0) {
    return "0000-00-00";
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

/**
 * @brief Finds latest date from array of prediction data
 * @param articles - Array of prediction data
 * @returns Latest date string
 * @throws Error if input array is empty
 */
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
