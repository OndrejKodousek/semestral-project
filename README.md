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

## Usage

You need to run 3 separate processes

### Daemon

```bash
python scripts/daemon.py
```

### API server

```bash
gunicorn --bind 0.0.0.0:500 website_backend/api_server:app
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

Assumes you have NGINX webserver setup up and ready to go

```bash
cd website
npm run build
npm run publish
```
