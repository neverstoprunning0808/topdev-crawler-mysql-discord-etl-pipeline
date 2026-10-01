# import pandas as pd
# from pathlib import Path


# def extract_data(file_path):
#     file_path = Path(file_path)

#     try:
#         df = pd.read_csv(file_path)

#         if df.empty:
#             raise ValueError("CSV file is empty")

#         print(f"Extracted {len(df)} rows successfully!")

#         return df

#     except FileNotFoundError:
#         raise FileNotFoundError(f"CSV file cannot be found: {file_path}")

#     except pd.errors.EmptyDataError:
#         raise ValueError(f"CSV file contains no data: {file_path}")

#     except Exception as e:
#         raise RuntimeError(f"Extract failed: {e}")


# =========================================================================================================
# =========================================================================================================

import json
import time 
import requests
import numpy as np
import pandas as pd

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, urlunsplit

# =========================================================
# CONFIG
# =========================================================

BASE_URL = "https://topdev.vn"
SEARCH_URL = "https://topdev.vn/viec-lam/tim-kiem"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    )
}

# =========================================================
# CLEAN URL
# =========================================================

def clean_job_url(url):
    """
    Remove tracking/query parameters from a TopDev job URL.

    Example:
    .../job-123?src=topdev_home&medium=superhotjobs
    ->
    .../job-123
    """

    parts = urlsplit(url)

    return urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path,
        "",
        ""
    ))
    
    
# =========================================================
# GET JOB LINKS
# =========================================================

def get_job_links(num_pages=5):
    """
    Crawl TopDev search pages and collect unique job URLs.
    """

    job_links = []

    for page in range(1, num_pages + 1):

        url = f"{SEARCH_URL}?page={page}"

        response = requests.get(url, headers=HEADERS, timeout=15)

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        page_links = []

        for a in soup.find_all("a", href=True):

            href = urljoin(
                BASE_URL,
                a["href"]
            )

            # Job detail pages
            if ("/viec-lam/" in href and "/tim-kiem" not in href):
                href = clean_job_url(href)
                page_links.append(href)

        # Remove duplicates within current page
        page_links = list(set(page_links))

        print(f"Page {page}: {len(page_links)} jobs")

        job_links.extend(page_links)

    # Remove duplicates across pages
    job_links = list(set(job_links))

    print(f"\nTotal unique jobs: {len(job_links)}")

    return job_links


# =========================================================
# PARSE SALARY
# =========================================================

def parse_salary_json(job_data):
    """
    Extract min salary, max salary and currency
    from JobPosting JSON-LD.
    """

    salary = job_data.get("baseSalary")

    if not isinstance(salary, dict):
        return np.nan, np.nan, None

    currency = salary.get("currency")

    value = salary.get("value", {})

    if not isinstance(value, dict):
        return np.nan, np.nan, currency

    min_salary = value.get("minValue")
    max_salary = value.get("maxValue")

    try:
        min_salary = (
            float(min_salary)
            if min_salary is not None
            else np.nan
        )
    except (ValueError, TypeError):
        min_salary = np.nan

    try:
        max_salary = (
            float(max_salary)
            if max_salary is not None
            else np.nan
        )
    except (ValueError, TypeError):
        max_salary = np.nan

    return (
        min_salary,
        max_salary,
        currency
    )


# =========================================================
# PARSE LOCATION
# =========================================================

def parse_location_json(job_data):
    """
    Extract structured location information
    from JobPosting JSON-LD.
    """

    location = job_data.get(
        "jobLocation",
        {}
    )

    if not isinstance(location, dict):
        return None, None, None

    address = location.get(
        "address",
        {}
    )

    if not isinstance(address, dict):
        return None, None, None

    city = address.get(
        "addressRegion"
    )

    district = address.get(
        "addressLocality"
    )

    street_address = address.get(
        "streetAddress"
    )

    return (
        city,
        district,
        street_address
    )


# =========================================================
# FIND JOBPOSTING JSON-LD
# =========================================================

def get_job_json(soup):
    """
    Find the JobPosting JSON-LD object
    inside a TopDev job page.
    """

    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):

        try:
            data = json.loads(
                script.get_text(strip=True)
            )

            if (
                isinstance(data, dict)
                and data.get("@type") == "JobPosting"
            ):
                return data

        except (
            json.JSONDecodeError,
            TypeError
        ):
            continue

    return None

# =========================================================
# SCRAPE ONE JOB
# =========================================================

def scrape_job(url):
    """
    Scrape one TopDev job page and return
    a flattened dictionary.
    """

    response = requests.get(url, headers=HEADERS,timeout=15)

    response.raise_for_status()

    soup = BeautifulSoup(response.text,"html.parser")

    job_data = get_job_json(soup)

    if job_data is None:
        return None

    # -------------------------
    # Salary
    # -------------------------

    min_salary, max_salary, currency = (parse_salary_json(job_data))

    # -------------------------
    # Location
    # -------------------------

    city, district, street_address = (parse_location_json(job_data))

    # -------------------------
    # Company
    # -------------------------

    organization = job_data.get("hiringOrganization", {})

    if isinstance(organization, dict):
        company = organization.get("name")
    else:
        company = None


    # -------------------------
    # Final record
    # -------------------------

    return {
        "created_date": job_data.get("datePosted"),
        "valid_through": job_data.get("validThrough"),
        "job_title": job_data.get("title"),
        "company": company,
        "min_salary": min_salary,
        "max_salary": max_salary,
        "salary_unit": currency,
        "skills": job_data.get("skills"),
        "city": city,
        "district": district,
        "street_address": street_address,
        "job_url": clean_job_url(url)
    }


# =========================================================
# EXTRACT DATA
# =========================================================

def extract_data(num_pages=5, delay=0.5):
    """
    Main extract function.

    1. Collect job URLs from TopDev.
    2. Scrape each job.
    3. Return DataFrame.
    """

    job_links = get_job_links(num_pages=num_pages)

    jobs = []

    total = len(job_links)

    print("\nScraping job details...\n")

    for i, url in enumerate(
        job_links,
        start=1
    ):

        try:

            job = scrape_job(url)

            if job is not None:
                jobs.append(job)

            if i%10 == 0:
                print(f"[{i}/{total}] OK")

        except requests.RequestException as e:

            print(f"[{i}/{total}] REQUEST ERROR: {e}")

        except Exception as e:

            print(
                f"[{i}/{total}] "
                f"ERROR: {e}"
            )

        # Avoid sending requests too aggressively
        time.sleep(delay)

    df = pd.DataFrame(jobs)

    if df.empty:
        raise ValueError(
            "No jobs were extracted from TopDev"
        )

    # Extra safety against duplicate URLs
    df = df.drop_duplicates(
        subset=["job_url"]
    ).reset_index(drop=True)

    print(
        f"\nExtracted {len(df)} "
        f"unique jobs successfully."
    )

    return df
