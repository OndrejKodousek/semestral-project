import React from "react";
import ArticleList from "./ArticleList";
import CombinedChart from "./CombinedChart";
import { StatisticsFieldProps } from "../utils/interfaces";

const StatisticsField: React.FC<StatisticsFieldProps> = ({ data, mode }) => {
  return (
    <div className="inset-container p-3">
      <div className="col-lg-12 col-md-12">
        {mode === 1 && <ArticleList data={data} />}
        {mode === 2 && <CombinedChart data={data} />}
      </div>
    </div>
  );
};

export default StatisticsField;
