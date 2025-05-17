/**
 * @file interfaces.ts
 * @brief Type definitions for the application
 * @details Contains all interface definitions used throughout the application
 * for type safety and documentation purposes.
 */

/**
 * @interface PredictionData
 * @brief Represents prediction data from a single article
 * @property title - Article title
 * @property source - News source name
 * @property link - URL to original article
 * @property ticker - Stock ticker symbol
 * @property summary - AI-generated summary of the article
 * @property published - Publication date
 * @property predictions - Object containing prediction data by date
 */
export interface PredictionData {
  title: string;
  source: string;
  link: string;
  ticker: string;
  summary: string;
  published: string;
  predictions: {
    [key: string]: {
      prediction: number;
      confidence: number;
    };
  };
}

/**
 * @interface CombinedChartProps
 * @brief Props for CombinedChart component
 * @property predictionData - Array of prediction data
 * @property historicalData - Array of historical stock prices
 * @property ticker - Stock ticker symbol
 * @property model - AI model name
 */
export interface CombinedChartProps {
  predictionData: PredictionData[];
  historicalData: HistoricalData[];
  ticker: string;
  model: string;
}

/**
 * @interface HistoricalData
 * @brief Represents historical stock price data
 * @property date - Date string (YYYY-MM-DD)
 * @property price - Stock price at given date
 */
export interface HistoricalData {
  date: string;
  price: number;
}

/**
 * @interface ChartProps
 * @brief Props for ArticleChart component
 * @property predictions - Prediction data by date
 * @property historicalData - Array of historical stock prices
 * @property published - Article publication date
 * @property ticker - Stock ticker symbol
 */
export interface ChartProps {
  predictions: {
    [key: string]: {
      prediction: number;
      confidence: number;
    };
  };
  historicalData: HistoricalData[];
  published: string;
  ticker: string;
}

/**
 * @interface ControlPanelProps
 * @brief Props for ControlPanel component
 * @property mode - Current view mode
 * @property setMode - Function to update view mode
 * @property setMinArticles - Function to update minimum articles filter
 * @property setIncludeConfidence - Function to toggle confidence display
 */
export interface ControlPanelProps {
  mode: number;
  setMode: (mode: number) => void;
  setMinArticles: (minArticles: number) => void;
  setIncludeConfidence: (includeConfidence: number) => void;
}

/**
 * @interface ArticleListProps
 * @brief Props for ArticleList component
 * @property predictionData - Array of prediction data or null
 * @property historicalData - Array of historical stock prices
 * @property ticker - Stock ticker symbol
 */
export interface ArticleListProps {
  predictionData: PredictionData[] | null;
  historicalData: HistoricalData[];
  ticker: string;
}

/**
 * @interface StatisticsFieldProps
 * @brief Props for StatisticsField component
 * @property predictionData - Array of prediction data
 * @property ticker - Stock ticker symbol
 * @property model - AI model name
 * @property mode - Current view mode
 * @property minArticles - Minimum articles filter value
 */
export interface StatisticsFieldProps {
  predictionData: PredictionData[];
  ticker: string;
  model: string;
  mode: number;
  minArticles: number;
}

/**
 * @interface ModelSelectProps
 * @brief Props for ModelSelect component
 * @property setModel - Function to update selected model
 */
export interface ModelSelectProps {
  setModel: (model: string) => void;
}

/**
 * @interface TickerSelectProps
 * @brief Props for TickerSelect component
 * @property setTicker - Function to update selected ticker
 * @property stockNames - Array of available stock names
 */
export interface TickerSelectProps {
  setTicker: (ticker: string) => void;
  stockNames: string[];
}

/**
 * @interface MetricsProps
 * @brief Props for Metrics component
 * @property predictionData - Array of prediction data
 * @property historicalData - Array of historical stock prices
 * @property ticker - Stock ticker symbol
 */
export interface MetricsProps {
  predictionData: PredictionData[];
  historicalData: HistoricalData[];
  ticker: string;
}

/**
 * @interface BatchDownloaderProps
 * @brief Props for BatchDownloader component
 * @property models - Array of model names to download
 * @property minArticles - Minimum articles filter value
 */
export interface BatchDownloaderProps {
  models: string[];
  minArticles: number;
}

/**
 * @interface Progress
 * @brief Represents download progress
 * @property current - Current progress count
 * @property total - Total items to process
 */
export interface Progress {
  current: number;
  total: number;
}
