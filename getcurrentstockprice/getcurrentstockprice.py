import os, re, time, datetime, logging

from urllib.request import build_opener, HTTPCookieProcessor
from urllib.parse import urlencode
from http.cookiejar import CookieJar

PALLAREL_NUM = os.environ.get("PALLAREL_NUM")
PALLAREL_ID = os.environ.get("PALLAREL_ID")
CONTROL_ID = os.environ.get("CONTROL_ID")
LOGIN_CONTROL_ID = os.environ.get("LOGIN_CONTROL_ID")
PAGE_ID = os.environ.get("PAGE_ID")
LOGIN_PAGE_ID = os.environ.get("LOGIN_PAGE_ID")
DATA_STORE_ID = os.environ.get("DATA_STORE_ID")
LOGIN_ID = os.environ.get("LOGIN_ID")
LOGIN_PASS = os.environ.get("LOGIN_PASS")


formatter = '%(levelname)s : %(asctime)s : %(message)s'
logging.basicConfig(level=logging.INFO, format=formatter)

availablestockIDs = []

stock_price_dic = dict()

def getcurrentprice(stockids):  
    opener = build_opener(HTTPCookieProcessor(CookieJar())) 

    url = ""

    post = {
        "_ControlID":LOGIN_CONTROL_ID,
        "_PageID":LOGIN_PAGE_ID,
        "user_id":LOGIN_ID,
        "user_password":LOGIN_PASS
    }

    login_data = urlencode(post).encode('utf-8')
    res = opener.open(url, login_data)

    post = {
        "_ControlID": CONTROL_ID,
        "_PageID": PAGE_ID,
        "_DataStoreID": DATA_STORE_ID,
    }


    for stockid in stockids:
        post["i_stock_sec"] = stockid
        data = urlencode(post).encode('utf-8')

        res = opener.open(url, data)

        html = res.read()
        shift = html.decode('Shift_JIS')

        try:
            price = re.search(r"(?<=現在値)[\"\'\-\+=><\(\)/0-9A-Za-z\n\r_&;:., ]*[0-9]*\,?[0-9]+\.?[0-9]*(?=</span>)",shift)
            price = re.search(r"[0-9]*\,?[0-9]+\.?[0-9]*$",price.group())
            price = float(price.group().replace(",", ""))

            logging.info("Success to get price {}".format(price))
        except:
            logging.warning("failed to parse price from response data")
            price = -1

        try:
            price_movement = re.search(r"(?<=前日比)[\"\'\-\+=><\(\)/0-9A-Za-z\n\r&;:., ]*[\+\-]?[0-9]*\,?[0-9]+\.?[0-9]*(?=</font>)",shift)
            price_movement = re.search(r"[\+\-]?[0-9]*\,?[0-9]+\.?[0-9]*$",price_movement.group())
            price_movement = float(price_movement.group().replace(",", ""))

            logging.info("Success to get price movement {}".format(price_movement))
        except:
            logging.warning("failed to parse price movement from response data")
            price_movement = None
        
        if price > 0 and price_movement is not None:
            stock_price_dic[stockid] = [price, price_movement]
            
    return


def getCurrentStockPrice():
    logging.info("start")
    availablestockidslist = availablestockIDs[int(PALLAREL_ID)*len(availablestockIDs)//int(PALLAREL_NUM):min((int(PALLAREL_ID)+1)*len(availablestockIDs)//int(PALLAREL_NUM), len(availablestockIDs))]

    getcurrentprice(availablestockidslist)

    logging.info("end")
    logging.info(stock_price_dic)

    stock_price_dic.clear()

    return
    

if __name__ == "__main__":
    getCurrentStockPrice()

