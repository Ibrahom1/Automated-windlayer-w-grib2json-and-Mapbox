#!/bin/bash
START_DATE="20240717"
START_TIME="00"
INTERVALS=("00" "06" "12" "18")
BASE_URL="https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_1p00.pl"
LEV="lev_10_m_above_ground=on"
LEFTLON="0"
RIGHTLON="360"
TOPLAT="90"
BOTTOMLAT="-90"

# Path to the grib2json executable
GRIB2JSON_PATH="PATH"

# File to store the last download date and time
LAST_RUN_FILE="last_run.txt"
# File to log the downloaded files
LOG_FILE="download_log.txt"

# Directories for storing files
GFS_DIR="gfs"
JSON_DIR="json"

# Create directories if they don't exist
mkdir -p "$GFS_DIR"
mkdir -p "$JSON_DIR"

increment_date() {
  local date=$1
  local interval=$2
  local timestamp=$(date -d "$date +$interval days" +%Y%m%d)
  echo "$timestamp"
}

file_exists() {
  local url=$1
  curl -s --head "$url" | head -n 1 | grep "HTTP/1.1 200 OK" > /dev/null
}

# Load the last run date and time, or use the starting values
if [ -f "$LAST_RUN_FILE" ]; then
  read -r LAST_DATE LAST_TIME < "$LAST_RUN_FILE"
else
  LAST_DATE=$START_DATE
  LAST_TIME=$START_TIME
fi

current_date=$LAST_DATE
current_time=$LAST_TIME

file_already_downloaded() {
  local filename=$1
  [ -f "$filename" ]
}

while true; do
  for time in "${INTERVALS[@]}"; do
    # Construct the file URL and download URL
    FILE_URL="gfs.t${time}z.pgrb2.1p00.f000"
    URL="${BASE_URL}?file=${FILE_URL}&${LEV}&leftlon=${LEFTLON}&rightlon=${RIGHTLON}&toplat=${TOPLAT}&bottomlat=${BOTTOMLAT}&dir=%2Fgfs.${current_date}%2F${time}%2Fatmos"
    
    # Construct the local filename with date and interval
    LOCAL_FILE="gfs.t${time}z.pgrb2.1p00.f000"
    RENAMED_FILE="${GFS_DIR}/gfs_${current_date}_${time}.pgrb2.1p00.f000"
    JSON_FILE="${JSON_DIR}/gfs_${current_date}_${time}.json"
    echo "Fetching URL: ${URL}"

    # Check if the file exists before downloading
    if file_exists "$URL"; then
      # Download the file if it doesn't already exist
      if ! file_already_downloaded "$RENAMED_FILE"; then
        curl -L -o "$LOCAL_FILE" "$URL"
        # Rename the file to include the date and time and move to the gfs folder
        mv "$LOCAL_FILE" "$RENAMED_FILE"
        echo "$current_date $time $RENAMED_FILE" >> "$LOG_FILE"
      else
        echo "File $RENAMED_FILE already exists. Skipping download."
      fi

      # Convert GRIB file to JSON using PowerShell
      if ! file_already_downloaded "$JSON_FILE"; then
        powershell -Command "& { & '${GRIB2JSON_PATH}' --names --data --fp wind --fs 103 --fv 10.0 -o $JSON_FILE $RENAMED_FILE }"
        echo "Converted $RENAMED_FILE to $JSON_FILE"
      else
        echo "JSON file $JSON_FILE already exists. Skipping conversion."
      fi

      # Update the last run date and time
      echo "$current_date $time" > "$LAST_RUN_FILE"
    else
      echo "No data available for $current_date at $time. Stopping execution."
      exit 1
    fi
  done

  # Move to the next date
  current_date=$(increment_date $current_date 1)
done
