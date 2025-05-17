/**
 * @file ArticleList.tsx
 * @brief Component for displaying a list of articles with their charts
 * @details Renders a list of financial articles each with:
 * - Article metadata (source, title, summary)
 * - Associated stock prediction chart
 */

import React from "react";
import ArticleChart from "./ArticleChart";
import { ArticleListProps } from "../utils/interfaces";
import { formatStringToCSSClass } from "../utils/parsing";

/**
 * @brief Component that renders a list of articles with their prediction charts
 * @param predictionData - Array of article prediction data
 * @param historicalData - Array of historical stock prices
 * @param ticker - Stock ticker symbol
 */
const ArticleList: React.FC<ArticleListProps> = ({
  predictionData,
  historicalData,
  ticker,
}) => {
  return (
    <>
      {predictionData &&
        predictionData.length > 0 &&
        predictionData.map((item, index) => (
          <div
            className={`p-3 ${index !== 0 ? "mt-3" : ""} article`}
            key={index}
          >
            <div
              className={`backdrop-${formatStringToCSSClass(item.source)} row p-3`}
            >
              <div className="col-6">
                <div className="pb-3">
                  <a href={item.link}>
                    {item.source}: {item.title}
                  </a>
                </div>
                <div>{item.summary}</div>
              </div>
              <div className="col-6">
                <ArticleChart
                  predictions={item.predictions}
                  historicalData={historicalData}
                  published={item.published}
                  ticker={ticker}
                />
              </div>
            </div>
          </div>
        ))}
    </>
  );
};

export default ArticleList;
