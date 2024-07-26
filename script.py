#!/usr/bin/env python3
import os
import requests
import subprocess
from datetime import datetime, timedelta

START_DATE = "20240716"
INTERVALS = ["00", "06", "12", "18"]
BASE_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_1p00.pl"
LEV = "lev_10_m_above_ground=on"
LEFTLON = "0"
RIGHTLON = "360"
TOPLAT = "90"
BOTTOMLAT = "-90"
# Path to the grib2json executable
GRIB2JSON_PATH = "PATH"
# File to store the last download date and time
LAST_RUN_FILE = "last_run.txt"
# File to log the downloaded files
LOG_FILE = "download_log.txt"

# Directories for storing files
GFS_DIR = "gfs"
JSON_DIR = "json"

# Create directories if they don't exist
os.makedirs(GFS_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

def increment_date(date_str, interval):
    date = datetime.strptime(date_str, "%Y%m%d")
    new_date = date + timedelta(days=interval)
    return new_date.strftime("%Y%m%d")

def file_exists(url):
    response = requests.head(url)
    return response.status_code == 200

def read_last_run():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, "r") as f:
            return f.read().strip().split()
    else:
        return START_DATE, INTERVALS[0]

def write_last_run(date, time):
    with open(LAST_RUN_FILE, "w") as f:
        f.write(f"{date} {time}")

def log_download(date, time, filename):
    with open(LOG_FILE, "a") as f:
        f.write(f"{date} {time} {filename}\n")

def file_already_downloaded(filename):
    return os.path.exists(filename)

last_date, last_time = read_last_run()

current_date = last_date
current_time = last_time

while True:
    data_available = False
    for time in INTERVALS:
        attempts = 0
        while attempts < 2:
            file_url = f"gfs.t{time}z.pgrb2.1p00.f000"
            url = (f"{BASE_URL}?file={file_url}&{LEV}&leftlon={LEFTLON}&rightlon={RIGHTLON}&"
                   f"toplat={TOPLAT}&bottomlat={BOTTOMLAT}&dir=%2Fgfs.{current_date}%2F{time}%2Fatmos")
            
            local_file = f"gfs.t{time}z.pgrb2.1p00.f000"
            renamed_file = os.path.join(GFS_DIR, f"gfs_{current_date}_{time}.pgrb2.1p00.f000")
            json_file = os.path.join(JSON_DIR, f"gfs_{current_date}_{time}.json")

            print(f"Fetching URL: {url}")

            if file_exists(url):
                data_available = True
                if not file_already_downloaded(renamed_file):
                    response = requests.get(url)
                    with open(local_file, "wb") as f:
                        f.write(response.content)
                    os.rename(local_file, renamed_file)
                    log_download(current_date, time, renamed_file)
                else:
                    print(f"File {renamed_file} already exists. Skipping download.")

                if not file_already_downloaded(json_file):
                    subprocess.run([
                        'powershell', '-Command',
                        f"& {{ & '{GRIB2JSON_PATH}' --names --data --fp wind --fs 103 --fv 10.0 -o {json_file} {renamed_file} }}"
                    ])
                    print(f"Converted {renamed_file} to {json_file}")
                else:
                    print(f"JSON file {json_file} already exists. Skipping conversion.")

                write_last_run(current_date, time)
                break
            else:
                attempts += 1
                if attempts == 2:
                    print(f"No data available for {current_date} at {time} after {attempts} attempts. Trying next interval.")

    if not data_available:
        print(f"No data available for any interval on {current_date}. Trying next date.")
    
    current_date = increment_date(current_date, 1)

    if current_date == datetime.utcnow().strftime("%Y%m%d"):
        break
