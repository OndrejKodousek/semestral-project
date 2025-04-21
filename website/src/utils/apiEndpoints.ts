import { getDateOnly } from "../utils/date";

const apiBaseUrl = (() => {
  const hostname = window.location.hostname;

  if (hostname === "localhost") {
    return "http://localhost:5000";
  } else if (hostname === "192.168.1.110") {
    return "http://192.168.1.110:5000";
  } else {
    return "https://kodousek.cz";
  }
})();

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
