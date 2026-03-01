import re
import os
import yaml
import requests
from bs4 import BeautifulSoup
from base_scraper import BaseScraper

"""
レース結果ページから下記情報を抽出する
"race_key": NetKeibaデータベース上の管理ID

"meta": {
    "data": "2025-12-14",
    "holding": 4 # 回,
    "track": "東京",
    "event": "4" # 日目
    "race_num": "11R",
    "race_grade": "G2",
    "race_name": "京王杯SC",
    "age_min": "3",
    "age_max": None,
    "sex_condition": "混合",
    "surface": "芝",
    "distance": 1600,
    "turn": "左",
    "course_layout": "外", 
    "weather": "晴",
    "ground_condition": "良",
    "time": "15:40"
}

"structure": {
    "lap": [12.3, 11.1, 11.4, ...],
    "pace": [12.3, 23.4, 34.8, ...],
    "first3F": 34.6,
    "last3F": 34.6,
    "corner_positions": 馬群情報
}

"horses": [
    {
        "horse_id": "2019101234",
        "name": 馬名,
        "frame": 枠番号,
        "number": 馬番号,
        "odds": オッズ,
        "popularity": 人気,
        "finish_rank": 順位,
        "agari": 上がりタイム,
        "corner_passage": [5, 3, 2, 2],
        "Handicap": 斤量,
        "jockey": ジョッキー名,
        "horse_link": "xxxx_xxxxxx",
        "weight": 馬体重, 
        "weight_diff": 馬体重増減, 
        "trainer": 調教師,
        "owner": 馬主, 
        "prize": 獲得賞金
    },
    ...
]

"payouts": {
    "tansho": {  # 単勝
        "1": {"odds": 3.2, "popularity": 1},
        "2": {"odds": 5.4, "popularity": 2},
    },
    "fukusho": {  # 複勝
        "1": {"min": 1.5, "max": 1.8},
    },
    "umaren": {
        "1-2": 8.4,
    },
    "umatan": {
        "1-2": 14.2,
    },
    "sanrenpuku": {
        "1-2-3": 22.4,
    },
    "sanrentan": {
        "1-2-3": 140.2,
    }
}
"""

