      
import datetime
import time
import pandas as pd
import MetaTrader5 as mt5
import numpy as np
import statistics
import pytz
import requests
from bs4 import BeautifulSoup
import investpy
import ta
import math
import telebot
import pandas_ta

# pip install requests beautifulsoup4

TOKEN = 'yourtoken1'

# bot = telebot.TeleBot(TOKEN)


# def send_message_to_channel(message):

#     channel_id = '@yourChannelid'
#     bot.send_message(channel_id, message)


# @bot.message_handler(func=lambda message: True)
# def echo_all(message):
  
#     send_message_to_channel(message.text)



# Total positions
def total_positons():
    positions_total=mt5.positions_total()
    return positions_total



# Total positions
def total_orders():
    orders_total=mt5.orders_get()
    return orders_total



# balance
def balance():
    balance = mt5.account_info()._asdict()['balance']
    return balance


# profit
def profit():
    positions = mt5.positions_get()
    profit = 0
    for position in positions:
        profit += position._asdict()['profit']
    return profit



# kandel
def kandel(timeframe='30m', limit=10 , symbol = 'BTCUSD.'):
       
    symbol = symbol
    if timeframe == '5m':
        time = mt5.TIMEFRAME_M5
    if timeframe == '3m':
        time = mt5.TIMEFRAME_M3
    if timeframe == '1m':
        time = mt5.TIMEFRAME_M1
    if timeframe == '2m':
        time = mt5.TIMEFRAME_M2
    if timeframe == '15m':
        time = mt5.TIMEFRAME_M15
    if timeframe == '30m':
        time = mt5.TIMEFRAME_M30
    if timeframe == '1h':
        time = mt5.TIMEFRAME_H1
    if timeframe == '4h':
        time = mt5.TIMEFRAME_H4
    if timeframe == '1d':
        time = mt5.TIMEFRAME_D1
    if timeframe == '1w':
        time = mt5.TIMEFRAME_W1
    if timeframe == '1mn':
        time = mt5.TIMEFRAME_MN1
    candles = mt5.copy_rates_from_pos(symbol, time, 0, limit)
    df = pd.DataFrame(candles, columns=['time', 'open', 'high', 'low', 'close'])
    return df.iloc




#rsi
def rsi(timeframe,symbol):

    ohlc = kandel(timeframe , 14*10 , symbol)
    candles = pd.DataFrame(ohlc[:])
    candles['rsi'] = ta.momentum.RSIIndicator(candles['close'], window=14).rsi()
    rsi= candles['rsi'].tolist()
    return rsi[-1]



# lot
def qty(myBalance):
    if myBalance < 300:
        lot =  0.01
        return lot
    elif myBalance >= 300 and myBalance <= 499:
        lot =  0.02
        return lot
    elif myBalance >= 500 and myBalance <= 999:
        lot = 0.03
        return lot
    elif myBalance >= 1000 and myBalance <= 1499:
        lot = 0.04
        return lot
    elif myBalance >= 1500 and myBalance <= 1999:
        lot = 0.05
        return lot
    elif myBalance >= 2000 and myBalance <= 2499:
        lot = 0.06
        return lot
    elif myBalance >= 2500 and myBalance <= 2999:
        lot = 0.07
        return lot
    elif myBalance >= 3000 and myBalance <= 3999:
        lot = 0.08
        return lot
    elif myBalance >= 4000 and myBalance <= 5000:
        lot = 0.09
        return lot
    elif myBalance > 5000:
        lot = 0.1
        return lot
    


# create_order
def create_order(symbol , lot , order_type , price , sl , tp , comment):
    symbol_info = mt5.symbol_info(symbol)
    filling_mode = symbol_info.filling_mode
    if filling_mode == 1:
        filling_mode = mt5.ORDER_FILLING_FOK
    elif filling_mode == 2:
        filling_mode = mt5.ORDER_FILLING_IOC
    elif filling_mode != 1 and filling_mode != 2:
        filling_mode = mt5.ORDER_FILLING_FOK or mt5.ORDER_FILLING_IOC

    request={
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl" : sl,
        "tp" : tp,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling":filling_mode,
        }
    order = mt5.order_send(request)
    return order



#close_order
def close_order(symbol , lot , order_type , price , ticket):
    filling_modes = [mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN]

    for filling_mode in filling_modes:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 0,
            "comment": "Close position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        result = mt5.order_send(request)




# pending_order
def pending_order(symbol , lot , order_type , price , sl , tp , comment):
    request={
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl" : sl,
        "tp" : tp,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
        }
    order = mt5.order_send(request)
    return order


#remove pending order
def remove_order(symbol , ticket):
    request={
        "action": mt5.TRADE_ACTION_REMOVE,
        "symbol": symbol,
        "order": ticket,
    }
    order = mt5.order_send(request)
    return order




#close_all_positions
def close_all_positions():
    positions = mt5.positions_get()
    if positions is None:
        pass

    for position in positions:

        p_symbol = position._asdict()['symbol']
        p_ticket = position._asdict()['ticket']
        p_lot = position._asdict()['volume']
        if position._asdict()['type'] == 0 :
            #buy
            order_type = mt5.ORDER_TYPE_SELL
            p = mt5.symbol_info_tick(p_symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            p = mt5.symbol_info_tick(p_symbol).ask

        close_order(p_symbol , p_lot , order_type , p , p_ticket)

   

#close_half_positions
def close_half_positions():
    positions = mt5.positions_get()
    if positions is None or len(positions) == 0:
        return

    # نصف تعداد پوزیشن‌ها را محاسبه می‌کنیم
    half_count = len(positions) // 2

    for i, position in enumerate(positions):
        if i >= half_count:
            break
        
        p_symbol = position._asdict()['symbol']
        p_ticket = position._asdict()['ticket']
        p_lot = position._asdict()['volume']
        if position._asdict()['type'] == 0 :
            #buy
            order_type = mt5.ORDER_TYPE_SELL
            p = mt5.symbol_info_tick(p_symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            p = mt5.symbol_info_tick(p_symbol).ask

        close_order(p_symbol , p_lot , order_type , p , p_ticket)








def close_half_with_comment(comment):
  
    positions = mt5.positions_get()
    
    positions_with_comment = [pos for pos in positions if pos.comment == comment]
    
    half_count = len(positions_with_comment) // 2

    for i, position in enumerate(positions_with_comment):
        if i >= half_count:
            break
         
        p_symbol = position._asdict()['symbol']
        p_ticket = position._asdict()['ticket']
        p_lot = position._asdict()['volume']
        if position._asdict()['type'] == 0 :
            #buy
            order_type = mt5.ORDER_TYPE_SELL
            p = mt5.symbol_info_tick(p_symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            p = mt5.symbol_info_tick(p_symbol).ask

        close_order(p_symbol , p_lot , order_type , p , p_ticket)


      



def close_all_with_comment(comment):
  
    positions = mt5.positions_get()
    
    positions_with_comment = [pos for pos in positions if pos.comment == comment]
    
    for position in positions_with_comment :
         
        p_symbol = position._asdict()['symbol']
        p_ticket = position._asdict()['ticket']
        p_lot = position._asdict()['volume']
        if position._asdict()['type'] == 0 :
            #buy
            order_type = mt5.ORDER_TYPE_SELL
            p = mt5.symbol_info_tick(p_symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            p = mt5.symbol_info_tick(p_symbol).ask

        close_order(p_symbol , p_lot , order_type , p , p_ticket)


      





# moving average 26
def average26(timeframe , symbol ='BTCUSD.'):
        
    ohlc = kandel(timeframe , limit=26 , symbol = symbol)
    average = statistics.mean(item['low'] for item in ohlc)
    return average


# moving average 12
def average12(timeframe , symbol ='BTCUSD.'):
        
    ohlc = kandel(timeframe , limit=12 , symbol = symbol)
    average = statistics.mean(item['close'] for item in ohlc)
    return average


# moving average 50
def average50(timeframe , symbol ='BTCUSD.'):
        
    ohlc = kandel(timeframe , limit=50 , symbol = symbol)
    average = statistics.mean(item['close'] for item in ohlc)
    return average


# moving average 60
def average60(timeframe , symbol ='BTCUSD.'):
        
    ohlc = kandel(timeframe , limit=60 , symbol = symbol)
    average = statistics.mean(item['close'] for item in ohlc)
    return average


# moving average 162
def average162(timeframe , symbol ='BTCUSD.'):
        
    ohlc = kandel(timeframe , limit=162 , symbol = symbol)
    average = statistics.mean(item['close'] for item in ohlc)
    return average


# moving average 100
def average100(timeframe , symbol ='BTCUSD.'):
        
    ohlc = kandel(timeframe , limit=100 , symbol = symbol)
    average = statistics.mean(item['close'] for item in ohlc)
    return average



# moving average 200
def average200(timeframe , symbol ='BTCUSD.'):
        
    ohlc = kandel(timeframe , limit=200 , symbol = symbol)
    average = statistics.mean(item['close'] for item in ohlc)
    return average



# long or short
def whatKandel(timeframe = '30m' , candle = -1 , symbol ='BTCUSD.'):
    ohlc = kandel(timeframe , limit=10 , symbol = symbol)
    if ohlc[candle]['open'] > ohlc[candle]['close']:
        return 'short'
    else:
        return 'long'
    


def isBeta(timeframe , candel , symbol ='BTCUSD.' , m = 50):
    kandels = kandel(timeframe , limit=10 , symbol = symbol)
    res = kandels[candel]
    if res['open'] > res['close']:
        # short kandel
        if res['open'] == res['high'] and (res['close'] - res['low']) <= res['open'] - res['close'] and body(timeframe , candel ,symbol ) >= m :
            return True
        else:
            return False
    elif res['open'] < res['close']:
        # long kandel
        if res['open'] == res['low']  and (res['high'] - res['close']) <= res['close'] - res['open'] and body(timeframe , candel ,symbol ) >= m :
            return True
        else:
            return False
    else:
        return False
    


def gap(timeframe , symbol ='BTCUSD.'):
    kandels = kandel(timeframe , limit=5 , symbol = symbol)
    #long
    if kandels[-1]['open'] > kandels[-2]['close'] and whatKandel(timeframe , -1 , symbol) == 'long':
        return True
    #short
    if kandels[-1]['open'] < kandels[-2]['close'] and whatKandel(timeframe , -1 , symbol) == 'short':
        return True
    else:
        return False
    



def isBack(timeframe , candel , upOrDown , symbol ='BTCUSD.'):
    kandels = kandel(timeframe , limit=10 , symbol = symbol)
    res = kandels[candel]
    if res['open'] > res['close']:
        # short kandel
        if upOrDown == 'up'and (res['open'] - res['close'])*3 < res['high'] - res['open'] and (res['close'] - res['low']) * 3 <= res['high'] - res['open'] :
            return True
        
        elif upOrDown == 'down'and (res['open'] - res['close'])*4 < res['close'] - res['low'] and (res['high'] - res['open'])*3 <= res['close'] - res['low'] :
            return True
        else:
            return False
        
    elif res['open'] < res['close']:
        # long kandel
        if upOrDown == 'up'and (res['close'] - res['open'])*4 < res['high'] - res['close'] and res['high'] - res['close'] > (res['open'] - res['low'])*3 :
            return True
        
        elif upOrDown == 'down'and (res['close'] - res['open'])*3 < res['open'] - res['low'] and (res['high'] - res['close'])*3 < res['open'] - res['low']:
            return True
        
        else:
            return False
    else:
        return False



def body(timeframe , candel , symbol ='BTCUSD.'):
    kandels = kandel(timeframe , limit=10 , symbol = symbol)
    res = kandels[candel]
    if res['open'] > res['close']:
        # short kandel
        body = res['open'] - res['close']
        return body
        
    elif res['open'] < res['close']:
        # long kandel
        body = res['close'] - res['open']
        return body
    else:
        return 0
    


def check_time(start_hour, end_hour):
    current_time = datetime.datetime.now(datetime.UTC).time()
    if current_time.hour >= start_hour and current_time.hour <= end_hour:
        return True
    else:
        return False
    



def check_time_min(start_hour, start_minute, end_hour, end_minute):

    current_time = datetime.datetime.now(datetime.UTC).time()
   
    start_time = datetime.time(start_hour, start_minute)
    end_time = datetime.time(end_hour, end_minute)
    
    if start_time <= current_time <= end_time:
        return True
    else:
        return False





def hemayat(symbol):
    kandeld = kandel('1d' , 5 , symbol )
    kandelw = kandel('1w' , 5 , symbol )
    kande4h = kandel('4h' , 5 , symbol )
    kande1h = kandel('1h' , 5 , symbol )
    lines = [kandeld[-2]['high'] , kandeld[-2]['low'] , kandelw[-1]['high'] , kandelw[-1]['low'] , kandelw[-2]['high'] , kandelw[-2]['low'] , kande4h[-2]['high'] , kande4h[-2]['low'] , kande1h[-2]['high'] , kande1h[-2]['low']]
    price = mt5.symbol_info_tick(symbol).ask
    line = []
    for i in lines:
        if i < price:
            line.append(i)
    if len(line) == 0:
        return False
    else:
        return max(line)
        

def moghavemat(symbol):
    kandeld = kandel('1d' , 5 , symbol )
    kandelw = kandel('1w' , 5 , symbol )
    kande4h = kandel('4h' , 5 , symbol )
    kande1h = kandel('1h' , 5 , symbol )
    lines = [kandeld[-2]['high'] , kandeld[-2]['low'] , kandelw[-1]['high'] , kandelw[-1]['low'] , kandelw[-2]['high'] , kandelw[-2]['low'] , kande4h[-2]['high'] , kande4h[-2]['low'] , kande1h[-2]['high'] , kande1h[-2]['low']]
    price = mt5.symbol_info_tick(symbol).ask
    line = []
    for i in lines:
        if i > price:
            line.append(i)
    if len(line) == 0:
        return False
    else:
        return min(line)
        

def session_hemayat(symbol) :

    def get_session(dt):
        if datetime.time(21, 0) <= dt.time() < datetime.time(5, 59):
            return 'sydney'
        elif datetime.time(0, 0) <= dt.time() < datetime.time(8, 59):
            return 'tokyo'
        elif datetime.time(7, 0) <= dt.time() < datetime.time(15, 59):
            return 'londen'
        elif datetime.time(13, 0) <= dt.time() < datetime.time(20, 59):
            return 'new'
        return None

    timezone = mt5.TIMEFRAME_H1
    date_from = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=2)
    date_to = datetime.datetime.now(pytz.UTC)

    rates = mt5.copy_rates_range(symbol, timezone, date_from, date_to)
    if rates is None or len(rates) == 0:
        return False

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)

    df['session'] = df['time'].apply(get_session)
    lines = []

    for session in ['sydney', 'tokyo', 'londen' , 'new']:
        session_data = df[df['session'] == session]
        if not session_data.empty:
            session_high = session_data['high'].max()
            session_low = session_data['low'].min()
            lines.extend([session_high, session_low])

    price = mt5.symbol_info_tick(symbol).ask
    line = []
    for i in lines:
        if i < price:
            line.append(i)
    if len(line) == 0:
        return False
    else:
        return max(line)


def session_moghavemat(symbol) :

    def get_session(dt):
        if datetime.time(21, 0) <= dt.time() < datetime.time(5, 59):
            return 'sydney'
        elif datetime.time(0, 0) <= dt.time() < datetime.time(8, 59):
            return 'tokyo'
        elif datetime.time(7, 0) <= dt.time() < datetime.time(15, 59):
            return 'londen'
        elif datetime.time(13, 0) <= dt.time() < datetime.time(20, 59):
            return 'new'
        return None

    timezone = mt5.TIMEFRAME_H1
    date_from = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=2)
    date_to = datetime.datetime.now(pytz.UTC)

    rates = mt5.copy_rates_range(symbol, timezone, date_from, date_to)
    if rates is None or len(rates) == 0:
        return False

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)

    df['session'] = df['time'].apply(get_session)
    lines = []

    for session in ['sydney', 'tokyo', 'londen' , 'new']:
        session_data = df[df['session'] == session]
        if not session_data.empty:
            session_high = session_data['high'].max()
            session_low = session_data['low'].min()
            lines.extend([session_high, session_low])

    price = mt5.symbol_info_tick(symbol).ask
    line = []
    for i in lines:
        if i > price:
            line.append(i)
    if len(line) == 0:
        return False
    else:
        return min(line)


