import os, re, time, datetime, logging, bisect

from urllib.request import build_opener, HTTPCookieProcessor
from urllib.parse import urlencode
from http.cookiejar import CookieJar

formatter = '%(levelname)s : %(asctime)s : %(message)s'
logging.basicConfig(level=logging.INFO, format=formatter)

TRADE_PWD = os.environ.get("TRADE_PWD")
LOGIN_ID = os.environ.get("LOGIN_ID")
LOGIN_PASS = os.environ.get("LOGIN_PASS")
LOGIN_PAGE_ID = os.environ.get("LOGIN_PAGE_ID")
LOGIN_CONTROL_ID = os.environ.get("LOGIN_CONTROL_ID")
GET_PRICE_PAGE_ID = os.environ.get("GET_PRICE_PAGE_ID")
GET_PRICE_DATA_STORE_ID = os.environ.get("GET_PRICE_DATA_STORE_ID")
GET_PRICE_CONTROL_ID = os.environ.get("GET_PRICE_CONTROL_ID")
GET_BUYING_POWER_PAGE_ID = os.environ.get("GET_BUYING_POWER_PAGE_ID")
GET_BUYING_POWER_DATA_STORE_ID = os.environ.get("GET_BUYING_POWER_DATA_STORE_ID")
GET_BUYING_POWER_CONTROL_ID = os.environ.get("GET_BUYING_POWER_CONTROL_ID")
GET_STOCK_HOLDINGS_PAGE_ID = os.environ.get("GET_STOCK_HOLDINGS_PAGE_ID")
GET_STOCK_HOLDINGS_DATA_STORE_ID = os.environ.get("GET_STOCK_HOLDINGS_DATA_STORE_ID")
GET_STOCK_HOLDINGS_CONTROL_ID = os.environ.get("GET_STOCK_HOLDINGS_CONTROL_ID")
BUY_ORDER_PAGE_ID = os.environ.get("BUY_ORDER_PAGE_ID")
BUY_ORDER_CONTROL_ID = os.environ.get("BUY_ORDER_CONTROL_ID")
SELL_ORDER_PAGE_ID = os.environ.get("SELL_ORDER_PAGE_ID")
SELL_ORDER_CONTROL_ID = os.environ.get("SELL_ORDER_CONTROL_ID")
ORDER_CANCEL_PAGE_ID = os.environ.get("BUY_ORDER_CANCEL_PAGE_ID")
ORDER_CANCEL_CONTROL_ID = os.environ.get("BUY_ORDER_CANCEL_CONTROL_ID")

global fee_per_order_tuple, fee_per_order_ref_tuple
fee_per_order_tuple = (())
fee_per_order_ref_tuple = tuple([])


