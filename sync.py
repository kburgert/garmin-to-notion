from dotenv import load_dotenv
load_dotenv()

from garmin_activities import main as sync_activities
from personal_records import main as sync_records
from daily_steps import main as sync_steps


def main():
    sync_activities()
    sync_records()
    sync_steps()


if __name__ == "__main__":
    main()