class RaceParser(BaseScraper):
    GRADE = {
        "GI": "G1",
        "GII": "G2",
        "GIII": "G3",
        "L": "L"
    }
    def __init__(self):
        super().__init__()

    def main(self, race_key: str):
        race_data = self.parse_race(race_key)
        if race_data["meta"] is not None:
            date = race_data["meta"]["date"]
            track = race_data["meta"]["track"]
            race_num = race_data["meta"]["race_num"]
            file_name = track + "_" + race_num + "_" + str(race_key)
            save_dir = os.path.join("/data/race_yaml/", date)
            os.makedirs(save_dir, exist_ok=True)
            file_path = os.path.join(save_dir, f"{file_name}.yaml")
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(race_data, f, allow_unicode=True, sort_keys=False)
            print(f"[Saved] {file_path}")
        return race_data

    def parse_race(self, race_key: str) -> dict:
        base_url = self.race_url + str(race_key)
        response = requests.get(base_url, headers=self.headers)
        if response.status_code == 200:
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, "lxml")
        else:
            raise Exception(f"HTTP Error: {status}")

        meta = self._parse_meta(soup)
        if meta is not None:
            structure = self._parse_structure(soup)
            horses = self._parse_horses(soup)
            payouts = self._parse_payouts(soup)
        else:
            structure = None
            horses = None
            payouts = None

        race_data = {
            "race_key": race_key,
            "meta": meta,
            "structure": structure,
            "horses": horses, 
            "payouts": payouts
        }
        return race_data

    def _parse_meta(self, soup):
        # 距離・馬場・コース種別など
        meta_src = soup.find_all("diary_snap")
        race_num = meta_src[0].dt.text.strip()
        race_name = meta_src[0].h1.text.strip()
        diary = meta_src[0].span.text
        info = soup.find_all(class_="smalltxt")[0].text
        race_title = self.__parse_race_title(race_name)
        race_condition = self.__parse_age_and_sex(info)
        race_event = self.__parse_holding_info(info)
        race_diary = self.__parse_course_info(diary)
        # output成形
        if race_diary is not None:
            meta = {}
            meta["date"] = race_event["date"]
            meta["holding"] = race_event["holding"]
            meta["track"] = race_event["track"]
            meta["event"] = race_event["event"]
            meta["race_num"] = race_num.replace(" ", "")
            meta["race_grade"] = race_title["grade"]
            meta["race_name"] = race_title["race_name"]
            meta["age_min"] = race_condition["age_min"]
            meta["age_max"] = race_condition["age_max"]
            meta["sex_condition"] = race_condition["sex_condition"]
            meta["surface"] = race_diary["surface"]
            meta["distance"] = race_diary["distance"]
            meta["turn"] = race_diary["turn"]
            meta["course_layout"] = race_diary["course_layout"]
            meta["weather"] = race_diary["weather"]
            meta["ground_condition"] = race_diary["going"]
            meta["time"] = race_diary["post_time"]
            return meta
        else:
            return None

    def __parse_race_title(self, title):
        result = {
            "race_name": None,
            "grade": None
        }
        # グレード抽出
        g = re.search(r"G(?:I{1,3}|[123])|L", title)
        if g:
            result["grade"] = self.GRADE[g.group(0)]
        # 勝クラス（1勝〜3勝）
        else:
            win_class = re.search(r"(\d)勝", title)
            if win_class:
                result["grade"] = f"{win_class.group(1)}勝"
            # OP
            elif re.search(r"[（(]OP[）)]", title):
                result["grade"] = "OP"
            # 新馬 or 未勝利
            elif "新馬" in title:
                result["grade"] = "新馬"
            # 未勝利
            elif "未勝利" in title:
                result["grade"] = "未勝利"
        # 文字削除して名前抽出
        cleaned = re.sub(r"第\d+回", "", title)
        cleaned = re.sub(r"[（(]G(?:I{1,3}|[123])[）)]", "", cleaned)
        cleaned = re.sub(r"[（(]L[）)]", "", cleaned)
        cleaned = re.sub(r"[（(]OP[）)]", "", cleaned)
        cleaned = re.sub(r"[（(](\d)勝[）)]", "", cleaned)
        result["race_name"] = cleaned.strip()
        return result

    def __parse_age_and_sex(self, info):
        result = {
            "age_min": None,
            "age_max": None,
            "sex_condition": "混合"
        }
        match = re.search(r"(\d)歳以上", info)
        if match:
            result["age_min"] = int(match.group(1))
            result["age_max"] = None
        else:
            match = re.search(r"(\d)歳", info)
            if match:
                result["age_min"] = int(match.group(1))
                result["age_max"] = int(match.group(1))
        if "牝" in info and "牡・牝" not in info:
            result["sex_condition"] = "牝限"
        return result

    def __parse_holding_info(self, info):
        # 第{holding}回{track}{event}日目
        result = {
            "date": None,
            "holding": None,
            "track": None,
            "event": None
        }
        # 日付
        date_match = re.search(r"(\d{4})年(\d{2})月(\d{2})日", info)
        if date_match:
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            day = int(date_match.group(3))
            result["date"] = f"{year:04d}-{month:02d}-{day:02d}"
        # 開催情報
        holding_match = re.search(r"(\d)回([^\d]+?)(\d+)日目", info)
        if holding_match:
            result["holding"] = int(holding_match.group(1))
            result["track"] = holding_match.group(2)
            result["event"] = int(holding_match.group(3))
        return result

    def __parse_course_info(self, diary):
        result = {
            "surface": None,
            "distance": None,
            "turn": None,
            "course_layout": None,
            "weather": None,
            "going": None,
            "post_time": None
        }
        try:
            # 芝右2500m など
            if "障" in diary:
                raise ValueError("Steeplechase races are excluded from scraping.")
            header_match = re.search(r"(芝|ダ)(右|左)?(\d+)m", diary)
            if header_match:
                # surface
                if header_match.group(1) == "芝":
                    result["surface"] = "芝"
                elif header_match.group(1) == "ダ":
                    result["surface"] = "ダ"
                else:
                    raise ValueError(f"")
                # turn
                if header_match.group(2) == "右":
                    result["turn"] = "右"
                elif header_match.group(2) == "左":
                    result["turn"] = "左"
                # distance
                result["distance"] = int(header_match.group(3))
            # 内外（あれば）
            if "内" in diary:
                result["course_layout"] = "内"
            elif "外" in diary:
                result["course_layout"] = "外"
            else:
                result["course_layout"] = None
            # 天候
            weather_match = re.search(r"天候\s*:\s*([^\s/]+)", diary)
            if weather_match:
                result["weather"] = weather_match.group(1)
            # 馬場状態
            going_match = re.search(r"(芝|ダ)\s*:\s*([^\s/]+)", diary)
            if going_match:
                result["going"] = going_match.group(2)
            # 発走時間
            time_match = re.search(r"発走\s*:\s*(\d{2}:\d{2})", diary)
            if time_match:
                result["post_time"] = time_match.group(1)
            return result
        except ValueError as e:
            print(f"[Skipped]: {e}")
            return None

    def _parse_structure(self, soup):
        """ラップ・コーナー通過順など（展開構造）"""
        result_tables = soup.find_all(class_="result_table_02")
        # ラップ
        lap_row = result_tables[2].find_all("td")[0]
        raw = lap_row.get_text(strip=True)
        laps = [float(x.strip()) for x in raw.split("-")]
        # ペース
        pace_row = result_tables[2].find_all("td")[1]
        raw = pace_row.get_text(strip=True)
        main, sectional = raw.split("(")
        sectional = sectional.replace(")", "")
        cumulative = [float(x.strip()) for x in main.split("-")]
        # 前後半3F
        first3f, last3f = [float(x) for x in sectional.split("-")]
        # コーナー情報
        corner_positions = self.__parse_corner_positions(result_tables[1])
        structure = {}
        structure["laps"] = laps
        structure["pace"] = cumulative
        structure["first3F"] = first3f 
        structure["last3F"] = last3f
        structure["corner_positions"] = corner_positions
        return structure

    def __parse_corner_positions(self, corner_info):
        corners = {
            "1corner": None,
            "2corner": None,
            "3corner": None,
            "4corner": None
        }
        rows = corner_info.find_all("tr")
        for n, _ in enumerate(rows):
            row = rows[-(n+1)]
            corner_name = row.find("th").get_text(strip=True)
            raw = row.find("td").get_text(strip=True)
            raw_strip = self.__parse_corner_with_gaps(raw)
            corners[f"{4-n}corner"] = raw_strip

        return corners

    def __parse_corner_with_gaps(self, raw):
        result = []
        i = 0
        current_gap = None
        GAP_MAP = {
            ",": "1to2_lengths",   # 1~2馬身
            "-": "2to5_lengths",   # 2~5馬身
            "=": "5plus_lengths"   # 5馬身以上
        }
        while i < len(raw):
            char = raw[i]
            # ギャップ記号
            if char in GAP_MAP:
                current_gap = GAP_MAP[char]
                i += 1
                continue
            # 並走グループ ()
            if char == "(":
                end = raw.find(")", i)
                group = raw[i+1:end]
                horses = []
                leader = None
                for h in group.split(","):
                    if h.startswith("*"):
                        num = int(h.replace("*", ""))
                        leader = num
                        horses.append(num)
                    else:
                        horses.append(int(h))
                # gap決定ロジック
                if not result:
                    gap = None  # 先頭
                else:
                    gap = current_gap if current_gap else "0to1_length"
                result.append({
                    "horses": horses,
                    "group_leader": leader,
                    "gap_from_prev": gap
                })
                current_gap = None
                i = end + 1
                continue
            # 単馬（*付き含む）
            if char == "*" or char.isdigit():
                star = False
                if char == "*":
                    star = True
                    i += 1
                num = ""
                while i < len(raw) and raw[i].isdigit():
                    num += raw[i]
                    i += 1
                if not result:
                    gap = None
                else:
                    gap = current_gap if current_gap else "0to1_length"
                result.append({
                    "horses": [int(num)],
                    "group_leader": int(num) if star else None,
                    "gap_from_prev": gap
                })
                current_gap = None
                continue
            i += 1
        return result

    def _parse_horses(self, soup):
        """各馬の着順・上がりなど"""
        results = []
        table = soup.find(class_="race_table_01 nk_tb_common")
        rows = table.select("tr")[1:]
        for row in rows:
            horse_data = self.__parse_horse_row(row)
            if horse_data:
                results.append(horse_data)
        return sorted(results, key=lambda x: x["horse_number"])

    def __parse_horse_row(self, row):
        cols = row.find_all("td")
        if len(cols) < 10:
            return None
        result = {}
        # 枠番
        result["frame_number"] = int(cols[1].text.strip())
        # 馬番
        result["horse_number"] = int(cols[2].text.strip())
        # 馬名 + horse_id
        horse_tag = cols[3].find("a")
        result["horse_name"] = horse_tag.text.strip()
        result["horse_id"] = horse_tag["href"].split("/")[-2]
        # 性齢
        sex_age = cols[4].text.strip()
        result["sex"] = sex_age[0]
        result["age"] = int(sex_age[1:])
        # 斤量
        result["weight_carried"] = float(cols[5].text.strip())
        # 騎手
        jockey_tag = cols[6].find("a")
        result["jockey_name"] = jockey_tag.text.strip()
        result["jockey_id"] = jockey_tag["href"].split("/")[-2]
        # 馬体重
        body_weight, weight_change = self.__parse_body_weight(cols[14].text.strip())
        result["body_weight"] = body_weight
        result["weight_change"] = weight_change
        # 調教師
        trainer_tag = row.select_one("a[href*='/trainer/']")
        if trainer_tag:
            result["trainer_name"] = trainer_tag.text.strip()
            result["trainer_id"] = trainer_tag["href"].split("/")[-2]
        # 所属（東西）
        stable_text = row.select_one("td.txt_l").text
        if "[" in stable_text:
            result["stable_region"] = stable_text.strip()[1]
        # 馬主
        owner_tag = row.select_one("a[href*='/owner/']")
        if owner_tag:
            result["owner_name"] = owner_tag.text.strip()
            result["owner_id"] = owner_tag["href"].split("/")[-2]
        # 着順
        rank_raw = cols[0].text.strip()
        rank = None if rank_raw in ["中", "除", "取"] else int(rank_raw)
        result["rank_raw"] = rank_raw
        result["rank"] = rank
        if rank is not None:
            # タイム
            result["time"] = self.__parse_time(cols[7].text.strip())
            # 着差
            result["margin"] = cols[8].text.strip()
            # 通過順位
            result["corner_positions"] = [int(x) for x in cols[10].text.strip().split("-")]
            # 上がり
            result["last3f"] = float(cols[11].text.strip())
            # 単勝オッズ
            result["odds"] = float(cols[12].text.strip())
            # 人気
            result["popularity"] = int(cols[13].text.strip())
        else:
            result["time"] = None
            result["margin"] = None
            result["corner_positions"] = None
            result["last3f"] = None
            result["odds"] = None
            result["popularity"] = None
        return result

    def __parse_body_weight(self, text):
        m = re.match(r"(\d+)\(([-+]?\d+)\)", text)
        if not m:
            return None, None
        return int(m.group(1)), int(m.group(2))

    def __parse_time(self, t):
        if t is not None:
            minute, sec = t.split(":")
            return int(minute) * 60 + float(sec)
        else:
            return None

    def _parse_payouts(self, soup):
        """払い戻し結果"""
        coord = {
            "単勝": "tansho", 
            "複勝": "fukusho",
            "枠連": "wakuren",
            "馬連": "umaren",
            "馬単": "umatan",
            "ワイド": "wide",
            "三連複": "sanrenfuku",
            "三連単": "sanrentan"       
        }
        pay_tables = soup.find_all(class_="pay_table_01")
        payouts = {}
        for table in pay_tables:
            rows = table.find_all("tr")
            for row in rows:
                bet_type = row.find("th").get_text(strip=True)
                tds = row.find_all("td")
                if len(tds) != 3:
                    continue
                combos = tds[0].get_text("\n", strip=True).split("\n")
                amounts = tds[1].get_text("\n", strip=True).split("\n")
                popularity = tds[2].get_text("\n", strip=True).split("\n")

                # カンマ除去して int 化
                amounts = [int(a.replace(",", "")) for a in amounts]
                popularity = [int(p) for p in popularity]
                entries = []
                for c, a, p in zip(combos, amounts, popularity):
                    entries.append({
                        "combination": c.strip(),
                        "payout": a,
                        "popularity": p
                    })
                payouts[coord[bet_type]] = entries
        return payouts

if __name__ == "__main__":
    inst = RaceParser()
    # ret = inst.parse_race(202205040911) # G1
    # inst.main(202205040911)
    # ret = inst.parse_race(202509050711) # G2
    # ret = inst.parse_race(202506050411) # G3
    # ret = inst.parse_race(202509050610) # Listed
    # ret = inst.parse_race(202509050509) # OP
    # ret = inst.parse_race(202509050612) # 3勝クラス
    # ret = inst.parse_race(202508031108) # 2勝クラス
    # ret = inst.parse_race(202507050609) # 1勝クラス
    # ret = inst.parse_race(202507050601) # 未勝利
    # ret = inst.parse_race(202507050605) # 新馬
    # ret = inst.parse_race(202503030405) # 障害
    inst.main(202506050308)
    # print(ret)