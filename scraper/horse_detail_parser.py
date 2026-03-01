from base_scraper import BaseScraper

class HorseDetailParser(BaseScraper):

    def parse_horse(self, horse_id: str) -> dict:
        url = f"https://db.netkeiba.com/horse/{horse_id}/"
        soup = self.fetch(url)

        horse_data = {
            "horse_id": horse_id,
            "profile": self._parse_profile(soup),
            "history": self._parse_race_history(soup)
        }

        return horse_data

    def _parse_profile(self, soup):
        return {}

    def _parse_race_history(self, soup):
        return []