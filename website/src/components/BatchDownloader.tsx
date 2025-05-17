/**
 * @file BatchDownloader.tsx
 * @brief Component for batch downloading stock prediction data
 * @details Handles downloading data for all ticker-model combinations
 * with progress tracking and error handling
 */

import React, { useState } from "react";
import { fetchStockNames } from "../utils/apiEndpoints";
import { extractTicker } from "../utils/parsing";
import { downloadTickerModelData } from "../utils/downloadUtils";
import { BatchDownloaderProps, Progress } from "../utils/interfaces";

/**
 * @brief Component for batch downloading stock prediction data
 * @param models - Array of model names to download data for
 * @param minArticles - Minimum number of articles required for a ticker to be included
 */
const BatchDownloader: React.FC<BatchDownloaderProps> = ({
  models,
  minArticles,
}) => {
  const [isDownloading, setIsDownloading] = useState<boolean>(false);
  const [progress, setProgress] = useState<Progress>({ current: 0, total: 0 });
  const [completed, setCompleted] = useState<string[]>([]);
  const [errorLog, setErrorLog] = useState<string[]>([]);
  const [currentModel, setCurrentModel] = useState<string>("");

  /**
   * @brief Initiates batch download process
   * @async
   */
  const downloadAll = async (): Promise<void> => {
    setIsDownloading(true);
    setCompleted([]);
    setErrorLog([]);

    try {
      for (const model of models) {
        setCurrentModel(model);
        try {
          const stockNames = await fetchStockNames(model, minArticles);
          const tickers = stockNames
            .map((name: string) => extractTicker(name))
            .filter((ticker: string): ticker is string => ticker !== null);

          setProgress({ current: 0, total: tickers.length });

          for (const ticker of tickers) {
            try {
              await downloadTickerModelData(ticker, model);

              setCompleted((prev) => [...prev, `${ticker}-${model}`]);
            } catch (error) {
              const errorMsg = `Failed to download ${ticker}-${model}: ${
                error instanceof Error ? error.message : String(error)
              }`;
              console.error(errorMsg);
              setErrorLog((prev) => [...prev, errorMsg]);
            } finally {
              setProgress((prev) => ({ ...prev, current: prev.current + 1 }));
            }
          }
        } catch (error) {
          const errorMsg = `Error processing model ${model}: ${
            error instanceof Error ? error.message : String(error)
          }`;
          console.error(errorMsg);
          setErrorLog((prev) => [...prev, errorMsg]);
        }
      }
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="batch-downloader p-3 border rounded">
      <h2 className="mb-3">Batch Data Download</h2>
      <h4>
        Downloads data for all combinations of model + ticker, with at least{" "}
        {minArticles} articles
      </h4>
      {isDownloading && (
        <h4>Currently downloading data from model {currentModel}</h4>
      )}

      <button
        onClick={downloadAll}
        disabled={isDownloading}
        className="btn btn-primary mb-3"
      >
        {isDownloading ? "Downloading..." : "Download All Data"}
      </button>

      {isDownloading && (
        <div className="progress-container mb-3">
          <div className="progress">
            <div
              className="progress-bar progress-bar-striped progress-bar-animated"
              role="progressbar"
              style={{
                width: `${Math.round(
                  (progress.current / progress.total) * 100,
                )}%`,
              }}
              aria-valuenow={progress.current}
              aria-valuemin={0}
              aria-valuemax={progress.total}
            >
              {progress.current} / {progress.total}
            </div>
          </div>
          <p className="mt-1 text-muted">
            Processing:{" "}
            {progress.current > 0
              ? completed[completed.length - 1]
              : "Starting..."}
          </p>
        </div>
      )}

      {completed.length > 0 && (
        <div className="completed-downloads mb-3">
          <h5>Completed Downloads ({completed.length}):</h5>
          <div
            className="border rounded p-2"
            style={{ maxHeight: "400px", overflowY: "auto" }}
          >
            {completed.map((item, index) => (
              <div key={index} className="text-success">
                ✓ {item}
              </div>
            ))}
          </div>
        </div>
      )}

      {errorLog.length > 0 && (
        <div className="error-log">
          <h5>Errors ({errorLog.length}):</h5>
          <div
            className="border rounded p-2"
            style={{ maxHeight: "200px", overflowY: "auto" }}
          >
            {errorLog.map((error, index) => (
              <div key={index} className="text-danger">
                ✗ {error}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BatchDownloader;
