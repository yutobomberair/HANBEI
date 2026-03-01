import time
import random
import requests
from bs4 import BeautifulSoup

class BaseScraper:
    BASE_URL = ""

    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.netkeiba.com/"
        }
        self.calender_url = f"https://race.netkeiba.com/top/calendar.html"
        self.racelist_url = f"https://db.netkeiba.com/race/list/"
        self.race_url = f"https://db.netkeiba.com/race/"

    def polite_sleep(self, min_sec=1.0, max_sec=2.5):
        sec = random.uniform(min_sec, max_sec)
        print(f"[Sleeping] stop scraping {sec:.2f}s...")
        time.sleep(sec)
