from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import polars as pl
import io
import requests
from datetime import datetime, timedelta, date
from time import sleep


def get_statcast_data(day, max_retries=3, retry_delay=5):
    """
    Fetches Statcast data for a single day with retry on failures.
    """
    statcast_csv_url = (
        f"https://baseballsavant.mlb.com/statcast_search/csv?"
        f"all=true&batter_stands=&game_date_gt={day}&game_date_lt={day}&"
        f"group_by=name&hfAB=&hfBBL=&hfBBT=&hfC=&hfFlag=&hfGT=R%7CPO%7CF%7CD%7CL%7CW%7CS%7CA%7C&"
        f"hfInfield=&hfInn=&hfMo=&hfNewZones=&hfOpponent=&hfOutfield=&hfOuts=&hfPR=&hfPT=&hfPull=&hfRO=&"
        f"hfSA=&hfSea=&hfSit=&hfStadium=&hfTeam=&hfZ=&home_road=&metric_1=&min_pas=0&min_pitches=0&min_results=0&"
        f"minors=false&pitcher_throws=&player_event_sort=api_p_release_speed&player_type=pitcher&position=&"
        f"sort_col=pitches&sort_order=desc&type=details&"
    )

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(statcast_csv_url, timeout=None)
            response.raise_for_status()  # Raise an exception for HTTP errors
            if not response.content.strip():  # Skip empty content
                print(f"No data for {day}.")
                return None
            return response.content.decode('utf-8')  # Decode the CSV response content as a string
        except requests.RequestException as e:
            print(f"Error fetching data for {day}, attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                sleep(retry_delay)  # Wait before retrying
            else:
                print(f"Max retries reached for {day}. Moving on.")
                return None


def get_new_data(start_date, end_date):
    """
    Fetches Statcast data for the date range [start_date, end_date] one day at a time,
    using tqdm for progress indication and concurrent requests for efficiency.
    """
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Cap end_date to today if it's in the future
    if end_date > date.today():
        end_date = date.today()

    # Generate a list of all dates in the range
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    # Fetch data concurrently with a progress bar
    all_responses = []
    with ThreadPoolExecutor() as executor:
        for response_content in tqdm(executor.map(get_statcast_data, dates), total=len(dates), desc="Fetching Statcast Data"):
            if response_content:  # Skip days with no data
                all_responses.append(response_content)

    # Combine all fetched data into a single Polars DataFrame
    if all_responses:
        # Combine responses into a single string, removing headers from all but the first response
        combined_csv = "\n".join(
            response if idx == 0 else "\n".join(response.splitlines()[1:])
            for idx, response in enumerate(all_responses)
        )

        # Use StringIO to simulate a file-like object
        buffer = io.StringIO(combined_csv)

        # Read the combined CSV string into a Polars DataFrame
        final_df = pl.read_csv(buffer, try_parse_dates=True)

        # Dynamically detect string columns for conversion
        schema_guess = final_df.schema
        string_columns = [col for col, dtype in schema_guess.items() if dtype == pl.Utf8]
        datetime_columns = [col for col in string_columns if "date" in col.lower() or "time" in col.lower()]

        # Convert dynamically detected columns with error handling
        for col in string_columns:
            try:
                if col in datetime_columns:
                    # Attempt to parse datetime columns
                    final_df = final_df.with_columns(
                        pl.col(col).str.to_date(format="%Y-%m-%d", strict=False).alias(col)
                    )
                else:
                    # Try converting to integer first, then fallback to float if necessary
                    try:
                        final_df = final_df.with_columns(
                            pl.col(col).cast(pl.Int64).alias(col)
                        )
                    except Exception:
                        # If integer conversion fails, try float
                        final_df = final_df.with_columns(
                            pl.col(col).cast(pl.Float64).alias(col)
                        )
            except Exception as e:
                #print(f"Skipping column '{col}' due to conversion error: {e}") #used for debugging
                continue

        # Filter out rows where all columns are null
        final_df = final_df.filter(~pl.all_horizontal(pl.all().is_null()))

        return final_df
    else:
        print("No data fetched.")
        return None