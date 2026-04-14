from dotenv import load_dotenv
load_dotenv()

from garmin_activities import main as sync_activities
from personal_records import main as sync_records
from daily_steps import main as sync_steps


def main():
    for name, fn in [("Activities", sync_activities), ("Records", sync_records), ("Steps", sync_steps)]:
        try:
            fn()
        except Exception as e:
            print(f"Error syncing {name}: {e}")


if __name__ == "__main__":
    main()
