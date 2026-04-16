import time
from datetime import date, timedelta
from garminconnect import Garmin, GarminConnectTooManyRequestsError
from notion_client import Client
from dotenv import load_dotenv
import os

_GARTH_DIR = "/tmp/garth_tokens"
_RETRY_DELAYS = [60, 120, 240]


def login_garmin(email: str, password: str) -> Garmin:
    """Login to Garmin Connect, reusing cached tokens when available.

    Falls back to username/password login and retries with exponential backoff
    on rate limit errors.
    """
    client = Garmin(email, password, garth_dir=_GARTH_DIR)
    last_exc = None
    for delay in [0] + _RETRY_DELAYS:
        if delay:
            print(f"Rate limited by Garmin. Waiting {delay}s before retry...")
            time.sleep(delay)
        try:
            client.login()
            return client
        except GarminConnectTooManyRequestsError as exc:
            last_exc = exc
    raise last_exc


def get_all_daily_steps(garmin):
    """
    Get last x days of daily step count data from Garmin Connect.
    """
    startdate = date.today() - timedelta(days=1)
    daterange = [startdate + timedelta(days=x) 
                 for x in range((date.today() - startdate).days)] # excl. today
    daily_steps = []
    for d in daterange:
        daily_steps += garmin.get_daily_steps(d.isoformat(), d.isoformat())
    return daily_steps

def daily_steps_exist(client, database_id, activity_date):
    """
    Check if daily step count already exists in the Notion database.
    """
    query = client.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {"property": "Date", "date": {"equals": activity_date}},
                {"property": "Activity Type", "title": {"equals": "Walking"}}
            ]
        }
    )
    results = query['results']
    return results[0] if results else None

def steps_need_update(existing_steps, new_steps):
    """
    Compare existing steps data with imported data to determine if an update is needed.
    """
    existing_props = existing_steps['properties']
    activity_type = "Walking"
    
    return (
        existing_props['Total Steps']['number'] != new_steps.get('totalSteps') or
        existing_props['Step Goal']['number'] != new_steps.get('stepGoal') or
        existing_props['Total Distance (km)']['number'] != new_steps.get('totalDistance') or
        existing_props['Activity Type']['title'] != activity_type
    )

def update_daily_steps(client, existing_steps, new_steps):
    """
    Update an existing daily steps entry in the Notion database with new data.
    """
    total_distance = new_steps.get('totalDistance')
    if total_distance is None:
        total_distance = 0
    properties = {
        "Activity Type":  {"title": [{"text": {"content": "Walking"}}]},
        "Total Steps": {"number": new_steps.get('totalSteps')},
        "Step Goal": {"number": new_steps.get('stepGoal')},
        "Total Distance (km)": {"number": round(total_distance / 1000, 2)}
    }
    
    update = {
        "page_id": existing_steps['id'],
        "properties": properties,
    }
        
    client.pages.update(**update)

def create_daily_steps(client, database_id, steps):
    """
    Create a new daily steps entry in the Notion database.
    """
    total_distance = steps.get('totalDistance')
    if total_distance is None:
        total_distance = 0
    properties = {
        "Activity Type": {"title": [{"text": {"content": "Walking"}}]},
        "Date": {"date": {"start": steps.get('calendarDate')}},
        "Total Steps": {"number": steps.get('totalSteps')},
        "Step Goal": {"number": steps.get('stepGoal')},
        "Total Distance (km)": {"number": round(total_distance / 1000, 2)}
    }
    
    page = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }
    
    client.pages.create(**page)

def main():
    load_dotenv()

    # Initialize Garmin and Notion clients using environment variables
    garmin_email = os.getenv("GARMIN_EMAIL")
    garmin_password = os.getenv("GARMIN_PASSWORD")
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_STEPS_DB_ID")

    # Initialize Garmin client and login
    garmin = login_garmin(garmin_email, garmin_password)
    client = Client(auth=notion_token)

    daily_steps = get_all_daily_steps(garmin)
    for steps in daily_steps:
        steps_date = steps.get('calendarDate')
        existing_steps = daily_steps_exist(client, database_id, steps_date)
        if existing_steps:
            if steps_need_update(existing_steps, steps):
                update_daily_steps(client, existing_steps, steps)
        else:
            create_daily_steps(client, database_id, steps)

if __name__ == '__main__':
    main()
