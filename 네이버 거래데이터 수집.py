from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
from tqdm import tqdm 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import requests
plt.rc('font', family='Malgun Gothic') 

def grpah(df,name):
    ## 시각화 ##
    plt_df = df.set_index('날짜')[['종가','MA5','MA20','MA60','MA120']].plot(figsize=(24,6),title=name)
    
    
    plt.xlabel("time",fontsize=15)
    plt.ylabel("price",fontsize=15)

    plt.legend(loc='best')
    plt.grid()
    plt.show()
    
    
def MA(trade_df,invest_df,save=False):

    df = pd.merge(trade_df,invest_df,on='날짜').sort_values(by='날짜').reset_index(drop=True)
    df['날짜'] = df['날짜'].apply(pd.to_datetime)
    print(df.columns)
    df[['종가', '전일비', '시가', '고가', '저가', '거래량', '등락률', ' 순매매량(기관)', '순매매량(외국인)', '보유주수(외국인)', '보유율(외국인)']] = df[['종가', '전일비', '시가', '고가', '저가', '거래량', '등락률', ' 순매매량(기관)', '순매매량(외국인)', '보유주수(외국인)', '보유율(외국인)']].astype('float')

    # 5, 20 ,60, 120선 데이터 추가
    ma5 = df['종가'].rolling(window=5).mean()
    ma20 = df['종가'].rolling(window=20).mean()
    ma60 = df['종가'].rolling(window=60).mean()
    ma120 = df['종가'].rolling(window=120).mean()
    df['MA5'] = ma5
    df['MA20'] = ma20
    df['MA60'] = ma60
    df['MA120'] = ma120

    # 5일 단위 거래량 평균 추가
    vma5 = df['거래량'].rolling(window=5).mean()
    df["VMA5"] = vma5

    # 주가와 이동평균선 차이 정도(이격도) 추가
    disp5 = (df['종가']/df['MA5'])*100
    df["Disp5"] = disp5

    # 결측치 처리
    df = df.fillna(0)
    
    if (save):
        df.to_csv("trade.csv",index=False,encoding='utf-8-sig')
    
    return df

def find_code(name):
    stock_df = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download', header=0)[0]
    com_code = str(stock_df.loc[stock_df['회사명']==name,"종목코드"].to_list()[0])
    
    if len(com_code) != 6:
        com_code = "0" * (6 - len(com_code)) + str(com_code)
    
    return com_code


def invest(code):

    # 외국인, 기관 매매량
    url = "https://finance.naver.com/item/frgn.naver?code=" + code
    header = { "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"}
    res = requests.get(url,headers=header) # header 없이 request를 사용할 수 없도록 변경되었음
    soup = BeautifulSoup(res.text, 'html.parser')

    last_page = int(soup.select_one("td.pgRR > a")['href'].split('page=')[1])

    temp = []

    for page in tqdm(range(1,int(last_page)+1)):
        res = requests.get(url + "&page=" + str(page),headers=header)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.select("table.type2")[1].select('tr')[3:]
        for row in table:

            try:
                date = row.select_one(".p10").text
                close_price = row.select(".p11")[0].text.replace(",","")
                change_price = row.select(".p11")[1].text.replace("\t","").replace("\n","").replace(",","")
                change_rate = row.select(".p11")[2].text.replace("\t","").replace("\n","").replace("%","").replace("+","")
                trading_value = row.select(".p11")[3].text.replace(",","")
                g_trade = row.select(".p11")[4].text.replace(",","").replace("+","")
                f_trade = row.select(".p11")[5].text.replace(",","").replace("+","")
                f_have = row.select(".p11")[6].text.replace(",","")
                f_have_rate = row.select(".p11")[7].text.replace("%","")
            except:
                continue

            line = [date,close_price,change_price,change_rate,trading_value,g_trade,f_trade,f_have,f_have_rate]
            temp.append(line)

    invest_total_df = pd.DataFrame(temp,columns=['날짜', '종가', '전일비', '등락률', '거래량',' 순매매량(기관)','순매매량(외국인)','보유주수(외국인)','보유율(외국인)'])
    invest_total_df['날짜'] = invest_total_df['날짜'].apply(pd.to_datetime)
    return invest_total_df

def trade(code):
    # 일별 시세
    url = "https://finance.naver.com/item/sise_day.nhn?code=" + code
    header = { "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"}
    res = requests.get(url,headers=header)
    soup = BeautifulSoup(res.text, 'html.parser')

    last_page = int(soup.select_one("td.pgRR > a")['href'].split('page=')[1])

    temp = []
    for page in tqdm(range(1,int(last_page)+1)):
        temp_url = url + "&page=" + str(page)
        res = requests.get(temp_url,headers=header)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.select("table.type2")[0].select('tr')[2:]
        for row in table:
            try:
                date = row.select_one(".p10").text
                open_price = row.select(".p11")[2].text.replace("\t","").replace("\n","").replace("%","").replace("+","").replace(",","")
                high_price = row.select(".p11")[3].text.replace(",","")
                low_price = row.select(".p11")[4].text.replace(",","").replace("+","")
            except:
                continue


        line = [date,open_price,high_price,low_price]
        temp.append(line)

    trade_total_df = pd.DataFrame(temp,columns=['날짜','시가','고가','저가'])
    trade_total_df['날짜'] = trade_total_df['날짜'].apply(pd.to_datetime)
    return trade_total_df


name = "" # 원하는 거래 종목 명
code = find_code(name)

trade_total_df = trade(code)
invest_total_df = invest(code)
df = MA(trade_total_df,invest_total_df) # save 옵션 추가 시 파일 저장
grpah(df, name)