def fvg(symbol , timeframe):
    kandels = kandel(timeframe , limit=10 , symbol = symbol)
    if kandels[-2]['high'] < kandels[-4]['low'] and whatKandel(timeframe , -2 , symbol) == 'short' and whatKandel(timeframe , -3 , symbol) == 'short' :
        return True
    elif kandels[-2]['low'] > kandels[-4]['high'] and whatKandel(timeframe , -2 , symbol) == 'long' and whatKandel(timeframe , -3 , symbol) == 'long' :
        return True
    else:
        return False
    

def sharp(symbol , timeframe):
    kandels = kandel(timeframe , limit=10 , symbol = symbol)
    if fvg(symbol , timeframe) == True and whatKandel(timeframe , -2 , symbol) == 'short':
        return 'short'
    elif fvg(symbol , timeframe) == True and whatKandel(timeframe , -2 , symbol) == 'long':
        return 'long'
    else: 
        return False


def kijun_sen(symbol ,timeframe ,num):
    kandels = kandel(timeframe =timeframe , limit=num , symbol = symbol)
    high = []
    low = []
    i = -1
    for n in range(num) :
        high.append(kandels[i]['high'])
        low.append(kandels[i]['low'])
        i -= 1
    mini = min(low)
    maxi = max(high)
    sen = (maxi + mini ) / 2 
    return sen



def kijun_sen_befor(symbol ,timeframe ,num):
    x = num + 2
    kandels = kandel(timeframe =timeframe , limit=x , symbol = symbol)
    high = []
    low = []
    i = -3
    for n in range(num) :
        high.append(kandels[i]['high'])
        low.append(kandels[i]['low'])
        i -= 1
    mini = min(low)
    maxi = max(high)
    sen = (maxi + mini ) / 2 
    return sen


def ichi_cross(symbol ,timeframe ,num1 , num2):
    if kijun_sen_befor(symbol ,timeframe ,num1) < kijun_sen_befor(symbol ,timeframe ,num2) and kijun_sen(symbol ,timeframe ,num1) >  kijun_sen(symbol ,timeframe ,num2):
        return 'down to up'
    elif kijun_sen_befor(symbol ,timeframe ,num1) > kijun_sen_befor(symbol ,timeframe ,num2) and kijun_sen(symbol ,timeframe ,num1) <  kijun_sen(symbol ,timeframe ,num2):
        return 'up to down'
    else:
        return False
    
    

def ema20(timeframe,symbol):
    ohlc = kandel(timeframe , 20*10 , symbol = symbol)
    prices = pd.DataFrame(ohlc[:])
    prices['ema'] = prices['close'].ewm(span = 20).mean()
    ema = prices['ema'].values.tolist()
    return (ema)[-1]



def ema50(timeframe,symbol):
    ohlc = kandel(timeframe , 50*10 , symbol = symbol)
    prices = pd.DataFrame(ohlc[:])
    prices['ema'] = prices['close'].ewm(span = 50).mean()
    ema = prices['ema'].values.tolist()
    return (ema)[-1]




def ema100(timeframe,symbol):
    ohlc = kandel(timeframe , 100*10 , symbol = symbol)
    prices = pd.DataFrame(ohlc[:])
    prices['ema'] = prices['close'].ewm(span = 100).mean()
    ema = prices['ema'].values.tolist()
    return (ema)[-1]




def ema200(timeframe,symbol):
    ohlc = kandel(timeframe , 200*10 , symbol = symbol)
    prices = pd.DataFrame(ohlc[:])
    prices['ema'] = prices['close'].ewm(span = 200).mean()
    ema = prices['ema'].values.tolist()
    return (ema)[-1]



def ema(timeframe, window , symbol):
    ohlc = kandel(timeframe , window*10 , symbol = symbol)
    prices = pd.DataFrame(ohlc[:])
    prices['ema'] = prices['close'].ewm(span = window).mean()
    ema = prices['ema'].values.tolist()
    return (ema)[-1]



def ema_all(timeframe, window , symbol):
    ohlc = kandel(timeframe , window*10 , symbol = symbol)
    prices = pd.DataFrame(ohlc[:])
    prices['ema'] = prices['close'].ewm(span = window).mean()
    ema = prices['ema'].values.tolist()
    return ema


#--------------------------------------------------------------------------------
def ema_cross(timeframe, symbol , ema1 , ema2): 
    if \
        ema_all(timeframe , ema1 , symbol)[-2] < ema_all(timeframe , ema2 , symbol)[-2] \
        and ema_all(timeframe , ema1 , symbol)[-1] > ema_all(timeframe , ema2 , symbol)[-1]  :
        
        return "down to up"
    
    elif \
        ema_all(timeframe , ema1 , symbol)[-2] > ema_all(timeframe , ema2 , symbol)[-2] \
        and ema_all(timeframe , ema1 , symbol)[-1] <ema_all(timeframe , ema2 , symbol)[-1] :

        return "up to down"
    
    else : 
            return False
    

    

cache = {
    'news_data': None,
    'last_updated': None
}

def fetch_economic_news():
    url = "https://www.investing.com/economic-calendar/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table', {'id': 'economicCalendarData'})
    rows = table.find_all('tr', {'class': 'js-event-item'})

    news_data = []
    for row in rows:
        date_str = row['data-event-datetime']
        event_time = datetime.datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")

        event_title = row.find('td', {'class': 'left event'}).get_text(strip=True)
        news_data.append({
            'time': event_time,
            'event': event_title
        })

    return news_data

def is_during_important_news(news_data, check_time):
    if check_time.tzinfo is None:
        check_time = check_time.replace(tzinfo=datetime.timezone.utc)

    for news in news_data:
        news_time = news['time']
        if news_time.tzinfo is None:
            news_time = news_time.replace(tzinfo=datetime.timezone.utc)

        if check_time <= news_time < (check_time + datetime.timedelta(minutes=30)):
            return True
    return False

def is_news():
    global cache
    current_time = datetime.datetime.now(datetime.timezone.utc)
    if cache['last_updated'] is None or (current_time - cache['last_updated']).total_seconds() > 1800:
        cache['news_data'] = fetch_economic_news()
        cache['last_updated'] = current_time

    news_data = cache['news_data']
    if is_during_important_news(news_data, current_time):
        return True
    return False




def fibo_long(symbol, timeframe, num):
   
    kandels = kandel(timeframe, num, symbol)
    
    high = [kandels[i]['high'] for i in range(num)]
    low = [kandels[i]['low'] for i in range(num)]
    
    high = max(high)
    low = min(low)

    diff = high - low
    
    levels = {
        "0%": low,
        "23.6%": high - 0.236 * diff,
        "38.2%": high - 0.382 * diff,
        "50%": high - 0.5 * diff,
        "61.8%": high - 0.618 * diff,
        "78.6%": high - 0.786 * diff,
        "100%": high
    }
    
    return levels



def fibo_short(symbol, timeframe, num):
   
    kandels = kandel(timeframe, num, symbol)
    
    high = [kandels[i]['high'] for i in range(num)]
    low = [kandels[i]['low'] for i in range(num)]
    
    high = max(high)
    low = min(low)
    diff = high - low
    
    levels = {
        "0%":low ,
        "78.6%": high - 0.236 * diff,
        "61.8%": high - 0.382 * diff,
        "50%": high - 0.5 * diff,
        "38.2%": high - 0.618 * diff,
        "23.6%": high - 0.786 * diff,
        "100%": high
    }
    
    return levels




# ایا داخل نماد بیت کوین در صد سفارش اخر میزان ده بیت کوین به بالا در فروشنده ها هست؟؟ اگر هست بیشترینش چقدره
def order_book(symbol, limit=100 , volume=10 , bidsOrasks = 'bids'):
    url = f'https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        bids = [[float(order[0]), float(order[1])] for order in data['bids']]
        asks = [[float(order[0]), float(order[1])] for order in data['asks']]

        def filter_large_orders(orders, volume):
            return [order for order in orders if order[1] >= volume]
        
        large_bids = filter_large_orders(bids, volume)
        large_asks = filter_large_orders(asks, volume)

        if bidsOrasks == 'bids' and large_bids != []:
            return max(large_bids)[0]
        elif bidsOrasks == 'asks' and large_asks != []:
            return min(large_asks)[0]
        else:
            pass
    else:
        
        return None




def order_book_signal(symbol):
    limit = 1000
    url = f'https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        bids = data['bids']
        asks = data['asks']
        bids_vol = []
        asks_vol = []
        for bid in bids :
            bids_vol.append(float(bid[1]))
           
        for ask in asks :
            asks_vol.append(float(ask[1]))
           
        if sum(asks_vol) > sum(bids_vol):
            return 'short'
        elif sum(bids_vol) > sum(asks_vol):
            return 'long'
        else:
            return None
    else:
        
        return None



#Bollinger Band Algorithm
def BB(timeframe, window , symbol, num_std_dev=2):
    
    ohlc = kandel(timeframe , limit=window , symbol = symbol)  
    
    
    SMA = statistics.mean(item['low'] for item in ohlc)
 
    SD = statistics.stdev(item['low'] for item in ohlc)
   
    UB = SMA + (num_std_dev * SD)
   
    LB = SMA - (num_std_dev * SD)
    
    
    return [SMA,UB,LB]


def time_high_low(symbol, start_hour, start_minute, timeframe_str, num_candles, time_offset_minutes=0):

    today = datetime.datetime.now(datetime.timezone.utc).date()

    start_time = datetime.datetime(today.year, today.month, today.day, start_hour, start_minute, 0, tzinfo=datetime.timezone.utc)
    start_time = start_time + datetime.timedelta(minutes=time_offset_minutes)

    def parse_timeframe(timeframe_str):
        tf_map = {
            '1m': (mt5.TIMEFRAME_M1, 1),
            '3m': (mt5.TIMEFRAME_M3, 3),
            '5m': (mt5.TIMEFRAME_M5, 5),
            '15m': (mt5.TIMEFRAME_M15, 15),
            '30m': (mt5.TIMEFRAME_M30, 30),
            '1h': (mt5.TIMEFRAME_H1, 60),
            '4h': (mt5.TIMEFRAME_H4, 240),
            '1d': (mt5.TIMEFRAME_D1, 1440),
            '1w': (mt5.TIMEFRAME_W1, 10080),
            '1mn': (mt5.TIMEFRAME_MN1, 43200)
        }

        return tf_map.get(timeframe_str.lower(), (None, None))

    timeframe, timeframe_minutes = parse_timeframe(timeframe_str)

    end_time = start_time + datetime.timedelta(minutes=timeframe_minutes * num_candles)

    rates = mt5.copy_rates_range(symbol, timeframe, start_time, end_time)

    if rates is None or len(rates) == 0:
        return False

    data = pd.DataFrame(rates)
    data['time'] = pd.to_datetime(data['time'], unit='s')
    data = data.sort_values(by='time')

    selected_candles = data.head(num_candles)

    highest_point = selected_candles['high'].max()
    lowest_point = selected_candles['low'].min()


    return {
        'high': highest_point,
        'low': lowest_point
    }




