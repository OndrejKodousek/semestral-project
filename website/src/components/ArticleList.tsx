import React from "react";
import ArticleChart from "./Chart";
import { ArticleListProps } from "../utils/interfaces";
import { formatStringToCSSClass } from "../utils/parsing";

const ArticleList: React.FC<ArticleListProps> = ({
  predictionData,
  historicalData,
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
                />
              </div>
            </div>
          </div>
        ))}
    </>
  );
};

export default ArticleList;
