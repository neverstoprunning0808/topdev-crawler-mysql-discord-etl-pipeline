# Job Market ETL Pipeline

An automated data engineering pipeline that collects job postings from TopDev (https://topdev.vn/en), transforms and stores the data in MySQL, and sends newly discovered jobs to a Discord server.

## Pipeline

```text
TopDev
   ↓
Extract Job Postings
   ↓
Transform & Normalize
   ↓
Filter New Jobs
   ↓         ↓
MySQL | Discord Server

```

The pipeline crawls job postings from TopDev and extracts structured job information from JSON-LD data.

Before loading, scraped jobs are compared with existing records in MySQL using the job URL. Only newly discovered jobs are inserted into the database.

The same list of new jobs is then sent to a Discord channel through a Discord Webhook.

## Features

- Crawl job postings from TopDev
- Extract structured JSON-LD job data
- Normalize job titles into job categories
- Extract salary, location, skills, experience, and employment type
- Filter and incrementally load only new jobs into MySQL
- Prevent duplicate jobs using job URLs
- Send newly inserted jobs to a Discord server
- Schedule automatic pipeline execution
- Logging and error handling

## Tech Stack

- Python
- Pandas
- BeautifulSoup
- Requests
- MySQL
- SQLAlchemy
- APScheduler
- Discord Webhooks
- Pytest

## Project Structure

```text
code/
├── etl/
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   ├── notify.py
│   └── pipeline.py
├── test/
├── logs/
└── analysis.ipynb
```

## Workflow

```python
df = extract_data()

df = transform_data(df)

new_jobs = load_data(df, engine)

send_discord_jobs(new_jobs)
```

`load_data()` compares the transformed jobs with existing records in MySQL and filters out previously processed jobs.

Only new jobs are:

1. Inserted into MySQL
2. Sent to the Discord server

This prevents duplicate records and avoids sending the same job notification multiple times.

## Data Collected

Each job record can include:

- Job title
- Company
- Posted date
- Expiration date
- Minimum and maximum salary
- Currency
- Skills
- City and locality
- Street address
- Job URL

## Run

From the project directory:

```bash
python -m etl.pipeline
```

The pipeline will:

```text
Crawl TopDev
      ↓
Transform Data
      ↓
Find New Jobs
      ↓
Insert New Jobs into MySQL
      ↓
Send New Jobs to Discord
```

## Environment Variables

Sensitive credentials such as the MySQL password and Discord Webhook URL should be stored in a `.env` file.

```env
DB_PASSWORD=your_password
DISCORD_WEBHOOK_URL=your_webhook_url
```
