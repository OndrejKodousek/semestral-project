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

export interface CombinedChartProps {
  data: PredictionData[] | null;
}

export interface HistoricalData {
  date: string;
  change: number;
}

export interface MetricsStats {
  average: string;
  min: string;
  max: string;
  median: string;
  variance: string;
  standardDeviation: string;
  iqr: string;
  confidenceIntervalRange: string;
  skewness: string;
  kurtosis: string;
}

export interface MetricsProps {
  data: PredictionData[] | null;
}

export interface ChartProps {
  published: string;
  ticker: string;
  predictions: {
    [key: string]: {
      prediction: number;
      confidence: number;
    };
  };
}

export interface ControlPanelProps {
  mode: number;
  setMode: (mode: number) => void;
  setMinArticles: (minArticles: number) => void;
  setIncludeConfidence: (includeConfidence: number) => void;
}

export interface ArticleListProps {
  data: PredictionData[] | null;
}

export interface StatisticsFieldProps {
  data: PredictionData[] | null;
  mode: number;
}

export interface ModelSelectProps {
  setModel: (model: string) => void;
}

export interface TickerSelectProps {
  setTicker: (ticker: string) => void;
  stockNames: string[];
}
