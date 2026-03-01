import argparse
from datetime import datetime
from race_key_collector import RaceKeyCollector
from race_parser import RaceParser
from horse_detail_parser import HorseDetailParser
from base_scraper import BaseScraper

def generate_month_range(start: str, end: str) -> list[str]:
    """
    YYYYMM 形式で start〜end の全月を返す
    """
    start_date = datetime.strptime(start, "%Y%m")
    end_date = datetime.strptime(end, "%Y%m")

    if start_date > end_date:
        raise ValueError("start_month は end_month 以下にしてください")
    months = []
    current = start_date
    while current <= end_date:
        months.append(current.strftime("%Y%m"))
        # 1ヶ月進める
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    return months

def run_pipeline(date: str):
    base_scraper = BaseScraper()
    key_collector = RaceKeyCollector()
    race_parser = RaceParser()
    horse_parser = HorseDetailParser()

    racekeys = key_collector.main([2025])

    for key in racekeys:
        race_data = race_parser.main(key)
        base_scraper.polite_sleep()
        # for horse in race_data["horses"]:
        #     horse_id = horse.get("horse_id")
        #     if horse_id:
        #         horse_detail = horse_parser.parse_horse(horse_id)
        #         # 保存処理へ

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="レースキー取得スクリプト")
    parser.add_argument("start_month", type=str, help="開始月 (YYYYMM)")
    parser.add_argument("end_month", type=str, help="終了月 (YYYYMM)")
    args = parser.parse_args()
    period = generate_month_range(args.start_month, args.end_month)
    run_pipeline(period)