def modify_position(ticket, new_stop_loss):

    position = mt5.positions_get(ticket=ticket)
    if not position:
        return False
    
    position = position[0]

    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": position.ticket,
        "sl": new_stop_loss,
        "tp": position.tp,
        "symbol": position.symbol,
        "type": position.type,
        "volume": position.volume,
    }

    result = mt5.order_send(request)





def new_tp(ticket, new_tp):

    position = mt5.positions_get(ticket=ticket)
    if not position:
        return False
    
    position = position[0]

    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": position.ticket,
        "sl": position.sl,
        "tp": new_tp,
        "symbol": position.symbol,
        "type": position.type,
        "volume": position.volume,
    }

    result = mt5.order_send(request)





def sar(symbol, timeframe, step=0.02, max=0.2, increment=0.01):
    ohlc = kandel(timeframe, 50, symbol)
    candles = pd.DataFrame(ohlc[:])

    step += increment
    max += increment
    
    candles['sar'] = ta.trend.PSARIndicator(high=candles['high'], low=candles['low'], close=candles['close'], step=step, max_step=max).psar()
    sar = candles['sar'].tolist()
    return sar




def cci (symbol , timeframe , period = 20): 

    ohlc = kandel(timeframe , period*10 , symbol)
    candles = pd.DataFrame(ohlc[:])
    candles['cci'] = ta.trend.CCIIndicator(high=candles['high'], low=candles['low'], close=candles['close'], window=period).cci()
    cci= candles['cci'].tolist()
    return cci



def atr(symbol , timeframe , period = 14) : 
    
    ohlc = kandel(timeframe , period*5 , symbol)
    candles = pd.DataFrame(ohlc[:])
    candles['H-L'] = abs(candles['high'] - candles['low'])
    candles['H-PC'] = abs(candles['high'] - candles['close'].shift(1))
    candles['L-PC'] = abs(candles['low'] - candles['close'].shift(1))
    candles['TR'] = candles[['H-L' , 'H-PC' , 'L-PC']].max(axis=1 , skipna=False)
    candles['ATR'] = candles['TR'].rolling(period).mean()
    atr = candles['ATR'].tolist()
    return atr


def mfi (symbol ,timeframe , period = 14) :

    ohlc = kandel(timeframe , period*5 , symbol)
    candles = pd.DataFrame(ohlc[:]) 
    candles['mfi'] = ta.volume.MFIIndicator(high=candles['high'], low=candles['low'], close=candles['close'], volume=candles['tick_volume'], window=period).money_flow_index()
    mfi = candles['mfi'].tolist()
    return mfi


def smma(symbol , timeframe , period):

    ohlc = kandel(timeframe , period*10 , symbol)
    candles = ohlc[:]


    smma = [np.nan] * (period - 1)
    initial_smma = candles['close'][:period].mean()
    smma.append(initial_smma)
    
    for price in candles['close'][period:]:
        smma_value = (smma[-1] * (period - 1) + price) / period
        smma.append(smma_value)
    return smma


def wma(symbol , timeframe , period) : 
    ohlc = kandel(timeframe , period*10 , symbol)
    candles = ohlc[:]

    weights = np.arange(1, period + 1)
    candles['wma'] = candles['close'].rolling(window = period).apply(lambda prices: np.dot(prices, weights)/weights.sum(), raw=True)
    wma = candles['wma'].tolist()

    return wma


def macd (symbol , timeframe , line ,short_period = 12 , long_period = 26 , signal_period = 9 ) : 
    ohlc = kandel(timeframe , long_period * 10 , symbol)
    candles = ohlc[:]

    candles['EMA_short'] = candles['close'].ewm(span=short_period, adjust=False).mean()
    candles['EMA_long'] = candles['close'].ewm(span=long_period, adjust=False).mean()
    candles['MACD'] = candles['EMA_short'] - candles['EMA_long']
    candles['Signal'] = candles['MACD'].rolling(window=signal_period).mean()
    candles['Histogram'] = candles['MACD'] - candles['Signal']

    
    macd = candles['MACD'].tolist()
    signall = candles['Signal'].tolist()
    histogram = candles['Histogram'].tolist()

    if line == 'macd' :
        return macd
    
    if line == 'signal' : 
        return signall
    
    if line == 'histogram' : 
        return histogram


def dema(symbol , timeframe , period = 14):
    ohlc = kandel(timeframe , period*5 , symbol)
    candles = ohlc[:]

    candles['ema1'] = candles['close'].ewm(span=period, adjust=False).mean()
    candles['ema2'] = candles['ema1'].ewm(span=period, adjust=False).mean()
    candles['dema'] = 2 * candles['ema1'] - candles['ema2']
    dema = candles['dema'].tolist()

    return dema


def tema(symbol , timeframe , period = 14) : 

    ohlc = kandel(timeframe , period * 10 , symbol)
    candles = ohlc[:]

    candles['ema1'] = candles['close'].ewm(span=period, adjust=False).mean()
    candles['ema2'] = candles['ema1'].ewm(span=period, adjust=False).mean()
    candles['ema3'] = candles['ema2'].ewm(span=period, adjust=False).mean()
    candles['tema'] = (3 * (candles['ema1'] - candles['ema2'])) + candles['ema3']
    tema = candles['tema'].tolist()

    return tema


def donchain_channel(symbol , timeframe ,line ,  period = 20) : 

    ohlc = kandel(timeframe , period*2 , symbol)
    candles = pd.DataFrame(ohlc[:])

    candles['upper'] = candles['high'].rolling(window=period).max()
    candles['lower'] = candles['low'].rolling(window=period).min()
    candles['middle'] = (candles['upper'] + candles['lower']) / 2

    upper = candles['upper'].shift(+1).tolist()
    lower = candles['lower'].shift(+1).tolist()
    middle = candles['middle'].shift(+1).tolist()

    if line == 'upper' : 
        return upper
    
    if line == 'lower' : 
        return lower

    if line == 'middle' : 
        return middle


def swing(symbol , timeframe , swing , window = 5 , lookback = 250)  : 

    ohlc = kandel(timeframe , lookback , symbol)
    candles = pd.DataFrame(ohlc[:])


    high_rolling_max = candles['high'].rolling(window=window, center=True).max()
    low_rolling_min = candles['low'].rolling(window=window, center=True).min()

    candles['swing_high'] = candles['high'][(candles['high'] == high_rolling_max) & (candles['high'].shift(window) < candles['high']) & (candles['high'].shift(-window) < candles['high'])]
    candles['swing_low'] = candles['low'][(candles['low'] == low_rolling_min) & (candles['low'].shift(window) > candles['low']) & (candles['low'].shift(-window) > candles['low'])]
    
    untouched_swing_highs = []
    untouched_swing_lows = []
    
    for i in range(len(candles)):
        if pd.notna(candles['swing_high'].iloc[i]):
            swing_high_touched = any(candles['high'].iloc[i+1:].ge(candles['swing_high'].iloc[i]))
            if not swing_high_touched:
                untouched_swing_highs.append(candles['swing_high'].iloc[i])
        
        if pd.notna(candles['swing_low'].iloc[i]):
            swing_low_touched = any(candles['low'].iloc[i+1:].le(candles['swing_low'].iloc[i]))
            if not swing_low_touched:
                untouched_swing_lows.append( candles['swing_low'].iloc[i])
    
    if swing == "high" : 
        return untouched_swing_highs

    if swing == "low" : 
        return untouched_swing_lows
    

def Avrage(symbol , timeframe, window) : 
    ohlc = kandel(timeframe, window*2 , symbol)
    prices = pd.DataFrame(ohlc[:])
    prices['ma'] = prices['close'].rolling(window= window).mean()
    ma = prices['ma'].values.tolist()
    return ma




def ravand(symbol, timeframe):

    if timeframe == '1m':
        i = '5m'
    elif timeframe == '3m':
        i = '15m'
    elif timeframe == '5m':
        i = '15m'
    elif timeframe == '15m':
        i = '30m'
    elif timeframe == '30m':
        i = '1h'
    elif timeframe == '1h':
        i = '4h'
    elif timeframe == '4h':
        i = '1d'
    elif timeframe == '1d':
        i = '1w'
    else:
        return False
    
    price = mt5.symbol_info_tick(symbol).ask
    sar_values = sar(symbol, i)
    if sar_values[-1] < price :
        return 'long'
    else :
        return 'short'



def sar_signal(symbol, timeframe, step=0.02, max_step=0.2 , increment=0.01):

    sar_values = sar(symbol, timeframe, step, max_step , increment )
    kandels = kandel(timeframe, 10, symbol)
    #sell signal 
    if kandels[-3]['open'] > sar_values[-3] and kandels[-2]['open'] < sar_values[-2] :
        return 'short'
    #long signal
    elif kandels[-3]['open'] < sar_values[-3] and kandels[-2]['open'] > sar_values[-2] :
        return 'long'
    else:
        return False



def engulfing (symbol , timeframe) : 
    ohlc = kandel(timeframe , 5 , symbol)
    candles = pd.DataFrame(ohlc[:])

    #short 
    if  whatKandel(timeframe , -3 , symbol) == 'long' and \
        whatKandel(timeframe , -2 , symbol) == 'short' and \
        candles['open'].iloc[-2] >= candles['close'].iloc[-3] and \
        candles['close'].iloc[-2] < candles['open'].iloc[-3] : 

        return 'short'
    
    #long 
    if  whatKandel(timeframe , -3 , symbol) == 'short' and \
        whatKandel(timeframe , -2 , symbol) == 'long' and \
        candles['open'].iloc[-2] <= candles['close'].iloc[-3] and \
        candles['close'].iloc[-2] > candles['open'].iloc[-3] : 

        return 'long'


def keltner_channel(symbol , timeframe ,line ,  period = 20 , atr = 10 , multiplier = 2) : 

    ohlc = kandel(timeframe , period*10 , symbol)
    candles = pd.DataFrame(ohlc[:])

    candles['EMA'] = candles['close'].ewm(span=period, adjust=False).mean()
    candles['TR'] = np.maximum(candles['high'] - candles['low'], 
                          np.maximum(abs(candles['high'] - candles['close'].shift(1)),
                                     abs(candles['low'] - candles['close'].shift(1))))
    candles['ATR'] = candles['TR'].rolling(window=atr).mean()
    candles['Upper_Channel'] = (candles['EMA'] + (multiplier * candles['ATR'])).shift(1)
    candles['Lower_Channel'] = (candles['EMA'] - (multiplier * candles['ATR'])).shift(1)

    if line == "up" : 
        return candles['Upper_Channel'].tolist()
    
    if line == 'mid' : 
        return candles['EMA'].shift(1).tolist()
    
    if line == 'low' :
        return candles['Lower_Channel'].tolist()



def line(symbol, timeframe, upOrdown):
    kandels = kandel(timeframe, 5, symbol)
    leg = (kandels[-2]['high'] - kandels[-2]['low']) / 8
    candle_color = whatKandel(timeframe, -1, symbol)
    lines = []

    if candle_color == 'long':
        num1 = kandels[-1]['low']
        lines.append(kandels[-1]['low'])
        for _ in range(50):
            num1 += leg
            lines.append(num1)
    else:
        num1 = kandels[-1]['high']
        lines.append(kandels[-1]['high'])
        for _ in range(50):
            num1 -= leg
            lines.append(num1)

    x = []
    if upOrdown == 'up':
        price = mt5.symbol_info_tick(symbol).bid
        for i in lines:
            if i > price:
                x.append(i)

        if len(x) == 0:
            return False
        else:
            return min(x)
    else:
        price = mt5.symbol_info_tick(symbol).ask
        for i in lines:
            if i < price:
                x.append(i)

        if len(x) == 0:
            return False
        else:
            return max(x)



def trend_alert(long_term='1d', mid_term='4h', symbol='BTCUSD.'):

    def candle(timeframe='30m', limit=500, symbol='BTCUSD'):
        timeframes = {
            '1m': mt5.TIMEFRAME_M1,
            '3m': mt5.TIMEFRAME_M3,
            '5m': mt5.TIMEFRAME_M5,
            '15m': mt5.TIMEFRAME_M15,
            '30m': mt5.TIMEFRAME_M30,
            '1h': mt5.TIMEFRAME_H1,
            '4h': mt5.TIMEFRAME_H4,
            '1d': mt5.TIMEFRAME_D1,
            '1w': mt5.TIMEFRAME_W1,
            '1mn': mt5.TIMEFRAME_MN1
        }
        
        time = timeframes.get(timeframe, mt5.TIMEFRAME_M30)  # Default to '30m' if not found
        candles = mt5.copy_rates_from_pos(symbol, time, 0, limit)
        
        if candles is None or len(candles) == 0:
            print(f"No data received for {symbol} on {timeframe}")
            return pd.DataFrame()  # Return empty DataFrame
        
        df = pd.DataFrame(candles, columns=['time', 'open', 'high', 'low', 'close'])
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def heiken_ashi(df):
        if len(df) < 2:
            return False
        
        ha_close = (df['open'] + df['high'] + df['low'] + df['close']) / 4.0
        ha_open = pd.Series(index=df.index, data=np.nan)
        ha_open.iloc[0] = (df['open'].iloc[0] + df['close'].iloc[0]) / 2.0
        
        for i in range(1, len(df)):
            ha_open.iloc[i] = (ha_open.iloc[i-1] + ha_close.iloc[i-1]) / 2.0
        
        ha_high = np.maximum(df['high'], np.maximum(ha_open, ha_close))
        ha_low = np.minimum(df['low'], np.minimum(ha_open, ha_close))
        
        ha_df = pd.DataFrame({
            'open': ha_open,
            'high': ha_high,
            'low': ha_low,
            'close': ha_close
        })
        return ha_df


    lt_df = candle(timeframe=long_term, limit=500, symbol=symbol)
    mt_df = candle(timeframe=mid_term, limit=500, symbol=symbol)

    if len(lt_df) < 2 or len(mt_df) < 2:
        return False

    lt_ha = heiken_ashi(lt_df)
    mt_ha = heiken_ashi(mt_df)
    mt_df['ema20'] = mt_df['close'].ewm(span=20, adjust=False).mean()
    lt_trend = lt_ha['close'] > lt_ha['open']
    mt_trend = (mt_ha['close'] > mt_ha['open']) & (mt_ha['close'] > mt_df['ema20']) & (mt_df['ema20'].diff() > 0)

    long_signal = lt_trend.iloc[-1] and mt_trend.iloc[-1]
    short_signal = not lt_trend.iloc[-1] and not mt_trend.iloc[-1]

    if long_signal:
        return 'long'
    elif short_signal:
        return 'short'
    else:
        return False




