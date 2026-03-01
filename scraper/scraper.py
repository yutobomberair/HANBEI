##library
# スクレイピング
# from selenium import webdriver
# from time import sleep
import requests
from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# import time
# テーブル操作
# import pandas as pd
# import numpy as np
# 画像出力
# import platform
#%matplotlib inline
# import argparse
# import os



class data_scraping:
    def __init__(self, race_key):
        self.race_key = race_key
        # self.url = "https://db.netkeiba.com/race/"+str(race_key)
        self.url = "https://db.netkeiba.com/race/202505010811/"
        self.course = 0
        self.distance = 0
        self.h_num = 0
        self.h_name = 0
        self.h_agari = 0
        self.form_corner = 0
        self.laptime = 0
        self.get_info()

    def get_info(self):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.netkeiba.com/"
        }
        response = requests.get(self.url, headers=headers)
        print(response.status_code)
        # print(response.text[:500])  
        # print(response)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "lxml")
        # soup = BeautifulSoup(response.content, 'html.parser')
        # print(soup)
        #分析対象
        self.course = soup.find('a', class_="active").text
        d_tmp = soup.find_all('p')[3].span.text.split('/')[0]
        self.distance = int(d_tmp[-6:-2])
        corner = soup.find_all('table', class_="result_table_02")
        self.form_corner = self.__corner_plot(corner[1])
        self.laptime = [float(i) for i in soup.find(class_='race_lap_cell').text.split(" - ")]
        self.h_name = [i.a.text for n, i in enumerate(soup.find_all('td', class_="txt_l")) if n % 4 == 0]
        self.h_agari = [float(i.text) for n, i in enumerate(soup.find_all('span')[7:]) if n % 3 == 1 and i.text != ""]
        self.h_num = [int(i.text) for n, i in enumerate(soup.find_all('td', class_="txt_r")[:5 * len(self.h_agari)]) if n % 5 == 1]
        
    def __corner_plot(self, corner):
        # h: 1.5馬身差
        # i: 3.5馬身差
        # s: 5馬身差
        li = []
        for i in corner.find_all('td'):
            li.append(i.text)
        corner = []
        for r in li:
            if r != '':
                exch = []
                cp = 0
                ap_i = 0
                for n, i in enumerate(r):
                    if i == ',':
                        continue
                    elif cp == 1:
                        exch[-1] = exch[-1] + i
                        cp = 0
                    elif i == '1' and n != len(r)-1:
                        if r[n+1] != ',' and r[n+1] !=  '(' and r[n+1] != ')' and r[n+1] != '-' and r[n+1]  != '=' and r[n+1] != '*':
                            exch.append(i)
                            cp = 1
                        else:
                            exch.append(i)
                    elif i == '-':
                        exch.append('h')
                    elif i == '=':
                        exch.append('i')
                    elif i == '*':
                        exch.append('s')
                    else:
                        exch.append(i)
                c_rank = [] 
                sp = 0
                for i in exch:
                    if i == ')':
                        c_rank.append(ap)
                        ap_i = 0
                    elif ap_i == 1:
                        if sp == 1:
                            i = '*' + i
                            sp = 0
                            ap.append(i)
                        elif i == 's':
                            sp = 1
                        else:
                            ap.append(i)
                    elif i == '(':
                        ap = []
                        ap_i = 1
                    elif sp == 1:
                        i = '*' + i
                        sp = 0
                        c_rank.append(i)
                    elif i == 's':
                        sp = 1
                    else:
                        c_rank.append(i)
                corner.append(c_rank)
            else:
                corner.append('')
        return corner

if __name__ == "__main__":
    inst = data_scraping(202505010811)
    print(inst.h_num)
    print(inst.h_name)
    print(inst.h_agari)
    print(inst.form_corner)
    print(inst.laptime)

