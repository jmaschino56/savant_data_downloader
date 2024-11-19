# Baseball Savant Data Downloader
This repository contains a Python script for fetching Statcast data from Baseball Savant, processing it, and converting it into a structured format using Polars. The data is fetched concurrently to optimize performance and includes retry logic for handling failures.

## Features
- Fetches Statcast data for a range of dates.
- Handles retries in case of request failures.
- Uses ThreadPoolExecutor to fetch data concurrently for each day in the specified range.
- Combines CSV data from multiple days into a single Polars DataFrame.
- Dynamically handles type conversions for string columns (including dates).
- Filters out rows where all columns are null.

## Installation
Ensure you have the required dependencies installed:

`pip install tqdm polars requests`

## Usage
Fetching Statcast Data for a Date Range
You can use the `get_new_data()` function to fetch Statcast data for a specific date range. This function will iterate through each date in the range, fetch data concurrently, and process it into a Polars DataFrame.

```
from savant_data_downloader import get_new_data

start_date = '2023-01-01'
end_date = '2023-01-10'

# Fetch the data
`data = get_new_data(start_date, end_date)`

# If data was fetched successfully, it will be returned as a Polars DataFrame
if data:
    print(data)
else:
    print("No data fetched.")
```

## Function Descriptions
`get_statcast_data(day, max_retries=3, retry_delay=5)`

Fetches Statcast data for a single day. If the request fails, the function will retry up to `max_retries` times, waiting `retry_delay` seconds between retries.

- Arguments:
  - `day` (str): The date in `YYYY-MM-DD` format for which to fetch data.
  - `max_retries` (int): The maximum number of retries for failed requests (default is 3).
  - `retry_delay` (int): The number of seconds to wait before retrying (default is 5).
- Returns:
  - The CSV content of the requested day if successful, or `None` if no data is fetched or after retries are exhausted.


`get_new_data(start_date, end_date)`

Fetches Statcast data for the entire date range from start_date to end_date. This function uses concurrent requests to fetch data for each day in the range efficiently.
- Arguments:
  - `start_date` (str): The start date of the range in `YYYY-MM-DD` format.
  - `end_date` (str): The end date of the range in `YYYY-MM-DD` format.
- Returns:
  - A Polars DataFrame containing the combined data for the specified date range, or `None` if no data is fetched.
 
## Example Output
When the data is successfully fetched, you will get a Polars DataFrame containing the Statcast data for the specified date range. This DataFrame includes all relevant columns from the fetched CSV data, with type conversions applied (e.g., date and numerical columns).

## Notes
- The data fetching is done using `requests.get()` and is optimized using `ThreadPoolExecutor` to run concurrently.
- If the date range includes future dates, the `end_date` will be capped to the current date.
- Empty responses or failed requests will be handled gracefully with retry logic.
