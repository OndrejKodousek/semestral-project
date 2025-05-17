# News Analyzer Project Documentation

## Overview

This project is a comprehensive system for scraping, analyzing, and evaluating news content. It consists of several components:

1. **Scraper**: Collects news articles from various sources
2. **Analyzer**: Processes and analyzes the collected news
3. **LSTM**: Machine learning component for predictions
4. **Evaluator**: Evaluates the system's performance
5. **Website**: Frontend interface
6. **Website Backend**: API server for the frontend

## Components

### Scraper

Located in `scraper/`, this component collects news articles.

### Analyzer

Located in `analyzer/`, this component processes news articles using various LLM providers.

### LSTM

Located in `lstm/`, this contains machine learning models for news analysis.

### Evaluator

Located in `evaluator/`, this evaluates system performance.

### Website

The frontend is built with React and TypeScript, featuring these key components:

\dot
digraph architecture {
node [shape=box];
App -> {TickerSelect, ModelSelect, ControlPanel, StatisticsField}
StatisticsField -> {ArticleList, CombinedChart, Metrics, BatchDownloader}
ArticleList -> ArticleChart
}
\enddot

## Key Features

- Real-time stock prediction visualization
- Multiple model comparison
- Batch data downloading
- Performance metrics

### Website Backend

Located in `website-backend/`, this provides API endpoints for the frontend.

\section backend_links Backend Services

- [Analysis API](@ref apiEndpoints.ts)
- [Data Models](@ref interfaces.ts)

\section frontend_links Frontend Components

- [Main Application](@ref App.tsx)
- [Chart Components](@ref ArticleChart.tsx)


## Getting Started

See the individual component documentation for details on each part of the system.
