/**
 * @file apiEndpoints.ts
 * @brief API service module for all backend communication
 * @details Handles all HTTP requests to the backend API with proper
 * error handling. Automatically detects environment to set correct
 * API base URL.
 */

import { getDateOnly } from "../utils/date";

/**
 * @brief Determines the base API URL based on current hostname
 * @returns Base URL string for API requests
 */
const apiBaseUrl = (() => {
  const hostname = window.location.hostname;

  if (hostname === "localhost") {
    return "http://localhost:5000";
  } else if (hostname === "192.168.1.101") {
    return "http://192.168.1.101:5000";
  } else {
    return "https://kodousek.cz";
  }
})();

/**
 * @brief Fetches historical stock price data
 * @param ticker - Stock ticker symbol
 * @param start - Start date for historical data
 * @returns Promise resolving to historical data array
 */
export const fetchHistoricalData = async (ticker: string, start: string) => {
  try {
    const response = await fetch(
      `${apiBaseUrl}/api/historical-data?ticker=${ticker}&start=${getDateOnly(start)}`,
    );

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const jsonData = await response.json();
    return jsonData;
  } catch (error) {
    console.error("Error fetching historical data:", error);
    return [];
  }
};

/**
 * @brief Fetches prediction analysis data
 * @param ticker - Stock ticker symbol
 * @param model - AI model name
 * @returns Promise resolving to analysis data
 */
export const fetchAnalysisData = async (ticker: string, model: string) => {
  try {
    const response = await fetch(
      `${apiBaseUrl}/api/analysis?ticker=${ticker}&model=${model}`,
    );
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching analysis data:", error);
    return null;
  }
};

/**
 * @brief Fetches list of available stock tickers for a model
 * @param model - AI model name
 * @param minArticles - Minimum articles filter
 * @returns Promise resolving to array of stock names
 */
export const fetchStockNames = async (model: string, minArticles: number) => {
  try {
    const response = await fetch(
      `${apiBaseUrl}/api/stocks?model=${model}&min_articles=${minArticles}`,
    );
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching stock names:", error);
    return [];
  }
};

/**
 * @brief Fetches summarized analysis data
 * @param ticker - Stock ticker symbol
 * @param model - AI model name
 * @returns Promise resolving to summarized analysis
 */
export const fetchSumAnalysis = async (ticker: string, model: string) => {
  try {
    const response = await fetch(
      `${apiBaseUrl}/api/sum_analysis?model=${model}&ticker=${ticker}`,
    );
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching summarized analysis:", error);
    return null;
  }
};

/**
 * @brief Fetches LSTM model predictions
 * @param ticker - Stock ticker symbol
 * @returns Promise resolving to LSTM predictions
 */
export const fetchLSTMAnalysis = async (ticker: string) => {
  try {
    const response = await fetch(
      `${apiBaseUrl}/api/fetch_lstm?ticker=${ticker}`,
    );
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching LSTM predictions analysis:", error);
    return null;
  }
};
