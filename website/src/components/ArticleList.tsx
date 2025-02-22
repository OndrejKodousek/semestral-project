import React from "react";
import Chart from "./Chart";
import { ArticleListProps } from "../utils/interfaces";

const formatString = (input: string): string => {
  return input
    .toLowerCase() // Convert the string to lowercase
    .replace(/\s+/g, "-") // Replace spaces with a dash
    .replace(/\./g, "-") // Replace dots with a dash
    .replace(/\'/g, "");
};

const ArticleList: React.FC<ArticleListProps> = ({ data }) => {
  return (
    <div className="">
      {data && data.length > 0 ? (
        data.map((item, index) => (
          <div
            key={index}
            className={`article-row p-3 my-3 backdrop-${formatString(item.source)}`}
          >
            <div className="row">
              <div className="col-6 col-md-6">
                <div className="article-title">
                  <a href={item.link}>{item.title}</a>
                </div>
                <div className="article-body">{item.summary}</div>
              </div>
              <div className="col-6 col-md-6">
                <Chart
                  predictions={item.predictions}
                  published={item.published}
                  ticker={item.ticker}
                />
              </div>
            </div>
          </div>
        ))
      ) : (
        <div className="col-12 h-100">
          <div>No data available</div>
        </div>
      )}
    </div>
  );
};

export default ArticleList;
