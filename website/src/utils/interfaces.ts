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
  predictionData: PredictionData[];
  historicalData: HistoricalData[];
  ticker: string;
  model: string;
}

export interface HistoricalData {
  date: string;
  price: number;
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
  predictions: {
    [key: string]: {
      prediction: number;
      confidence: number;
    };
  };
  historicalData: HistoricalData[];
  published: string;
}

export interface ControlPanelProps {
  mode: number;
  setMode: (mode: number) => void;
  setMinArticles: (minArticles: number) => void;
  setIncludeConfidence: (includeConfidence: number) => void;
}

export interface ArticleListProps {
  predictionData: PredictionData[] | null;
  historicalData: HistoricalData[];
}

export interface StatisticsFieldProps {
  predictionData: PredictionData[];
  ticker: string;
  model: string;
  mode: number;
}

export interface ModelSelectProps {
  setModel: (model: string) => void;
}

export interface TickerSelectProps {
  setTicker: (ticker: string) => void;
  stockNames: string[];
}
