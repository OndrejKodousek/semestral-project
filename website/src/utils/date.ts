import { PredictionData } from "../utils/interfaces"; // Import the correct interface

const formatDate = (date: Date): string => {
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return `${day}-${month}`;
  //const year = date.getFullYear();
  //return `${day}-${month}-${year}`;
};

export const generateWeekDates = (startDate: string): string[] => {
  const date = new Date(startDate);
  const weekDates = [formatDate(date)];
  for (let i = 1; i < 7; i++) {
    const nextDate = new Date(date);
    nextDate.setDate(date.getDate() + i);
    weekDates.push(formatDate(nextDate));
  }

  return weekDates;
};

export const getCurrentDate = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0"); // Months are 0-indexed
  const day = String(today.getDate()).padStart(2, "0");
  return `${day}-${month}`;
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

export const getEarliestPublishedDate = (
  articles: PredictionData[],
): string => {
  if (articles.length === 0) {
    throw new Error("Articles array is empty");
  }

  const publishedDates = articles.map((article) => new Date(article.published));

  const earliestDate = new Date(
    Math.min(...publishedDates.map((date) => date.getTime())),
  );

  const year = earliestDate.getFullYear();
  const month = String(earliestDate.getMonth() + 1).padStart(2, "0");
  const day = String(earliestDate.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
};
