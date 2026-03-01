import re
import requests
from bs4 import BeautifulSoup
from base_scraper import BaseScraper

class RaceKeyCollector(BaseScraper):
    JRA_CODES = {"01","02","03","04","05","06","07","08","09","10"}
    def __init__(self):
        super().__init__()

    def main(self, period: list):
        """
        period: [YYYY - YYYY]
        return: [race_key list]
        """
        dates = self.get_kaisai_dates(period)
        racekeys = self.get_racekeys_by_date(dates)
        return racekeys

    def get_kaisai_dates(self, period: list) -> list[str]:
        dates = set()
        for ym in period:
            y = ym[:4]
            m = ym[4:]
            url = self.calender_url + f"?year={y}&month={m}"
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, "lxml")
            for a in soup.find_all("a", href=True):
                if "kaisai_date=" in a["href"]:
                    date = a["href"].split("kaisai_date=")[1]
                    dates.add(date)
            self.polite_sleep()
        return sorted(list(dates))

    def get_racekeys_by_date(self, dates:list):
        racekeys = set()
        for date in dates:
            url = self.racelist_url + str(date)
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                print("Request failed:", response.status_code)
                return None
            soup = BeautifulSoup(response.text, "lxml")
            pattern = re.compile(r"/race/(\d{12})/?$")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                m = pattern.match(href)
                if m:
                    race_key = m.group(1)
                    place_code = race_key[8:10]
                    if place_code in self.JRA_CODES:
                        racekeys.add(race_key)
            self.polite_sleep()
        return list(racekeys)

if __name__ == "__main__":
    inst = RaceKeyCollector()
    result = inst.main([2025])
    print(result)