class Trader():
    def __init__(self):
        self.stock_id = os.environ.get("STOCK_ID")

        self.login_url = ""
        self.get_price_url = ""
        self.get_buying_power_url = ""
        self.get_stock_holdings_url = ""
        self.buy_order_url = ""
        self.sell_order_url = ""
        self.order_cancel_url = ""

        self.price = -1
        self.price_movement = None
        self.price_movement_limit = None
        self.buying_power = -1
        self.order_unit = None
        self.fee_per_order = -1

        self.order_num = -1
        self.ec_order_no = -1

        self.buy_order_quantity = -1
        self.buy_order_trigger_price = None

        self.sell_order_quantity = -1
        self.sell_order_trigger_price = None

        self.satisfied_buy_order_condition = False
        self.satisfied_market_order_sell_order_condition = False

        self.successed_buy_order = False
        self.successed_buy_order_cancel = False
        self.successed_buy_trade = False
        self.successed_initial_sell_order = False
        self.successed_initial_sell_trade = False
        self.successed_market_order_sell_order = False
        self.successed_sell_order_cancel = False
        self.successed_market_order_sell_trade = False

        self.login_post_data = {
            "_PageID": LOGIN_PAGE_ID,
            "_ControlID": LOGIN_CONTROL_ID,
            "user_id": LOGIN_ID,
            "user_password": LOGIN_PASS
        }

        self.get_price_post_data = {
            "_PageID": GET_PRICE_PAGE_ID,
            "_DataStoreID": GET_PRICE_DATA_STORE_ID,
            "_ControlID": GET_PRICE_CONTROL_ID,
            "i_stock_sec": self.stock_id
        }

        self.get_buying_power_post_data = {
            "_PageID": GET_BUYING_POWER_PAGE_ID,
            "_DataStoreID": GET_BUYING_POWER_DATA_STORE_ID,
            "_ControlID": GET_BUYING_POWER_CONTROL_ID,
        }

        self.buy_order_post_data = {
            "_PageID": BUY_ORDER_PAGE_ID,
            "_ControlID": BUY_ORDER_CONTROL_ID,
            "stock_sec_code": self.stock_id,
            "input_quantity": str(self.buy_order_quantity),
            "input_trigger_price": str(self.buy_order_trigger_price),
            "trade_pwd": TRADE_PWD
        }

        self.initial_sell_order_post_data = {
            "_PageID": SELL_ORDER_PAGE_ID,
            "_ControlID": SELL_ORDER_CONTROL_ID,
            "stock_sec_code": self.stock_id,
            "input_quantity": str(self.sell_order_quantity),
            "input_trigger_price": str(self.sell_order_trigger_price),
            "trade_pwd": TRADE_PWD,
        }

        self.market_order_sell_order_post_data = {
            "_PageID": SELL_ORDER_PAGE_ID,
            "_ControlID": SELL_ORDER_CONTROL_ID,
            "stock_sec_code": self.stock_id,
            "input_quantity": str(self.sell_order_quantity),
            "trade_pwd": TRADE_PWD,
        }

        self.order_cancel_post_data = {
            "_PageID": ORDER_CANCEL_PAGE_ID,
            "_ControlID": ORDER_CANCEL_CONTROL_ID,
            "trade_pwd": TRADE_PWD 
        }

        self.get_stock_holdings_post_data = {
            "_ControlID":GET_STOCK_HOLDINGS_CONTROL_ID,
            "_PageID":GET_STOCK_HOLDINGS_PAGE_ID,
            "_DataStoreID": GET_STOCK_HOLDINGS_DATA_STORE_ID
        }


    def get_price(self):
        self.price = -1
        self.price_movement = None

        opener = build_opener(HTTPCookieProcessor(CookieJar())) 

        urlencoded_login_data = urlencode(self.login_post_data).encode('utf-8')
        try:
            res = opener.open(self.login_url, urlencoded_login_data)
        except:
            logging.warning("failed to login")
            exit("Failed to login.")

        urlencoded_get_price_post_data = urlencode(self.get_price_post_data).encode('utf-8')
        try:
            res = opener.open(self.get_price_url, urlencoded_get_price_post_data)
            html = res.read()
            shift = html.decode('Shift_JIS')
        except:
            logging.warning("failed to get price")

        try:
            price = re.search(r"(?<=現在値)[\"\'\-\+=><\(\)/0-9A-Za-z\n\r_&;:., ]*[0-9]*\,?[0-9]+\.?[0-9]*(?=</span>)",shift)
            price = re.search(r"[0-9]*\,?[0-9]+\.?[0-9]*$",price.group())
            self.price = float(price.group().replace(",", ""))

            logging.info("Success to get price {}".format(self.price))
        except:
            logging.warning("failed to parse price from response data")
            self.price = -1
            return

        try:
            price_movement = re.search(r"(?<=前日比)[\"\'\-\+=><\(\)/0-9A-Za-z\n\r&;:., ]*[\+\-]?[0-9]*\,?[0-9]+\.?[0-9]*(?=</font>)",shift)
            price_movement = re.search(r"[\+\-]?[0-9]*\,?[0-9]+\.?[0-9]*$",price_movement.group())
            self.price_movement = float(price_movement.group().replace(",", ""))

            logging.info("Success to get price movement {}".format(self.price_movement))
        except:
            logging.warning("failed to parse price movement from response data")
            self.price_movement = None
            return

        if self.order_unit is None:
            try:
                order_unit = re.search(r"(?<=売買単位)[\"\'\-\+=><\(\)/0-9A-Za-z\n\r&;:., ]*[0-9]+(?=</span>)",shift)
                order_unit = re.search(r"[0-9]+$",order_unit.group())
                self.order_unit = float(order_unit.group())

                logging.info("Success to get order unit {}".format(self.order_unit))
            except:
                logging.warning("failed to parse order unit from response data")
                self.order_unit = None
                return

        return


    def set_price_movement_limit(self):
        price_movement_limit_tuple = (())
        ls = []
        plindex = bisect.bisect_left(ls, self.price-self.price_movement)
        self.price_movement_limit = price_movement_limit_tuple[plindex][1]
        return


    def get_buying_power(self):
        opener = build_opener(HTTPCookieProcessor(CookieJar())) 

        urlencoded_login_data = urlencode(self.login_post_data).encode('utf-8')
        try:
            res = opener.open(self.login_url, urlencoded_login_data)
        except:
            logging.warning("failed to login")
            exit("Failed to login.")

        urlencoded_get_buying_power_post_data = urlencode(self.get_buying_power_post_data).encode('utf-8')
        try:
            res = opener.open(self.get_buying_power_url, urlencoded_get_buying_power_post_data)
            html = res.read()
            shift = html.decode('Shift_JIS')
        except:
            logging.warning("failed to get buying power")

        try:
            buying_power = re.search(r"(?<=買付余力\(2営業日後\))[\"\'=></0-9A-Za-z\n\r ]*[0-9]*\,?[0-9]*\,?[0-9]+\.?[0-9]*(?=&nbsp;)",shift)
            buying_power = re.search(r"[0-9]*\,?[0-9]*\,?[0-9]+\.?[0-9]*$",buying_power.group())
            self.buying_power = float(buying_power.group().replace(",", ""))

            logging.info("Success to get buying power {}".format(self.buying_power))

            self.set_fee_per_order()
        except:
            logging.warning("failed to parse buying power from response data")
            self.buying_power = -1
            self.fee_per_order = -1

        return

    
    def set_fee_per_order(self):
        ind = bisect.bisect_left(fee_per_order_ref_tuple, self.buying_power)
        self.fee_per_order = fee_per_order_tuple[ind][1]
        return


    def buy_monitor(self):
        while 0 <= datetime.datetime.now().hour < 6:
            self.get_price()
            if self.price < 0:
                continue
            if self.price_movement is None:
                continue
            if self.order_unit is None:
                continue

            if self.price_movement_limit is None:
                self.set_price_movement_limit()

            assert self.price >= 0, "ERROR: stock price have not gotten yet"
            assert self.price_movement is not None, "ERROR: stock price movement have not gotten yet"
            assert self.price_movement_limit is not None, "ERROR: stock price movement limit have not set yet"
            assert self.order_unit is not None, "ERROR: stock order unit is None"

            self.get_buying_power()

            if self.buying_power < 0:
                continue

            assert self.buying_power >= 0, "ERROR: buying power have not gotten yet"

            if self.buying_power < int(self.price - self.price_movement + self.price_movement_limit) * self.order_unit:
                logging.warning("I don't have enough buying power to buy {0} stock, but continue to monitor {0} stock".format(self.stock_id))
                time.sleep(10)
                continue

            self.check_buy_order_condition()
            if self.satisfied_buy_order_condition:
                self.buy_order()
                if self.successed_buy_order:
                    self.check_buy_trade()
                    if self.successed_buy_trade:
                        self.sell_monitor()
                        break
            
        return


    def check_buy_order_condition(self):
        return


    def buy_order(self):
        opener = build_opener(HTTPCookieProcessor(CookieJar())) 

        urlencoded_login_data = urlencode(self.login_post_data).encode('utf-8')
        try:
            res = opener.open(self.login_url, urlencoded_login_data)
        except:
            logging.warning("failed to login")
            exit("Failed to login.")

        self.update_buy_order_post_data()
        urlencoded_buy_order_data = urlencode(self.buy_order_post_data).encode('utf-8')
        try:
            res = opener.open(self.buy_order_url, urlencoded_buy_order_data)
            html = res.read()
            shift = html.decode('Shift_JIS')
            order_num = re.search(r"(?<=注文番号)[\"\'\-\+=><\(\)/A-Za-z\n\r&;:. ]*[0-9]*\,?[0-9]*\,?[0-9]+(?=<)",shift)
            order_num = re.search(r"[0-9]*\,?[0-9]*\,?[0-9]+$",order_num.group())
            self.order_num = int(order_num.group().replace(",", ""))

            ec_order_no = re.search(r"(?<=stporder)[_0-9]*[0-9]+(?=\")",shift)
            ec_order_no = re.search(r"[0-9]+$",ec_order_no.group())
            self.ec_order_no = int(ec_order_no.group())

            if self.order_num > 0 and self.ec_order_no > 0: 
                self.successed_buy_order = True
                logging.info("Successed buy order at order No.{}".format(self.order_num))
                logging.info("Successed buy order at ec_order_no: {}".format(self.ec_order_no))
            else: 
                self.successed_buy_order = False
                self.order_num = -1
                self.ec_order_no = -1
                logging.info("failed to buy order")
        except:
            logging.warning("failed to buy order")
            self.order_num = -1
            self.ec_order_no = -1
            self.successed_buy_order = False
        
        return


    def update_buy_order_post_data(self):
        if self.fee_per_order > 0:
            self.buy_order_quantity = int(self.order_unit*((self.buying_power-2*self.fee_per_order)//(self.price - self.price_movement + self.price_movement_limit)))
            self.buy_order_post_data["input_quantity"] = str(self.buy_order_quantity)
        else:
            logging.warning("fee per order is less than 0")

        assert self.buy_order_quantity > 0, "ERROR: buy order quantity is less than 0"

        return


    def check_buy_trade(self):
        while not self.successed_buy_trade and datetime.datetime.now().hour < 6:
            opener = build_opener(HTTPCookieProcessor(CookieJar())) 

            urlencoded_login_data = urlencode(self.login_post_data).encode('utf-8')
            try:
                res = opener.open(self.login_url, urlencoded_login_data)
            except:
                logging.warning("failed to login")
                exit("Failed to login.")

            urlencoded_get_stock_holdings_data = urlencode(self.get_stock_holdings_post_data).encode('utf-8')
            try:
                res = opener.open(self.get_stock_holdings_url, urlencoded_get_stock_holdings_data)
                html = res.read()
                shift = html.decode('Shift_JIS')
                stock_holdings_num = re.findall("(?<=<br>){}(?=&nbsp;)".format(self.stock_id),shift)
                if len(stock_holdings_num):
                    self.successed_buy_trade = True
                    logging.info("Successed buy trade of stock {}".format(self.stock_id))
                    break
                else:
                    logging.info("have not yet done buy trade of stock {}".format(self.stock_id))
            except:
                logging.warning("failed to get stock holdings for check buy trade")
                self.successed_buy_trade = False

            self.get_price()
            if self.price < 0:
                continue
            if self.price_movement is None:
                continue
            if self.order_unit is None:
                continue

            if True: 
                self.buy_order_cancel()
                break
            
        return


    def buy_order_cancel(self):
        opener = build_opener(HTTPCookieProcessor(CookieJar())) 

        urlencoded_login_data = urlencode(self.login_post_data).encode('utf-8')
        try:
            res = opener.open(self.login_url, urlencoded_login_data)
        except:
            logging.warning("failed to login")
            exit("Failed to login.")

        self.update_buy_order_cancel_post_data()
        urlencoded_buy_order_cancel_data = urlencode(self.order_cancel_post_data).encode('utf-8')
        try:
            res = opener.open(self.order_cancel_url, urlencoded_buy_order_cancel_data)
            self.order_num = -1
            self.ec_order_no = -1
            logging.info("buy order was canceled")
        except:
            logging.warning("failed to cancel buy order ")

        return

    
    def update_buy_order_cancel_post_data(self):
        self.order_cancel_post_data["ec_order_no"] = str(self.ec_order_no)
        return


    def sell_monitor(self):
        self.initial_sell_order()
        if self.successed_initial_sell_order:
            while datetime.datetime.now().hour < 6:
                self.check_initial_sell_trade()
                if self.successed_initial_sell_trade:
                    break
                
                self.get_price()
                if self.price < 0:
                    continue
                if self.order_unit is None:
                    continue

                assert self.price >= 0, "ERROR: Can't get stock price"
                assert self.order_unit is not None, "ERROR: order unit is None"

                self.check_market_order_sell_order_condition()
                if self.satisfied_market_order_sell_order_condition:
                    self.initial_sell_order_cancel()
                    time.sleep(10)
                    self.market_order_sell_order()
                    if self.successed_market_order_sell_order:
                        self.check_market_order_sell_trade()
                        if self.successed_market_order_sell_trade:
                            logging.info("Trade of stock {} finished completely!".format(self.stock_id))
                            break
                    
        return


    def initial_sell_order(self):
        opener = build_opener(HTTPCookieProcessor(CookieJar())) 

        urlencoded_login_data = urlencode(self.login_post_data).encode('utf-8')
        try:
            res = opener.open(self.login_url, urlencoded_login_data)
        except:
            logging.warning("failed to login")
            exit("Failed to login.")

        self.update_initial_sell_order_post_data()
        urlencoded_initial_sell_order_data = urlencode(self.initial_sell_order_post_data).encode('utf-8')
        try:
            res = opener.open(self.sell_order_url, urlencoded_initial_sell_order_data)
            html = res.read()
            shift = html.decode('Shift_JIS')
            order_num = re.search(r"(?<=注文番号)[\"\'\-\+=><\(\)/A-Za-z\n\r&;:. ]*[0-9]*\,?[0-9]*\,?[0-9]+(?=<)",shift)
            order_num = re.search(r"[0-9]*\,?[0-9]*\,?[0-9]+$",order_num.group())
            self.order_num = int(order_num.group().replace(",", ""))
            logging.info("Successed initial sell order at order No.{}".format(self.order_num))

            if self.order_num > 0 and self.ec_order_no > 0: 
                self.successed_initial_sell_order = True
                logging.info("Successed initial sell order at ec_order_no: {}".format(self.ec_order_no))
            else: 
                self.successed_initial_sell_order = False
                self.order_num = -1
                self.ec_order_no = -1
                logging.info("failed to do initial sell order")
        except:
            logging.warning("failed to do initial sell order")
            self.order_num = -1
            self.ec_order_no = -1
            self.successed_initial_sell_order = False

        return


    def update_initial_sell_order_post_data(self):
        self.sell_order_quantity = int(self.buy_order_quantity)

        assert self.sell_order_quantity > 0, "ERROR: sell order quantity is less than 0"
        self.initial_sell_order_post_data["input_quantity"] = str(self.sell_order_quantity)

        return

    
    def check_initial_sell_trade(self):
        opener = build_opener(HTTPCookieProcessor(CookieJar())) 

        urlencoded_login_data = urlencode(self.login_post_data).encode('utf-8')
        try:
            res = opener.open(self.login_url, urlencoded_login_data)
        except:
            logging.warning("failed to login")
            exit("Failed to login.")

        urlencoded_get_stock_holdings_data = urlencode(self.get_stock_holdings_post_data).encode('utf-8')
        try:
            res = opener.open(self.get_stock_holdings_url, urlencoded_get_stock_holdings_data)
            html = res.read()
            shift = html.decode('Shift_JIS')
            stock_holdings_num = re.findall("(?<=<br>){}(?=&nbsp;)".format(self.stock_id),shift)
            if not len(stock_holdings_num):
                self.successed_initial_sell_trade = True
                logging.info("Successed initial sell trade of stock {}".format(self.stock_id))
            else:
                self.successed_initial_sell_trade = False
                logging.info("have not yet done initial sell trade of stock {}".format(self.stock_id))
        except:
            logging.warning("failed to get stock holdings for check initital sell trade")
            self.successed_initail_sell_trade = False

        return


    def check_market_order_sell_order_condition(self):
        return


    def initial_sell_order_cancel(self):
        opener = build_opener(HTTPCookieProcessor(CookieJar())) 

        urlencoded_login_data = urlencode(self.login_post_data).encode('utf-8')
        try:
            res = opener.open(self.login_url, urlencoded_login_data)
        except:
            logging.warning("failed to login")
            exit("Failed to login.")

        self.update_initial_sell_order_cancel_post_data()
        urlencoded_initial_sell_order_cancel_data = urlencode(self.order_cancel_post_data).encode('utf-8')
        try:
            res = opener.open(self.order_cancel_url, urlencoded_initial_sell_order_cancel_data)
            self.order_num = -1
            self.ec_order_no = -1
            logging.info("initial sell order was canceled")
        except:
            logging.warning("failed to cancel initial sell order ")

        return

    
    def update_initial_sell_order_cancel_post_data(self):
        return


    def market_order_sell_order(self):
        opener = build_opener(HTTPCookieProcessor(CookieJar())) 

        urlencoded_login_data = urlencode(self.login_post_data).encode('utf-8')
        try:
            res = opener.open(self.login_url, urlencoded_login_data)
        except:
            logging.warning("failed to login")
            exit("Failed to login.")

        self.update_market_order_sell_order_post_data()
        urlencoded_market_order_sell_order_data = urlencode(self.market_order_sell_order_post_data).encode('utf-8')
        try:
            res = opener.open(self.sell_order_url, urlencoded_market_order_sell_order_data)
            html = res.read()
            shift = html.decode('Shift_JIS')
            order_num = re.search(r"(?<=注文番号)[\"\'\-\+=><\(\)/A-Za-z\n\r&;:. ]*[0-9]*\,?[0-9]*\,?[0-9]+(?=<)",shift)
            order_num = re.search(r"[0-9]*\,?[0-9]*\,?[0-9]+$",order_num.group())
            self.order_num = int(order_num.group().replace(",", ""))
            logging.info("Successed market order sell order at order No.{}".format(self.order_num))

            if self.order_num > 0 and self.ec_order_no > 0: 
                self.successed_market_order_sell_order = True
                logging.info("Successed market order sell order at ec_order_no: {}".format(self.ec_order_no))
            else: 
                self.successed_market_order_sell_order = False
                self.order_num = -1
                self.ec_order_no = -1
                logging.info("failed to do market order sell order")
        except:
            logging.warning("failed to do market order sell order")
            self.successed_market_order_sell_order = False
            self.order_num = -1
            self.ec_order_no = -1

        return


    def update_market_order_sell_order_post_data(self):
        self.sell_order_quantity = int(self.buy_order_quantity)

        assert self.sell_order_quantity > 0, "ERROR: sell order quantity is less than 0"
        self.market_order_sell_order_post_data["input_quantity"] = str(self.sell_order_quantity)

        return


    def check_market_order_sell_trade(self):
        while not self.successed_market_order_sell_trade and datetime.datetime.now().hour < 6:
            opener = build_opener(HTTPCookieProcessor(CookieJar())) 

            urlencoded_login_data = urlencode(self.login_post_data).encode('utf-8')
            try:
                res = opener.open(self.login_url, urlencoded_login_data)
            except:
                logging.warning("failed to login")
                exit("Failed to login.")

            urlencoded_get_stock_holdings_data = urlencode(self.get_stock_holdings_post_data).encode('utf-8')
            try:
                res = opener.open(self.get_stock_holdings_url, urlencoded_get_stock_holdings_data)
                html = res.read()
                shift = html.decode('Shift_JIS')
                stock_holdings_num = re.findall("(?<=<br>){}(?=&nbsp;)".format(self.stock_id),shift)
                if not len(stock_holdings_num):
                    self.successed_market_order_sell_trade = True
                    logging.info("Successed market order sell trade of stock {}".format(self.stock_id))
                    break
                else:
                    self.successed_market_order_sell_trade = False
                    logging.info("have not yet done market order sell trade of stock {}".format(self.stock_id))
            except:
                logging.warning("failed to get stock holdings for check market order sell trade")
                self.successed_market_order_sell_trade = False

        return


    def market_order_sell_order_cancel(self):
        opener = build_opener(HTTPCookieProcessor(CookieJar())) 

        urlencoded_login_data = urlencode(self.login_post_data).encode('utf-8')
        try:
            res = opener.open(self.login_url, urlencoded_login_data)
        except:
            logging.warning("failed to login")
            exit("Failed to login.")

        self.update_market_order_sell_order_cancel_post_data()
        urlencoded_market_order_sell_order_cancel_data = urlencode(self.order_cancel_post_data).encode('utf-8')
        try:
            res = opener.open(self.order_cancel_url, urlencoded_market_order_sell_order_cancel_data)
            logging.info("market order sell order was canceled")
        except:
            logging.warning("failed to cancel market order sell order ")
            self.order_num = -1
            self.ec_order_no = -1

        return


    def update_market_order_sell_order_cancel_post_data(self):
        return


    def trade(self):
        logging.info("start")
        self.buy_monitor()
        logging.info("end")

        return
    

if __name__ == "__main__":
    trader = Trader()
    trader.trade()