def nadaraya_upper(symbol, timeframe, mult=2.0, h=8.0):

    if timeframe == '5m':
        time = mt5.TIMEFRAME_M5
    if timeframe == '3m':
        time = mt5.TIMEFRAME_M3
    if timeframe == '1m':
        time = mt5.TIMEFRAME_M1
    if timeframe == '15m':
        time = mt5.TIMEFRAME_M15
    if timeframe == '30m':
        time = mt5.TIMEFRAME_M30
    if timeframe == '1h':
        time = mt5.TIMEFRAME_H1
    if timeframe == '4h':
        time = mt5.TIMEFRAME_H4
    if timeframe == '1d':
        time = mt5.TIMEFRAME_D1
    if timeframe == '1w':
        time = mt5.TIMEFRAME_W1
    if timeframe == '1mn':
        time = mt5.TIMEFRAME_MN1

    def gauss(x, h):
        return np.exp(-(x**2) / (2 * h**2))

    def nadaraya_watson(src, h):
        n = len(src)
        out = np.zeros(n)
        for i in range(n):
            weights = gauss(np.arange(i+1)[::-1], h)
            out[i] = np.sum(src[:i+1] * weights) / np.sum(weights)
        return out

    rates = mt5.copy_rates_from_pos(symbol, time, 0, 500)
    if rates is None:
        print("Failed to get rates, error code =", mt5.last_error())
        return []

    
    data = pd.DataFrame(rates)
    data['time'] = pd.to_datetime(data['time'], unit='s')
    data.set_index('time', inplace=True)

  
    src = data['close'].values
    out = nadaraya_watson(src, h)
    mae = np.mean(np.abs(src - out)) * mult
    upper = out + mae
    lower = out - mae



    return upper



def nadaraya_lower(symbol, timeframe, mult=2.0, h=8.0):

    if timeframe == '5m':
        time = mt5.TIMEFRAME_M5
    if timeframe == '3m':
        time = mt5.TIMEFRAME_M3
    if timeframe == '1m':
        time = mt5.TIMEFRAME_M1
    if timeframe == '15m':
        time = mt5.TIMEFRAME_M15
    if timeframe == '30m':
        time = mt5.TIMEFRAME_M30
    if timeframe == '1h':
        time = mt5.TIMEFRAME_H1
    if timeframe == '4h':
        time = mt5.TIMEFRAME_H4
    if timeframe == '1d':
        time = mt5.TIMEFRAME_D1
    if timeframe == '1w':
        time = mt5.TIMEFRAME_W1
    if timeframe == '1mn':
        time = mt5.TIMEFRAME_MN1

    def gauss(x, h):
        return np.exp(-(x**2) / (2 * h**2))

    def nadaraya_watson(src, h):
        n = len(src)
        out = np.zeros(n)
        for i in range(n):
            weights = gauss(np.arange(i+1)[::-1], h)
            out[i] = np.sum(src[:i+1] * weights) / np.sum(weights)
        return out

    rates = mt5.copy_rates_from_pos(symbol, time, 0, 500)
    if rates is None:
        print("Failed to get rates, error code =", mt5.last_error())
        return []

    
    data = pd.DataFrame(rates)
    data['time'] = pd.to_datetime(data['time'], unit='s')
    data.set_index('time', inplace=True)

  
    src = data['close'].values
    out = nadaraya_watson(src, h)
    mae = np.mean(np.abs(src - out)) * mult
    upper = out + mae
    lower = out - mae



    return lower



def nadaraya(symbol, timeframe, mult=2.0, h=8.0 , updown='up'):

    if timeframe == '5m':
        time = mt5.TIMEFRAME_M5
    if timeframe == '3m':
        time = mt5.TIMEFRAME_M3
    if timeframe == '1m':
        time = mt5.TIMEFRAME_M1
    if timeframe == '15m':
        time = mt5.TIMEFRAME_M15
    if timeframe == '30m':
        time = mt5.TIMEFRAME_M30
    if timeframe == '1h':
        time = mt5.TIMEFRAME_H1
    if timeframe == '4h':
        time = mt5.TIMEFRAME_H4
    if timeframe == '1d':
        time = mt5.TIMEFRAME_D1
    if timeframe == '1w':
        time = mt5.TIMEFRAME_W1
    if timeframe == '1mn':
        time = mt5.TIMEFRAME_MN1

    def gauss(x, h):
        return np.exp(-(x**2) / (2 * h**2))

    def nadaraya_watson(src, h):
        n = len(src)
        out = np.zeros(n)
        for i in range(n):
            weights = gauss(np.arange(i+1)[::-1], h)
            out[i] = np.sum(src[:i+1] * weights) / np.sum(weights)
        return out

    rates = mt5.copy_rates_from_pos(symbol, time, 0, 500)
    if rates is None:
        print("Failed to get rates, error code =", mt5.last_error())
        return []

    
    data = pd.DataFrame(rates)
    data['time'] = pd.to_datetime(data['time'], unit='s')
    data.set_index('time', inplace=True)

  
    src = data['close'].values
    out = nadaraya_watson(src, h)
    mae = np.mean(np.abs(src - out)) * mult
    upper = out + mae
    lower = out - mae
    if updown == 'up':
        return upper
    else :
        return lower


def ravand_signal(symbol, timeframe):

    uper = nadaraya(symbol, timeframe, mult=2, h=4.0 , updown='up')
    down = nadaraya(symbol, timeframe, mult=2, h=4.0 , updown='down')
    Avrage18 = Avrage(symbol ,timeframe,18)[-1]
    if down[-1] > Avrage18 and down[-2]>= Avrage18 and down[-3] <= Avrage18 and uper[-1] > Avrage18 :
        return 'long'
    elif uper[-1] < Avrage18 and uper[-2]<= Avrage18 and uper[-3] >= Avrage18 and down[-1] < Avrage18 :
        return 'short'
    elif  uper[-1] > Avrage18 and uper[-2] > Avrage18 and uper[-3] > Avrage18  and uper[-4] > Avrage18 and uper[-5] > Avrage18 and down[-1] < Avrage18 and  down[-2] < Avrage18 and down[-3] < Avrage18  and down[-4] < Avrage18  and down[-4] < Avrage18:
        return 'reng'
    else :
        return False
    
def nadaraya_signals(symbol, timeframe, mult=2.0, h=8.0):
    ask_price = mt5.symbol_info_tick(symbol).ask
    bid_price = mt5.symbol_info_tick(symbol).bid
    Avrage18 = Avrage(symbol , timeframe , 18)[-1]
    if ravand_signal(symbol, timeframe) == 'reng' and bid_price > Avrage18:
        return 'short' 
    elif ravand_signal(symbol, timeframe) == 'reng' and ask_price < Avrage18:
        return 'long' 

def ott_signal(symbol ,timeframe, length=1, percent=1.4):

    ohlc = kandel(timeframe , 100 , symbol)
    candles = ohlc[:]
    src = candles['close']
    valpha = 2 / (length + 1)

    vud1 = pd.Series(np.where(src > src.shift(1), src - src.shift(1), 0))
    vdd1 = pd.Series(np.where(src < src.shift(1), src.shift(1) - src, 0))
    vUD = vud1.rolling(window=9).sum()
    vDD = vdd1.rolling(window=9).sum()
    vCMO = (vUD - vDD) / (vUD + vDD)
    vCMO = vCMO.fillna(0)  # Replace NaNs with 0

    VAR = np.zeros(len(src))
    for i in range(1, len(src)):
        VAR[i] = valpha * abs(vCMO[i]) * src[i] + (1 - valpha * abs(vCMO[i])) * VAR[i-1]

    MAvg = VAR
    fark = MAvg * percent * 0.01
    longStop = MAvg - fark
    longStopPrev = pd.Series(longStop).shift(1).fillna(longStop[0])

    longStop = np.where(MAvg > longStopPrev, np.maximum(longStop, longStopPrev), longStop)
    shortStop = MAvg + fark
    shortStopPrev = pd.Series(shortStop).shift(1).fillna(shortStop[0])

    shortStop = np.where(MAvg < shortStopPrev, np.minimum(shortStop, shortStopPrev), shortStop)
    dir = np.ones(len(src))
    dir[0] = 1

    for i in range(1, len(src)):
        if dir[i-1] == -1 and MAvg[i] > shortStopPrev[i]:
            dir[i] = 1
        elif dir[i-1] == 1 and MAvg[i] < longStopPrev[i]:
            dir[i] = -1
        else:
            dir[i] = dir[i-1]

    MT = np.where(dir == 1, longStop, shortStop)
    OTT = np.where(MAvg > MT, MT * (200 + percent) / 200, MT * (200 - percent) / 200)
    candles['OTT'] = OTT

    otts = candles['OTT'].tolist()
    if round(otts[-10]) == round(otts[-5]) and round(otts[-5]) == round(otts[-1]) :
        return 'reng'
    elif round(otts[-1]) < round(otts[-3]):
        return 'short'
    elif round(otts[-1]) > round(otts[-3]):
        return 'long'
    else:
        return False

def supertrend(symbol , timeframe , atr_period=9, multiplier=3.9, change_atr=True):
    ohlc = kandel(timeframe, atr_period*10 , symbol)
    df = ohlc[:]
    df['hl2'] = (df['high'] + df['low']) /2
    
    df['TR'] = np.maximum(df['high'] - df['low'], 
                          np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                     abs(df['low'] - df['close'].shift(1))))
    

    if change_atr:
        df['ATR'] = df['TR'].rolling(window=atr_period).mean()
    else:
        df['ATR'] = df['TR'].ewm(span=atr_period, adjust=False).mean()


    df['UpperBand'] = df['hl2'] - (multiplier * df['ATR'])
    df['LowerBand'] = df['hl2'] + (multiplier * df['ATR'])


    df['Supertrend'] = np.nan
    df['Trend'] = 1
    
    for i in range(1, len(df)):
        if df['close'].iloc[i - 1] > df.at[i - 1, 'UpperBand']:
            df.at[i, 'UpperBand'] = max(df.at[i, 'UpperBand'], df.at[i - 1, 'UpperBand'])
        else:
            df.at[i, 'UpperBand'] = df.at[i, 'UpperBand']

        if df['close'].iloc[i - 1] < df.at[i - 1, 'LowerBand']:
            df.at[i, 'LowerBand'] = min(df.at[i, 'LowerBand'], df.at[i - 1, 'LowerBand'])
        else:
            df.at[i, 'LowerBand'] = df.at[i, 'LowerBand']


        if df.at[i - 1, 'Trend'] == 1:
            df.at[i, 'Trend'] = -1 if df.at[i, 'close'] < df.at[i - 1, 'UpperBand'] else 1
        else:
            df.at[i, 'Trend'] = 1 if df.at[i, 'close'] > df.at[i - 1, 'LowerBand'] else -1


        df.at[i, 'Supertrend'] = df.at[i, 'UpperBand'] if df.at[i, 'Trend'] == 1 else df.at[i, 'LowerBand']
        df['Supertrend_Position'] = np.where(df['Supertrend'] > df['close'], 'Above', 'Below')

        supertrend = []
        for _, row in df.iterrows():
            row_dict = {'value': row['Supertrend'], 'position': row['Supertrend_Position']}
            supertrend.append(row_dict)
        
    return supertrend

def nadaraya_signals2(symbol, timeframe, mult=2.0, h=8.0):
    ask_price = mt5.symbol_info_tick(symbol).ask
    bid_price = mt5.symbol_info_tick(symbol).bid
    Avrage18 = Avrage(symbol , timeframe , 18)[-1]
    if ravand_signal(symbol, timeframe) == 'reng' and bid_price > Avrage18:
        return 'short' 
    elif ravand_signal(symbol, timeframe) == 'reng' and ask_price < Avrage18:
        return 'long' 

def supertrend_signal(symbol , timeframe , atr_period=9, multiplier=3.9, change_atr=True):
    last1 = supertrend(symbol , timeframe , atr_period , multiplier)[-2]['position']
    last2 = supertrend(symbol , timeframe , atr_period , multiplier)[-3]['position']
    if last1 == 'Below' and last2 == 'Above' :
        return 'buy'
    elif last1 == 'Above' and last2 == 'Below':
        return 'sell'
    else:
        return False

def SMA_RSI(timeframe , symbol , period):
    ohlc = kandel(timeframe, period*10, symbol)  
    
    candles = pd.DataFrame(ohlc[:], columns=['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume'])

    candles['rsi'] = ta.momentum.RSIIndicator(candles['close'], window=period).rsi()
    
    valid_rsi = candles['rsi'].dropna()
    
    average_rsi = statistics.mean(valid_rsi)
    
    return average_rsi

def williams(symbol , timeframe , period = 14) : 

    ohlc = kandel(timeframe , period*5 , symbol)
    candles = pd.DataFrame(ohlc[:])

    high = candles['high'].rolling(window=period).max()
    low = candles['low'].rolling(window=period).min()
    close = candles['close']
    williams_r = ((high - close) / (high - low)) * -100
    return williams_r.tolist()

