## [https://www.kodousek.cz](https://www.kodousek.cz)

# Project Structure

## Scraper

Fetches RSS feed from Yahoo Finance, scrapes articles and saves them into database.

## Analyzer

Fetches saved articles from database, and passes them through various LLM models with various APIs, and saves the analyzed articles into the database.

## Website

React + Vite + Typescript website which shows user parsed analyzed data.

## Website backend

Website backend is simple FLASH server which handles all API endpoints.

## Daemon

Simple script which continuosly runs the scraper and then analyzer.

# Installation and usage

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt 
cd website
npm install
cd ..
```

Put your API keys to these files:

* data/API_KEY_GEMINI
* data/API_KEY_GROQ
* data/API_KEY_OPENROUTER

## Usage

You need to run 4 separate processes

### Daemon - Runs scraper and analyzer

```bash
python scripts/daemon.py
```

### LSTM Daemon - Trains LSTM models and creates predictions

```bash
python scripts/lstm_daemon.py
```

### API server

```bash
gunicorn --bind 0.0.0.0:500 website_backend/api_server:app
OR
python website-backend/api_server.py 
```

### Host website locally

```bash
cd website
npm run dev
```

If you want to host it on different PC on same network

```bash
cd website
npm run dev-host
```

### Build and publish website

Assumes you have NGINX webserver set up and ready to go

```bash
cd website
npm run build
npm run publish // Has fixed path
```

### Note

You theoretically don't need to run either of daemons aside of website's api server, since the database is included, but it will have old data and it might have undefined behaviour (some things rely on current day, for example, so there could be too large gap between current day and the data, so graphs might show no data).