def trend_signal(symbol, timeframe, ma_type="EMA", ma_period=9, alma_offset=0.85, alma_sigma=6, num_candles=100):

    if timeframe == '5m':
        time = mt5.TIMEFRAME_M5
    if timeframe == '3m':
        time = mt5.TIMEFRAME_M3
    if timeframe == '1m':
        time = mt5.TIMEFRAME_M1
    if timeframe == '2m':
        time = mt5.TIMEFRAME_M2
    if timeframe == '15m':
        time = mt5.TIMEFRAME_M15
    if timeframe == '30m':
        time = mt5.TIMEFRAME_M30
    if timeframe == '1h':
        time = mt5.TIMEFRAME_H1
    if timeframe == '4h':
        time = mt5.TIMEFRAME_H4
    if timeframe == '1d':
        time = mt5.TIMEFRAME_D1
    if timeframe == '1w':
        time = mt5.TIMEFRAME_W1
    if timeframe == '1mn':
        time = mt5.TIMEFRAME_MN1
    rates = mt5.copy_rates_from_pos(symbol, time, 0, num_candles)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    df['HA_Close'] = (df['close'] + df['open'] + df['high'] + df['low']) / 4
    df['HA_Open'] = (df['open'].shift(1) + df['close'].shift(1)) / 2
    df['HA_High'] = df[['high', 'HA_Open', 'HA_Close']].max(axis=1)
    df['HA_Low'] = df[['low', 'HA_Open', 'HA_Close']].min(axis=1)

    if ma_type == "ALMA":
        m = np.floor(0.5 * (ma_period - 1))
        s = ma_period / alma_sigma
        w = np.exp(-((np.arange(ma_period) - m)**2) / (2 * s**2))
        alma = np.convolve(df['HA_Close'], w / w.sum(), mode='valid')
        df['MA'] = pd.Series(alma, index=df.index[ma_period-1:])
    elif ma_type == "HMA":
        wma_half = df['HA_Close'].rolling(window=ma_period//2).mean()
        wma_full = df['HA_Close'].rolling(window=ma_period).mean()
        df['MA'] = 2 * wma_half - wma_full
        df['MA'] = df['MA'].rolling(window=int(np.sqrt(ma_period))).mean()
    elif ma_type == "SMA":
        df['MA'] = df['HA_Close'].rolling(window=ma_period).mean()
    elif ma_type == "EMA":
        df['MA'] = df['HA_Close'].ewm(span=ma_period, adjust=False).mean()
    elif ma_type == "ZLEMA":
        lag = (ma_period - 1) // 2
        df['MA'] = df['HA_Close'] + (df['HA_Close'] - df['HA_Close'].shift(lag)).ewm(span=ma_period, adjust=False).mean()
    else:
        raise ValueError("نوع MA معتبر نیست!")

    df['Trend'] = 100 * (df['HA_Close'] - df['HA_Open']) / (df['HA_High'] - df['HA_Low'])
    signals = np.where(df['Trend'] > 0, 'long', 'short')

    return signals

def candle(timeframe='30m', limit=500, symbol='BTCUSD'):
        timeframes = {
            '1m': mt5.TIMEFRAME_M1,
            '3m': mt5.TIMEFRAME_M3,
            '5m': mt5.TIMEFRAME_M5,
            '15m': mt5.TIMEFRAME_M15,
            '30m': mt5.TIMEFRAME_M30,
            '1h': mt5.TIMEFRAME_H1,
            '4h': mt5.TIMEFRAME_H4,
            '1d': mt5.TIMEFRAME_D1,
            '1w': mt5.TIMEFRAME_W1,
            '1mn': mt5.TIMEFRAME_MN1
        }
        
        time = timeframes.get(timeframe, mt5.TIMEFRAME_M30)  # Default to '30m' if not found
        candles = mt5.copy_rates_from_pos(symbol, time, 0, limit)
        
        if candles is None or len(candles) == 0:
            print(f"No data received for {symbol} on {timeframe}")
            return pd.DataFrame()  # Return empty DataFrame
        
        df = pd.DataFrame(candles, columns=['time', 'open', 'high', 'low', 'close'])
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

def heiken_ashi(df):
        if len(df) < 2:
            return False
        
        ha_close = (df['open'] + df['high'] + df['low'] + df['close']) / 4.0
        ha_open = pd.Series(index=df.index, data=np.nan)
        ha_open.iloc[0] = (df['open'].iloc[0] + df['close'].iloc[0]) / 2.0
        
        for i in range(1, len(df)):
            ha_open.iloc[i] = (ha_open.iloc[i-1] + ha_close.iloc[i-1]) / 2.0
        
        ha_high = np.maximum(df['high'], np.maximum(ha_open, ha_close))
        ha_low = np.minimum(df['low'], np.minimum(ha_open, ha_close))
        
        ha_df = pd.DataFrame({
            'open': ha_open,
            'high': ha_high,
            'low': ha_low,
            'close': ha_close
        })
        return ha_df

def heiken_ashi_signals(timeframe='5m' , limit=500 , symbol='XAUUSD.'):

    ca = candle(timeframe , limit , symbol)
    hi = heiken_ashi(ca).iloc[-1]

    if hi['close'] > hi['open'] :
        hi_signal = 'long'
    elif hi['close'] < hi['open'] :
        hi_signal = 'short'
    else :
        hi_signal = None

    return hi_signal

def supertrend_hi(symbol, timeframe, atr_period=9, multiplier=3.9, change_atr=True, source='hl2', ema_value=200):
    ohlc = candle(timeframe, atr_period * 10, symbol)  # گرفتن داده‌های کندل
    ha_df = heiken_ashi(ohlc)  # تبدیل داده‌ها به کندل‌های Heiken Ashi

    df = ha_df.copy()
    
    # محاسبه EMA با مقدار مشخص‌شده توسط کاربر
    df['ema'] = df['close'].ewm(span=ema_value, adjust=False).mean()

    # محاسبه hl2
    df['hl2'] = (df['high'] + df['low']) / 2
    
    # انتخاب منبع (hl2 یا ema)
    if source == 'hl2':
        df['selected_source'] = df['hl2']
    elif source == 'ema':
        df['selected_source'] = df['ema']
    else:
        raise ValueError("Source must be either 'hl2' or 'ema'")

    df['TR'] = np.maximum(df['high'] - df['low'],
                          np.maximum(abs(df['high'] - df['close'].shift(1)),
                                     abs(df['low'] - df['close'].shift(1))))

    if change_atr:
        df['ATR'] = df['TR'].rolling(window=atr_period).mean()
    else:
        df['ATR'] = df['TR'].ewm(span=atr_period, adjust=False).mean()

    # استفاده از منبع انتخاب‌شده برای محاسبه UpperBand و LowerBand
    df['UpperBand'] = df['selected_source'] - (multiplier * df['ATR'])
    df['LowerBand'] = df['selected_source'] + (multiplier * df['ATR'])

    df['Supertrend'] = np.nan
    df['Trend'] = 1

    for i in range(1, len(df)):
        if df['close'].iloc[i - 1] > df.at[i - 1, 'UpperBand']:
            df.at[i, 'UpperBand'] = max(df.at[i, 'UpperBand'], df.at[i - 1, 'UpperBand'])
        else:
            df.at[i, 'UpperBand'] = df.at[i, 'UpperBand']

        if df['close'].iloc[i - 1] < df.at[i - 1, 'LowerBand']:
            df.at[i, 'LowerBand'] = min(df.at[i, 'LowerBand'], df.at[i - 1, 'LowerBand'])
        else:
            df.at[i, 'LowerBand'] = df.at[i, 'LowerBand']

        if df.at[i - 1, 'Trend'] == 1:
            df.at[i, 'Trend'] = -1 if df.at[i, 'close'] < df.at[i - 1, 'UpperBand'] else 1
        else:
            df.at[i, 'Trend'] = 1 if df.at[i, 'close'] > df.at[i - 1, 'LowerBand'] else -1

        df.at[i, 'Supertrend'] = df.at[i, 'UpperBand'] if df.at[i, 'Trend'] == 1 else df.at[i, 'LowerBand']

    df['Supertrend_Position'] = np.where(df['Supertrend'] > df['close'], 'Above', 'Below')

    supertrend_hi = []
    for _, row in df.iterrows():
        row_dict = {'value': row['Supertrend'], 'position': row['Supertrend_Position']}
        supertrend_hi.append(row_dict)

    return supertrend_hi

def TS_signal(symbol, timeframe, ma_type="EMA", ma_period=9, alma_offset=0.85, alma_sigma=6, num_candles=100):
    last1 = trend_signal(symbol, timeframe, ma_type="EMA", ma_period=9, alma_offset=0.85, alma_sigma=6, num_candles=100)[-1]
    last2 = trend_signal(symbol, timeframe, ma_type="EMA", ma_period=9, alma_offset=0.85, alma_sigma=6, num_candles=100)[-2]
    last3 = trend_signal(symbol, timeframe, ma_type="EMA", ma_period=9, alma_offset=0.85, alma_sigma=6, num_candles=100)[-3]
    if last1 == 'long' and last2 == 'long' and last3 == 'short' :
        return 'buy'
    elif last1 == 'short' and last2 == 'short'and last3 == 'long':
        return 'sell'
    else:
        return False

def count_sl():
    time_difference = datetime.timedelta(hours=3)
    mt5_now = datetime.datetime.now(datetime.timezone.utc) + time_difference
    start_of_day = datetime.datetime(mt5_now.year, mt5_now.month, mt5_now.day, tzinfo=datetime.timezone.utc) + time_difference
    orders = mt5.history_deals_get(start_of_day, mt5_now)
    stop_count = sum(1 for order in orders if order.profit < 0 )
    return stop_count

def count_tp():
    time_difference = datetime.timedelta(hours=3)
    mt5_now = datetime.datetime.now(datetime.timezone.utc) + time_difference
    start_of_day = datetime.datetime(mt5_now.year, mt5_now.month, mt5_now.day, tzinfo=datetime.timezone.utc) + time_difference
    orders = mt5.history_deals_get(start_of_day, mt5_now)
    profit_count = sum(1 for order in orders if order.profit > 0)
    return profit_count

def profit_today():
    time_difference = datetime.timedelta(hours=3)
    mt5_now = datetime.datetime.now(datetime.timezone.utc) + time_difference
    start_of_day = datetime.datetime(mt5_now.year, mt5_now.month, mt5_now.day, tzinfo=datetime.timezone.utc) + time_difference
    orders = mt5.history_deals_get(start_of_day, mt5_now)
    profit_today = sum(order.profit for order in orders)    
    return profit_today

def count_sl_in_hours(hours=0):
    time_difference = datetime.timedelta(hours=3)
    mt5_now = datetime.datetime.now(datetime.timezone.utc) + time_difference
    start_time = mt5_now - datetime.timedelta(hours=hours)
    orders = mt5.history_deals_get(start_time, mt5_now)
    stop_count = sum(1 for order in orders if order.profit < 0 )
    return stop_count

def count_tp_in_hours(hours=0):
    time_difference = datetime.timedelta(hours=3)
    mt5_now = datetime.datetime.now(datetime.timezone.utc) + time_difference
    start_time = mt5_now - datetime.timedelta(hours=hours)
    orders = mt5.history_deals_get(start_time, mt5_now)
    stop_count = sum(1 for order in orders if order.profit > 0 )
    return stop_count

def count_sl_in_hours_with_comment(comment, hours=0):
    time_difference = datetime.timedelta(hours=3)
    mt5_now = datetime.datetime.now(datetime.timezone.utc) + time_difference
    start_time = mt5_now - datetime.timedelta(hours=hours)
    deals = mt5.history_deals_get(start_time, mt5_now)
    if deals is None:
        print("No deals found.")
        return 0
    position_ids = set(deal.position_id for deal in deals if deal.comment == comment and deal.type in (mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL))
    stop_count = sum(1 for deal in deals if deal.position_id in position_ids and deal.profit < 0)

    return stop_count

def count_sl_with_comment(comment):
    time_difference = datetime.timedelta(hours=3)
    mt5_now = datetime.datetime.now(datetime.timezone.utc) + time_difference
    start_of_day = datetime.datetime(mt5_now.year, mt5_now.month, mt5_now.day, tzinfo=datetime.timezone.utc) + time_difference
    deals = mt5.history_deals_get(start_of_day, mt5_now)
    if deals is None:
        print("No deals found.")
        return 0
    position_ids = set(deal.position_id for deal in deals if deal.comment == comment and deal.type in (mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL))
    stop_count = sum(1 for deal in deals if deal.position_id in position_ids and deal.profit < 0)

    return stop_count

def total_profit_today_with_comment(comment):
    time_difference = datetime.timedelta(hours=3)
    mt5_now = datetime.datetime.now(datetime.timezone.utc) + time_difference
    start_of_day = datetime.datetime(mt5_now.year, mt5_now.month, mt5_now.day, tzinfo=datetime.timezone.utc) + time_difference
    deals = mt5.history_deals_get(start_of_day, mt5_now)
    if deals is None:
        print("No deals found.")
        return 0
    position_ids = set(deal.position_id for deal in deals if comment in deal.comment and deal.type in (mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL))
    profit_today = sum(deal.profit for deal in deals if deal.position_id in position_ids)

    return profit_today

def count_tp_with_comment(comment):
    time_difference = datetime.timedelta(hours=3)
    mt5_now = datetime.datetime.now(datetime.timezone.utc) + time_difference
    start_of_day = datetime.datetime(mt5_now.year, mt5_now.month, mt5_now.day, tzinfo=datetime.timezone.utc) + time_difference
    deals = mt5.history_deals_get(start_of_day, mt5_now)
    if deals is None:
        print("No deals found.")
        return 0
    position_ids = set(deal.position_id for deal in deals if deal.comment == comment and deal.type in (mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL))
    profit_count = sum(1 for deal in deals if deal.position_id in position_ids and deal.profit > 0)

    return profit_count



def lot_calculator(symbol : str , risk : int , open_price : float , stop_loss : float) : 
    price = open_price
    sl = stop_loss
    amount_of_risk = mt5.account_info()._asdict()['balance'] * (risk / 100)
    raw_lot_size = 0
    lot_size = None
    if symbol in  ['XAUUSD' , 'XAUUSD.' , 'XAUUSD_i'] : 

        raw_lot_size = amount_of_risk / (abs(sl - price) * 100)
        raw_lot_size = math.floor(raw_lot_size *100) / 100.0

    elif symbol in ['USDJPY' , 'USDJPY.' , 'USDJPY_i']  : 
        pip_size = 0.01

        stop_pip_integer = abs((sl - price) / pip_size)

        pip_value = amount_of_risk / stop_pip_integer
        pip_value = pip_value * sl

        raw_lot_size = pip_value / 1000
    
    elif symbol in ['BTCUSD' , 'BTCUSD.' , 'BTCUSD_i']  : 
        pip_size = 1.00  

        stop_pip_integer = abs((sl - price) / pip_size)

        raw_lot_size = amount_of_risk / stop_pip_integer

    elif symbol in ['USDCAD' , 'USDCAD.' , 'USDCAD_i'] : 
        pip_size = 0.0001 

        stop_pip_integer = abs((sl - price) / pip_size)

        pip_value = amount_of_risk / stop_pip_integer 
        pip_value = pip_value * sl 

        raw_lot_size = pip_value / 10

    elif symbol in ['EURUSD' , 'GBPUSD'  , 'USDCHF' , 'AUDUSD' , 'EURUSD.' , 'EURUSD_i' , 'GBPUSD.' , 'GBPUSD_i' , 'USDCHF.' , 'USDCHF_i' , 'AUDUSD.' , 'AUDUSD_i']  :
        pip_size = 0.0001

        stop_pip_integer = abs((sl - price) / pip_size)

        pip_value = amount_of_risk / stop_pip_integer

        raw_lot_size = pip_value / 10
    else : 
        lot_size = 0.01


    if raw_lot_size != 0 : 
        lot_size = float(raw_lot_size)
        lot_size = math.floor(lot_size * 100) / 100.0

        if lot_size < 0.01  : 
            lot_size = 0.01 


    if lot_size is None :

        if symbol in ['EURUSD' , 'GBPUSD'  , 'USDCHF' , 'AUDUSD' , 'EURUSD.' , 'EURUSD_i' , 'GBPUSD.' , 'GBPUSD_i' , 'USDCHF.' , 'USDCHF_i' , 'AUDUSD.' , 'AUDUSD_i']  :
           lot_size = 0.05
     
        else:
            lot_size = 0.01
    
    return lot_size



def pnl_today( timezone = 3 ) : 
    def broker_now(h = 0 ) : 
        custom_utc_offset = datetime.timedelta(hours=h)
        custom_timezone = pytz.FixedOffset(custom_utc_offset.total_seconds() // 60)

        return datetime.datetime.now(custom_timezone)


    profit = 0

    # adding history profits
    now = broker_now(timezone)
    from_time = datetime.datetime(now.year , now.month , now.day , 0 , 0 , 0 , 0)
    to_time =  from_time + datetime.timedelta(days=1)

    history = mt5.history_deals_get(from_time ,to_time )

    for position in history : 
        profit += position.commission
        profit += position.swap
        profit += position.profit
        profit += position.fee

    
    positions = mt5.positions_get()

    for i in positions : 
        position = i._asdict()
        profit += position['swap']
        profit += position['profit']


    return round(profit , 2)

def draw_down_checker (balance , pnl , percent) : 
    if pnl < 0 : 
        if (abs(pnl)) >= (balance * percent) : 
            return True
        else : 
            return False
    else : 
        return False

def total_draw_down(balance , percent):
    equity = mt5.account_info()._asdict()['equity']
    if equity - balance < 0 : 
        if abs(equity - balance) >= (balance * percent) : 
            return True
        else : 
            return False
    else : 
        return False
    
def stoch(symbol, timeframe, type='k', period_k=14, smooth_k=1, period_d=3):
    if timeframe == '5m':
        time = mt5.TIMEFRAME_M5
    if timeframe == '3m':
        time = mt5.TIMEFRAME_M3
    if timeframe == '1m':
        time = mt5.TIMEFRAME_M1
    if timeframe == '2m':
        time = mt5.TIMEFRAME_M2
    if timeframe == '15m':
        time = mt5.TIMEFRAME_M15
    if timeframe == '30m':
        time = mt5.TIMEFRAME_M30
    if timeframe == '1h':
        time = mt5.TIMEFRAME_H1
    if timeframe == '4h':
        time = mt5.TIMEFRAME_H4
    if timeframe == '1d':
        time = mt5.TIMEFRAME_D1
    if timeframe == '1w':
        time = mt5.TIMEFRAME_W1
    if timeframe == '1mn':
        time = mt5.TIMEFRAME_MN1
    rates = mt5.copy_rates_from_pos(symbol, time, 0, 1000)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    lowest_low = df['low'].rolling(window=period_k).min()
    highest_high = df['high'].rolling(window=period_k).max()
    k = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
    k_smooth = k.rolling(window=smooth_k).mean()
    if type.lower() == 'k':
        return k_smooth.tolist()
    elif type.lower() == 'd':
        d = k_smooth.rolling(window=period_d).mean()
        return d.tolist()
    else:
       return False
    


def tsi(symbol , timeframe ,line = 'tsi',long_length = 25, short_length=13 , signal_length=13):
    if timeframe == '5m':
        time = mt5.TIMEFRAME_M5
    if timeframe == '3m':
        time = mt5.TIMEFRAME_M3
    if timeframe == '1m':
        time = mt5.TIMEFRAME_M1
    if timeframe == '2m':
        time = mt5.TIMEFRAME_M2
    if timeframe == '15m':
        time = mt5.TIMEFRAME_M15
    if timeframe == '30m':
        time = mt5.TIMEFRAME_M30
    if timeframe == '1h':
        time = mt5.TIMEFRAME_H1
    if timeframe == '4h':
        time = mt5.TIMEFRAME_H4
    if timeframe == '1d':
        time = mt5.TIMEFRAME_D1
    if timeframe == '1w':
        time = mt5.TIMEFRAME_W1
    if timeframe == '1mn':
        time = mt5.TIMEFRAME_MN1

    rates = mt5.copy_rates_from_pos(symbol, time, 0, 1000) 
    prices = pd.DataFrame(rates)['close'] 
    def ema(data, length):
        return data.ewm(span=length, adjust=False).mean()

    def double_smooth(src, long_length, short_length):
        first_smooth = ema(src, long_length)
        return ema(first_smooth, short_length)
    
    pc = prices.diff()
    double_smoothed_pc = double_smooth(pc, long_length, short_length)
    double_smoothed_abs_pc = double_smooth(np.abs(pc), long_length, short_length)
    tsi_value = 100 * (double_smoothed_pc / double_smoothed_abs_pc)
    signal_line = ema(tsi_value, signal_length)

    if line == 'tsi':
        return tsi_value.to_numpy()
    else:
        return signal_line.to_numpy()

def cross_tsi(symbol , timeframe ,long_length = 25, short_length=13 , signal_length=13 ):
    tsis = tsi(symbol , timeframe , 'tsi' , long_length , short_length , signal_length)
    signals = tsi(symbol , timeframe , 'signals' , long_length , short_length , signal_length)
    if  tsis[-1]> signals[-1] and tsis[-2]>=signals[-2] and tsis[-3]<signals[-3] and tsis[-4]<signals[-2] and tsis[-5]<signals[-2]:
        return 'buy'
    elif tsis[-1]< signals[-1] and tsis[-2]<=signals[-2] and tsis[-3]>signals[-3] and tsis[-4]>signals[-2] and tsis[-5]>signals[-2]:
        return 'sell'
    else:
        return False



def count_position_now(type , symbol):
    positions = mt5.positions_get()
    buy = 0
    sell = 0
    for position in positions :
        if position._asdict()['type'] == 0 and position._asdict()['symbol'] == symbol :
            buy += 1

        if position._asdict()['type'] == 1 and position._asdict()['symbol'] == symbol :
            sell += 1
    if type == 'buy':
        return buy
    else:
        return sell



def cross_macd(symbol , timeframe ,short_period = 12 , long_period = 26 , signal_period = 9 ):
    mcd = macd(symbol , timeframe , 'macd' ,short_period = 12 , long_period = 26 , signal_period = 9 )
    signals = macd(symbol , timeframe , 'signal' ,short_period = 12 , long_period = 26 , signal_period = 9 )
    if  mcd[-1]> signals[-1] and mcd[-2]>=signals[-2] and mcd[-3]<signals[-3] and mcd[-4]<signals[-2] and mcd[-5]<signals[-2]:
        return 'buy'
    elif mcd[-1]< signals[-1] and mcd[-2]<=signals[-2] and mcd[-3]>signals[-3] and mcd[-4]>signals[-2] and mcd[-5]>signals[-2]:
        return 'sell'
    else:
        return False



def tokyo_vol(symbol):

    high = time_high_low(symbol, 0, 8, '1h',8, 120)['high']
    low = time_high_low(symbol, 0, 8, '1h',8, 120)['low']

    return high - low



def london_vol(symbol):

    high = time_high_low(symbol, 7, 15, '1h',8, 120)['high']
    low = time_high_low(symbol, 7, 15, '1h',8, 120)['low']

    return high - low


def new_york_vol(symbol):

    high = time_high_low(symbol, 13, 21, '1h',8, 120)['high']
    low = time_high_low(symbol, 13, 21, '1h',8, 120)['low']

    return high - low



def tokyo_hl(symbol , hl):

    high = time_high_low(symbol, 0, 8, '1h',8, 120)['high']
    low = time_high_low(symbol, 0, 8, '1h',8, 120)['low']
    if hl == 'h':
        return high
    else:
        return low



def london_hl(symbol,hl):

    high = time_high_low(symbol, 7, 15, '1h',8, 120)['high']
    low = time_high_low(symbol, 7, 15, '1h',8, 120)['low']

    if hl == 'h':
        return high
    else:
        return low


def new_york_hl(symbol,hl):

    high = time_high_low(symbol, 13, 21, '1h',8, 120)['high']
    low = time_high_low(symbol, 13, 21, '1h',8, 120)['low']

    if hl == 'h':
        return high
    else:
        return low



def half_trend(symbol, timeframe, amplitude=2, channel_deviation=2):
    ohlc = kandel(timeframe, amplitude * 20, symbol)
    df = ohlc[:]

    df['high_price'] = df['high'].rolling(window=amplitude).max()
    df['low_price'] = df['low'].rolling(window=amplitude).min()

    df['TR'] = np.maximum(df['high'] - df['low'], 
    np.maximum(abs(df['high'] - df['close'].shift(1)), 
    abs(df['low'] - df['close'].shift(1))))
    df['ATR'] = df['TR'].rolling(window=100).mean() / 2
    df['Dev'] = channel_deviation * df['ATR']
 
    df['high_ma'] = df['high'].rolling(window=amplitude).mean()
    df['low_ma'] = df['low'].rolling(window=amplitude).mean()

    df['trend'] = 0
    df['max_low_price'] = df['low'].shift(1).copy()
    df['min_high_price'] = df['high'].shift(1).copy()
    df['up'] = 0.0
    df['down'] = 0.0
    df['HalfTrend'] = np.nan
 
    for i in range(1, len(df)):
        if df.at[i - 1, 'trend'] == 1:
            df.at[i, 'max_low_price'] = max(df.at[i, 'low_price'], df.at[i - 1, 'max_low_price'])

            if df.at[i, 'high_ma'] < df.at[i, 'max_low_price'] and df.at[i, 'close'] < df.at[i - 1, 'low']:
                df.at[i, 'trend'] = 0
                df.at[i, 'min_high_price'] = df.at[i, 'high_price']
            else:
                df.at[i, 'trend'] = df.at[i - 1, 'trend']
        else:
            df.at[i, 'min_high_price'] = min(df.at[i, 'high_price'], df.at[i - 1, 'min_high_price'])

            if df.at[i, 'low_ma'] > df.at[i, 'min_high_price'] and df.at[i, 'close'] > df.at[i - 1, 'high']:
                df.at[i, 'trend'] = 1
                df.at[i, 'max_low_price'] = df.at[i, 'low_price']
            else:
                df.at[i, 'trend'] = df.at[i - 1, 'trend']

        if df.at[i, 'trend'] == 0:
            df.at[i, 'up'] = max(df.at[i, 'max_low_price'], df.at[i - 1, 'up'] if i > 0 else df.at[i, 'max_low_price'])
        else:
            df.at[i, 'down'] = min(df.at[i, 'min_high_price'], df.at[i - 1, 'down'] if i > 0 else df.at[i, 'min_high_price'])

        df.at[i, 'HalfTrend'] = df.at[i, 'up'] if df.at[i, 'trend'] == 0 else df.at[i, 'down']

    positions = ['long' if df.at[i, 'HalfTrend'] <= df.at[i, 'close'] else 'short' for i in range(len(df))]

    return positions


def half_signal(symbol, timeframe, amplitude=2, channel_deviation=2) :
    half = half_trend(symbol, timeframe, amplitude, channel_deviation)

    if half[-3] == 'short' and half[-2] == 'long' :
        return 'buy'
    elif half[-3] == 'long' and half[-2] == 'short' :
        return 'sell'
    else :
        return 'hold'
    

today = datetime.datetime.today().strftime('%A')


def winRate(symbol , timeframe , type='sell' , risk=None):
    
    if symbol in  ['XAUUSD' , 'XAUUSD.' , 'XAUUSD_i'] : 
        m = 1
    if  symbol in ['EURUSD' , 'GBPUSD'  , 'USDCHF' , 'AUDUSD' , 'EURUSD.' , 'EURUSD_i' , 'GBPUSD.' , 'GBPUSD_i' , 'USDCHF.' , 'USDCHF_i' , 'AUDUSD.' , 'AUDUSD_i']  :
        m = 0.0002
        
    win = 50
    
    half = half_trend(symbol , timeframe)
    p_sar = sar(symbol , timeframe , 0.01 , 0.1)
    s_s = sar_signal(symbol , timeframe , 0.01 , 0.1)
    h_s = half_signal(symbol , timeframe)
    mcd = cross_macd(symbol , timeframe , 34 , 144)
    ts = cross_tsi(symbol , timeframe )
    rsii =  rsi('1m' , symbol )
    rsiii =  rsi(timeframe , symbol )
    kandel_now = whatKandel(timeframe , -1 , symbol)
    histogram = macd(symbol , timeframe , 'histogram' , 34 , 144)[-1]
    if type == 'sell':
        
        if kandel_now == 'long':
            win -= 5
          
        if histogram > 0:
            win -= 5
            
              
        priceWin = mt5.symbol_info_tick(symbol).bid
        if check_time(13 , 16) :
            
            if priceWin < london_hl(symbol , 'h') - london_vol(symbol) / 2 or tokyo_hl(symbol , 'l') > london_hl(symbol , 'l'):
                win += 5
        
        if check_time(7 , 10) :
            if priceWin < tokyo_hl(symbol , 'h') - tokyo_vol(symbol) / 2:
                win += 3
        
        if half[-1] == 'short':
            win += 5
        if half[-2] == 'short':
            win += 2 
        if p_sar[-1] > priceWin:
            win += 5 
        if s_s == 'short' or h_s == 'sell' :
            win += 7 
        if mcd == 'sell' or ts == 'sell':
            win += 7 
            
        if rsii <= 25 or rsiii <= 35 :
            win -= 20 
        if is_news() == True:
            win -= 30

        if check_time(7 , 15) and tokyo_vol(symbol) < m*15 :
            win += 2

        if check_time(7 , 15) and tokyo_vol(symbol) < m*12 :
            win += 2
        
        if check_time(7 , 15) and tokyo_vol(symbol) < m*10 :
            win += 2

        if check_time(7 , 15) and tokyo_vol(symbol) > m*20 :
            win -= 3
        
        if check_time(7 , 15) and tokyo_vol(symbol) > m*30 :
            win -= 3

        if check_time(3,8):
            win -= 20

        if check_time(19 , 2):
            win -= 30
        
        if check_time(11 , 13):
            win += 10

        if check_time(14 , 17):
            win += 5
        
        if check_time(13 , 19) and tokyo_vol(symbol) > m*15 and london_vol(symbol) > m*20 :
            win -= 5

    else:
        if kandel_now == 'short':
            win -= 5
            
        if histogram < 0:
            win -= 5
            
        priceWin = mt5.symbol_info_tick(symbol).ask
        if check_time(13 , 16) :
            
            if priceWin > london_hl(symbol , 'l') + london_vol(symbol) / 2 or tokyo_hl(symbol , 'h') < london_hl(symbol , 'h'):
                win += 5
        
        if check_time(7 , 10) :
            if priceWin > tokyo_hl(symbol , 'l') + tokyo_vol(symbol) / 2:
                win += 3
        
        if half[-1] == 'long':
            win += 5
        if half[-2] == 'long':
            win += 2 
        if p_sar[-1] < priceWin:
            win += 5 
        if s_s == 'long' or h_s == 'buy' :
            win += 7 
        if mcd == 'buy' or ts == 'buy':
            win += 7 
            
        if rsii >= 75 or rsiii >= 65 :
            win -= 20 
        if is_news() == True:
            win -= 30

        if check_time(7 , 15) and  tokyo_vol(symbol) < m*15:
            win += 2

        if  check_time(7 , 15) and tokyo_vol(symbol) < m*12:
            win += 2
        
        if  check_time(7 , 15) and tokyo_vol(symbol) < m*10:
            win += 2

        if  check_time(7 , 15) and tokyo_vol(symbol) > m*20:
            win -= 3
        
        if  check_time(7 , 15) and tokyo_vol(symbol) > m*30:
            win -= 3

        if check_time(3,8):
            win -= 20

        if check_time(19 , 2):
            win -= 30
        
        if check_time(11 , 13):
            win += 10

        if check_time(14 , 17):
            win += 5
        
        if check_time(13 , 19) and tokyo_vol(symbol) > m*20 and london_vol(symbol) > m*30 :
            win -= 5

    if today == 'Friday' or today == 'Monday':
        win += 10

    if win >= 95:
        win = 95
    if win <= 5 :
        win = 5

    
    if risk == None:
        return win
    else:
        if win >= 80 :
            risk = risk* 2
            return risk
        elif win < 80 and win >= 65:
            risk = risk* 1.2
            return risk
        elif win < 65 and win >= 50:
            risk = risk
            return risk
        elif win < 50 and win >= 40:
            risk = risk / 1.3
            return risk
        elif win < 40 :
            risk = risk / 2
            return risk
        else:
            return risk



def ut_bot(symbol, timeframe, a=2, atr_period=1):
    ohlc = kandel(timeframe, 50, symbol)
    
    candles = pd.DataFrame(ohlc[:], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    high_low = candles['high'] - candles['low']
    high_close = np.abs(candles['high'] - candles['close'].shift())
    low_close = np.abs(candles['low'] - candles['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    candles['ATR'] = tr.rolling(window=atr_period).mean()
    
    candles['nLoss'] = a * candles['ATR']
    
    candles['xATRTrailingStop'] = np.nan
    
    for i in range(1, len(candles)):
        prev_stop = candles.loc[i-1, 'xATRTrailingStop'] if not np.isnan(candles.loc[i-1, 'xATRTrailingStop']) else candles.loc[i, 'close']
        
        if candles.loc[i, 'close'] > prev_stop:
            candles.loc[i, 'xATRTrailingStop'] = max(prev_stop, candles.loc[i, 'close'] - candles.loc[i, 'nLoss'])
        else:
            candles.loc[i, 'xATRTrailingStop'] = min(prev_stop, candles.loc[i, 'close'] + candles.loc[i, 'nLoss'])
    
    candles['position'] = candles.apply(lambda row: 'long' if row['close'] > row['xATRTrailingStop'] else 'short', axis=1)

    position = candles['position'].iloc

    return position


def position_time_check(symbol , comment , timeframe , timezone = 3) : 
    time_map = {
        '1m': 1, '3m': 3, '5m': 5, '10m': 10, 
        '15m': 15, '20m': 20, '30m': 30, 
        '1h': 60, '4h': 240
    }
    time_plus = time_map.get(timeframe, 1)

    def broker_now(h = 0 ) : 
        custom_timezone = datetime.timezone(datetime.timedelta(hours=h))
        return datetime.datetime.now(custom_timezone)
    
    

    # adding history profits
    now = broker_now(timezone)
    from_time = datetime.datetime(now.year, now.month, now.day, tzinfo=now.tzinfo)
    to_time = from_time + datetime.timedelta(days=1)

    history = mt5.history_deals_get(from_time, to_time)
    positions = [i for i in history if i.entry == 0 and i.comment == comment and i.symbol == symbol]


    if len(positions) > 0 : 
        t = positions[-1].time
        dt_time = datetime.datetime.fromtimestamp(t, datetime.UTC)
        aware_dt_time = dt_time.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=timezone)))
        new_time = aware_dt_time + datetime.timedelta(minutes=time_plus)
        if new_time < now : 
            return True
        else : 
            return False
    else : 
        return True


import pandas_ta
def stochrsi(symbol , timeframe , line , rsi_length=14, stoch_length=14, k_period=3, d_period=3):
    candles = candle(timeframe , stoch_length * 10 , symbol)
    df_close = candles['close']
    stoch_rsi = pandas_ta.stochrsi(df_close, length=stoch_length, rsi_length=rsi_length, k=k_period, d=d_period)

    d = stoch_rsi['STOCHRSId_' + str(rsi_length) + '_' + str(stoch_length) + '_' + str(k_period) + '_' + str(d_period)].tolist()
    k = stoch_rsi['STOCHRSIk_' + str(rsi_length) + '_' + str(stoch_length) + '_' + str(k_period) + '_' + str(d_period)].tolist()
    
    return k if line == 'k' else d



def cmo(symbol , timeframe, period):

    ohlc = kandel(timeframe , period*10 , symbol)
    df = pd.DataFrame(ohlc[:])
    prices = df['close']

    delta = np.diff(prices)
    gains = np.where(delta > 0, delta, 0)
    losses = np.where(delta < 0, -delta, 0)

    sum_gains = pd.Series(gains).rolling(window=period).sum()
    sum_losses = pd.Series(losses).rolling(window=period).sum()

    cmo = 100 * (sum_gains - sum_losses) / (sum_gains + sum_losses)
    return cmo



def stochrsi_cross(symbol , timeframe , rsi_length=14, stoch_length=14, k_period=3, d_period=3) :
    d = stochrsi(symbol , timeframe , 'd' , rsi_length, stoch_length, k_period, d_period)
    k = stochrsi(symbol , timeframe , 'k' , rsi_length, stoch_length, k_period, d_period)

    if k[-4] < d[-2] and k[-3] < d[-2] and k[-2] <= d[-2] and k[-1] > d[-1] and d[-2] < 50:
        return 'buy'
    elif  k[-4] > d[-2] and k[-3] > d[-2] and k[-2] >= d[-2] and k[-1] < d[-1] and d[-2] > 50:
        return 'sell'
    else :
        None



def order_block(symbol, timeframe, upOrDown='up', lookback=10, volume_threshold=1.5, use_body=False):
    
    def candle(timeframe='30m', limit=100, symbol='BTCUSD'):
        timeframes = {
            '1m': mt5.TIMEFRAME_M1,
            '3m': mt5.TIMEFRAME_M3,
            '5m': mt5.TIMEFRAME_M5,
            '15m': mt5.TIMEFRAME_M15,
            '30m': mt5.TIMEFRAME_M30,
            '1h': mt5.TIMEFRAME_H1,
            '4h': mt5.TIMEFRAME_H4,
            '1d': mt5.TIMEFRAME_D1,
            '1w': mt5.TIMEFRAME_W1,
            '1mn': mt5.TIMEFRAME_MN1
        }
        
        time = timeframes.get(timeframe, mt5.TIMEFRAME_M30)  
        candles = mt5.copy_rates_from_pos(symbol, time, 0, limit)
        
        if candles is None or len(candles) == 0:
            return pd.DataFrame()  
        
        df = pd.DataFrame(candles, columns=['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume'])
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        df['volume'] = df['tick_volume']  
        return df[['time', 'open', 'high', 'low', 'close', 'volume']]

    ohlc = candle(timeframe, 200, symbol)
    
    def detect_swing(df, length=lookback):
        df['swing_high'] = df['high'][df['high'] == df['high'].rolling(window=length, center=True).max()]
        df['swing_low'] = df['low'][df['low'] == df['low'].rolling(window=length, center=True).min()]
        return df

    ohlc = detect_swing(ohlc, lookback)
    
    avg_volume = ohlc['volume'].rolling(window=lookback).mean()
    ohlc['high_volume'] = ohlc['volume'] > (avg_volume * volume_threshold)
    
    order_blocks = []
    current_price = ohlc['close'].iloc[-1]
    
    for i in range(len(ohlc)):
        top, bottom = None, None
        
        if pd.notna(ohlc['swing_high'].iloc[i]) and ohlc['high_volume'].iloc[i]:
            top = ohlc['high'].iloc[i] if not use_body else max(ohlc['close'].iloc[i], ohlc['open'].iloc[i])
            bottom = ohlc['low'].iloc[i] if not use_body else min(ohlc['close'].iloc[i], ohlc['open'].iloc[i])
            
            if upOrDown == 'up' and top > current_price:
                order_blocks.append({
                    'top': top,
                    'bottom': bottom,
                })

        elif pd.notna(ohlc['swing_low'].iloc[i]) and ohlc['high_volume'].iloc[i]:
            top = ohlc['high'].iloc[i] if not use_body else max(ohlc['close'].iloc[i], ohlc['open'].iloc[i])
            bottom = ohlc['low'].iloc[i] if not use_body else min(ohlc['close'].iloc[i], ohlc['open'].iloc[i])

            if upOrDown == 'down' and bottom < current_price:
                order_blocks.append({
                    'top': top,
                    'bottom': bottom,
                })

    return order_blocks if order_blocks else None


def find_closest_order_block(order_blocks, current_price):
    closest_block = None
    min_distance = float('inf')  

    for block in order_blocks:
        top_distance = abs(block['top'] - current_price)
        bottom_distance = abs(block['bottom'] - current_price)

        if top_distance < min_distance:
            min_distance = top_distance
            closest_block = block['top']
        
        if bottom_distance < min_distance:
            min_distance = bottom_distance
            closest_block = block['bottom']


    return closest_block





def ichimoku_signals(symbol, timeframe, ts_bars=9, ks_bars=26, ssb_bars=52, cs_offset=26, ss_offset=26):
    ohlc = kandel(timeframe, limit=max(ts_bars, ks_bars, ssb_bars) + ss_offset + cs_offset + 50, symbol=symbol)
    candles = pd.DataFrame(list(ohlc))

    if candles.empty or 'high' not in candles or 'low' not in candles or 'close' not in candles:
        raise ValueError("Invalid data received from `kandel`. Check the function output.")
    
    tenkan_sen = (candles['high'].rolling(window=ts_bars).max() + candles['low'].rolling(window=ts_bars).min()) / 2
    kijun_sen = (candles['high'].rolling(window=ks_bars).max() + candles['low'].rolling(window=ks_bars).min()) / 2
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(ss_offset)
    senkou_span_b = ((candles['high'].rolling(window=ssb_bars).max() + candles['low'].rolling(window=ssb_bars).min()) / 2).shift(ss_offset)
    chikou_span = candles['close'].shift(-cs_offset).fillna(candles['close'].iloc[-1])  # رفع NaN

    signals = []
    last_signal = "neutral"

    for i in range(max(ts_bars, ks_bars, ssb_bars) + ss_offset, len(candles)):
        tk_cross_bull = tenkan_sen.iloc[i] > kijun_sen.iloc[i]
        tk_cross_bear = tenkan_sen.iloc[i] < kijun_sen.iloc[i]
        cs_cross_bull = candles['close'].iloc[i] > chikou_span.iloc[i]
        cs_cross_bear = candles['close'].iloc[i] < chikou_span.iloc[i]
        price_above_kumo = candles['close'].iloc[i] > max(senkou_span_a.iloc[i], senkou_span_b.iloc[i])
        price_below_kumo = candles['close'].iloc[i] < min(senkou_span_a.iloc[i], senkou_span_b.iloc[i])

        bullish_signal = tk_cross_bull and cs_cross_bull and price_above_kumo
        bearish_signal = tk_cross_bear and cs_cross_bear and price_below_kumo
        
        if bullish_signal and last_signal != "buy":
            signals.append("buy")
            last_signal = "buy"
        elif bearish_signal and last_signal != "sell":
            signals.append("sell")
            last_signal = "sell"
        else:
            signals.append("neutral")

    return signals



def ichimoku_signals_pro(symbol, timeframe, ts_bars=9, ks_bars=26, ssb_bars=52, cs_offset=26, ss_offset=26):
    ohlc = kandel(timeframe, limit=max(ts_bars, ks_bars, ssb_bars) + ss_offset + cs_offset + 50, symbol=symbol)
    candles = pd.DataFrame(list(ohlc))

    if candles.empty or 'high' not in candles or 'low' not in candles or 'close' not in candles:
        raise ValueError("Invalid data received from `kandel`. Check the function output.")
    
    def heikin_ashi(data):
        ha_data = data.copy()
        ha_data['close'] = (data['open'] + data['high'] + data['low'] + data['close']) / 4
        ha_data['open'] = (data['open'].shift(1) + data['close'].shift(1)) / 2
        ha_data['high'] = ha_data[['open', 'close', 'high']].max(axis=1)
        ha_data['low'] = ha_data[['open', 'close', 'low']].min(axis=1)
        ha_data.iloc[0, ha_data.columns.get_loc('open')] = (data['open'].iloc[0] + data['close'].iloc[0]) / 2  # اولین مقدار open
        return ha_data

    tenkan_sen = (candles['high'].rolling(window=ts_bars).max() + candles['low'].rolling(window=ts_bars).min()) / 2
    kijun_sen = (candles['high'].rolling(window=ks_bars).max() + candles['low'].rolling(window=ks_bars).min()) / 2
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(ss_offset)
    senkou_span_b = ((candles['high'].rolling(window=ssb_bars).max() + candles['low'].rolling(window=ssb_bars).min()) / 2).shift(ss_offset)
    chikou_span = candles['close'].shift(-cs_offset).fillna(candles['close'].iloc[-1])  # رفع NaN

    ha_candles = heikin_ashi(candles)

    signals = []
    last_signal = "neutral"

    for i in range(max(ts_bars, ks_bars, ssb_bars) + ss_offset, len(candles)):
        tk_cross_bull = tenkan_sen.iloc[i] > kijun_sen.iloc[i]
        tk_cross_bear = tenkan_sen.iloc[i] < kijun_sen.iloc[i]
        cs_cross_bull = candles['close'].iloc[i] > chikou_span.iloc[i]
        cs_cross_bear = candles['close'].iloc[i] < chikou_span.iloc[i]
        price_above_kumo = candles['close'].iloc[i] > max(senkou_span_a.iloc[i], senkou_span_b.iloc[i])
        price_below_kumo = candles['close'].iloc[i] < min(senkou_span_a.iloc[i], senkou_span_b.iloc[i])

        bullish_signal = tk_cross_bull and cs_cross_bull and price_above_kumo
        bearish_signal = tk_cross_bear and cs_cross_bear and price_below_kumo

        ha_bullish = ha_candles['close'].iloc[i] > ha_candles['open'].iloc[i]
        ha_bearish = ha_candles['close'].iloc[i] < ha_candles['open'].iloc[i]
        
        if bullish_signal and ha_bullish and last_signal != "buy":
            signals.append("buy")
            last_signal = "buy"
        elif bearish_signal and ha_bearish and last_signal != "sell":
            signals.append("sell")
            last_signal = "sell"
        else:
            signals.append("neutral")

    return signals


def ssl_hybrid(symbol, timeframe):
    df = candle(timeframe , 500 , symbol)

    atr_period = 14
    atr_multiplier = 1
    baseline_length = 60
    continuation_length = 5
    keltner_multiplier = 0.2

    def wma(data, period):
        weights = np.arange(1, period + 1)
        return data.rolling(period).apply(lambda prices: np.dot(prices, weights) / weights.sum(), raw=True)

    def hma(data, period):
        half_length = int(period / 2)
        sqrt_length = int(np.sqrt(period))
        return wma(2 * wma(data, half_length) - wma(data, period), sqrt_length)

    def jma(data, period, phase=3, power=1):
        
        if phase < -100:
            phase_ratio = 0.5
        elif phase > 100:
            phase_ratio = 2.5
        else:
            phase_ratio = phase / 100 + 1.5

        beta = 0.45 * (period - 1) / (0.45 * (period - 1) + 2)
        alpha = beta ** power

        e0 = data.copy()
        e1 = data.copy()
        e2 = data.copy()
        jma_val = data.copy()

        for i in range(1, len(data)):
            e0[i] = (1 - alpha) * data.iloc[i] + alpha * e0[i - 1]
            e1[i] = (data.iloc[i] - e0[i]) * (1 - beta) + beta * e1[i - 1]
            e2[i] = (e0[i] + phase_ratio * e1[i] - jma_val[i - 1]) * (1 - alpha) ** 2 + (alpha ** 2) * e2[i - 1]
            jma_val[i] = e2[i] + jma_val[i - 1]

        return jma_val


    # ATR Calculation
    df['tr'] = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
    df['atr'] = wma(df['tr'], atr_period)
    df['atr+'] = df['close'] + atr_multiplier * df['atr']
    df['atr-'] = df['close'] - atr_multiplier * df['atr']

    # MA Baseline (HMA)
    df['baseline'] = hma(df['close'], baseline_length)

    # Keltner Channel
    df['true_range'] = df['tr']
    df['range_ma'] = wma(df['true_range'], baseline_length)
    df['keltner_upper'] = df['baseline'] + df['range_ma'] * keltner_multiplier
    df['keltner_lower'] = df['baseline'] - df['range_ma'] * keltner_multiplier

    # MA Baseline Color
    df['baseline_color'] = np.where(
        (df['close'] > df['keltner_upper']), 'buy',
        np.where((df['close'] < df['keltner_lower']), 'sell', 'gray')
    )

    # SSL2 Calculation (JMA) using logic from Pine Script
    df['ssl2_high'] = jma(df['high'], continuation_length)
    df['ssl2_low'] = jma(df['low'], continuation_length)

    # Initialize Hlv2 with NaN
    Hlv2 = np.nan * np.ones(len(df))

    # Calculate Hlv2 according to the Pine Script logic
    for i in range(1, len(df)):
        if df['close'].iloc[i] > df['ssl2_high'].iloc[i]:
            Hlv2[i] = 1
        elif df['close'].iloc[i] < df['ssl2_low'].iloc[i]:
            Hlv2[i] = -1
        else:
            Hlv2[i] = Hlv2[i-1]

    # Calculate ssl2 using Hlv2 logic
    sslDown2 = np.where(Hlv2 < 0, df['ssl2_high'], df['ssl2_low'])
    df['ssl2'] = sslDown2

    # Output
    return {
        'atr+': df['atr+'].tolist(),
        'atr-': df['atr-'].tolist(),
        'ssl2': df['ssl2'].tolist(),
        'color': df['baseline_color'].tolist()
    }

def ssl_signal(symbol , timeframe) :

    ssl = ssl_hybrid(symbol , timeframe)['color'][-2]
    ssl1 = ssl_hybrid(symbol , timeframe)['color'][-3]

    if ssl1 != 'buy' and ssl == 'buy' :
        return 'buy'
    elif ssl1 != 'sell' and ssl == 'sell' :
        return 'sell'
    else :
        return 'hold'






def min_last_position(symbol , h=3):
    BROKER_TIMEZONE_OFFSET = datetime.timedelta(hours=h)
    positions = mt5.positions_get(symbol=symbol)
    if not positions or len(positions) == 0:
        return 0 
    last_position_time = max(position.time for position in positions)
    last_position_datetime_utc = datetime.datetime.fromtimestamp(last_position_time, tz=datetime.timezone.utc)
    server_time = mt5.symbol_info_tick(symbol).time
    server_datetime = datetime.datetime.fromtimestamp(server_time, tz=datetime.timezone.utc)
    last_position_datetime_broker = last_position_datetime_utc + BROKER_TIMEZONE_OFFSET
    now_broker = server_datetime + BROKER_TIMEZONE_OFFSET
    difference = now_broker - last_position_datetime_broker
    minutes_passed = difference.total_seconds() / 60

    return round(minutes_passed)




    
    
def ichimoku(symbol, timeframe, conversion_line=9, base_line=26, lagging_span=26, leading_b_period=52):
    import pandas as pd
    
    df = candle(timeframe, 500, symbol)

    def kijun_sen(data, period):
        high = data['high']
        low = data['low']
        return (high.rolling(window=period).max() + low.rolling(window=period).min()) / 2

    tenkan_sen = kijun_sen(df, conversion_line)
    kijun_sen_line = kijun_sen(df, base_line)
    leading_span_a = (tenkan_sen + kijun_sen_line) / 2
    leading_span_b = kijun_sen(df, leading_b_period)
    lagging = df['close'].shift(-lagging_span)
    
    upper_kumo = leading_span_a.combine(leading_span_b, max)
    lower_kumo = leading_span_a.combine(leading_span_b, min)

    cloud_color = [
        "green" if a > b else "red"
        for a, b in zip(leading_span_a.fillna(0), leading_span_b.fillna(0))
    ]

    return {
        'conversion_line': tenkan_sen.tolist(),
        'baseline': kijun_sen_line.tolist(),
        'leading_span_a': leading_span_a.tolist(),
        'leading_span_b': leading_span_b.tolist(),
        'lagging_span': lagging.tolist(),
        'upper_kumo': upper_kumo.tolist(),
        'lower_kumo': lower_kumo.tolist(),
        'cloud': cloud_color
    }
    
    
    
    


def custom_kandel(minutes='24m', symbol='BTCUSD.', limit=100):
    minutes = int(minutes.replace('m', ''))
    total_minutes_needed = minutes * limit * 2
    
    raw_candles = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, total_minutes_needed)
    
    if raw_candles is None or len(raw_candles) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame(raw_candles, columns=['time', 'open', 'high', 'low', 'close', 'tick_volume'])
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    df['aligned_time'] = df['time'].dt.floor(f'{minutes}min')
    
    resampled = df.groupby('aligned_time').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'tick_volume': 'sum'
    }).reset_index()
    
    resampled = resampled.sort_values('aligned_time', ascending=False)
    
    result = resampled.head(limit)
    
    result = result.sort_values('aligned_time').set_index('aligned_time')
    
    return result.iloc


def heiken_ashi_custom(symbol , timeframe , limit=100):

    timeframe = int(timeframe.replace('m', ''))
        
    def custom(symbol , minutes=24, limit=10):
        
        total_minutes_needed = minutes * limit * 2
        
        raw_candles = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, total_minutes_needed)
        
        if raw_candles is None or len(raw_candles) == 0:
            return pd.DataFrame()
        
        df = pd.DataFrame(raw_candles, columns=['time', 'open', 'high', 'low', 'close', 'tick_volume'])
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        df['aligned_time'] = df['time'].dt.floor(f'{minutes}min')
        
        resampled = df.groupby('aligned_time').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'tick_volume': 'sum'
        }).reset_index()
        
        resampled = resampled.sort_values('aligned_time', ascending=False)
        
        result = resampled.head(limit)
        
        result = result.sort_values('aligned_time').set_index('aligned_time')
        
        return result
    
    df = custom(symbol , timeframe , limit)
    
    ha_df = pd.DataFrame(index=df.index)
    
    ha_df['close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4

    ha_df['open'] = 0.0
    ha_df.iloc[0, ha_df.columns.get_loc('open')] = df['open'].iloc[0]
    
    for i in range(1, len(df)):
        ha_df.iloc[i, ha_df.columns.get_loc('open')] = (ha_df['open'].iloc[i-1] + 
                                                          ha_df['close'].iloc[i-1]) / 2
    
    ha_df['high'] = ha_df[['open', 'close']].max(axis=1).combine(df['high'], max)
    ha_df['low'] = ha_df[['open', 'close']].min(axis=1).combine(df['low'], min)
    
    return ha_df.iloc




tokyo = check_time(0 , 8)
londen = check_time(7 , 15)
new_york = check_time(12 , 20)
sydney = check_time(22 , 5)
best_time = check_time(10 , 17)
off_time = check_time(22 , 23)

buy = mt5.ORDER_TYPE_BUY
buy_pending = mt5.ORDER_TYPE_BUY_LIMIT
sell = mt5.ORDER_TYPE_SELL
sell_pending = mt5.ORDER_TYPE_SELL_LIMIT
