from module.hashem import *
from module.stg_def import *
from module.stg_var import *



def parabolic_STG(symbol , timeframe , buycomment , sellcomment , risk , buy_var , sell_var ):
    

    signal_parabolic = sar_signal(symbol, timeframe , 0.02 , 0.1) #long/short
    signal_half = half_signal(symbol , timeframe , 2 ,2) #buy/sell

    half = half_trend(symbol , timeframe , 2,2)[-1] #long/short
    parabolic = sar(symbol, timeframe , 0.02 , 0.1)[-1]

    price = mt5.symbol_info_tick(symbol).ask

    if ((signal_parabolic == 'long' and half == 'long') or (signal_half == 'buy' and parabolic < price)) and check_time(11 , 15) and buy_var == 0 and whatKandel(timeframe , -1 , symbol) == 'long' and count_position_now('buy' , symbol) == 0 :
            
        risk_p = risk

        sl = parabolic
       
        position_ok = True
        pending_ok = False
        normal_sl = False


        if price - sl >= 9:
            position_ok = False

        elif price - sl < 9 and price - sl >= 6:
            pending_ok = True

        elif price - sl < 6 and price - sl >= 4:
            sl = price - 4

        else:
            normal_sl = True
        

        if winRate(symbol , timeframe ,'buy') > 80:
            tp = price + (( price - sl )*2)
        elif normal_sl == True:
            tp = price + (( price - sl )*5)
        else:
            tp = price + (( price - sl )*1.5)


        new_risk = winRate(symbol , timeframe ,'buy' ,risk_p)

        lot = lot_calculator(symbol , new_risk , price , sl )
        

        #create order
        if price > sl and position_ok == True and pending_ok == False :
            create_order(symbol , lot , buy , price , sl , tp ,buycomment)

        if price > sl and pending_ok == True :
            create_order(symbol , lot/2 , buy , price , sl , tp ,buycomment)
            pending_order(symbol , lot/2 , buy_pending , (price - ((price - sl) /2)) , sl , tp ,buycomment)
        

    #sell
    price = mt5.symbol_info_tick(symbol).bid

    if ((signal_parabolic == 'short' and half == 'short') or (signal_half == 'sell' and parabolic > price)) and check_time(11 , 15) and sell_var == 0 and whatKandel(timeframe , -1 , symbol) == 'short' and count_position_now('sell' , symbol) == 0 :
            
        risk_p = risk

        sl = parabolic
       
        position_ok = True
        pending_ok = False
        normal_sl = False


        if sl - price >= 9:
            position_ok = False

        elif sl - price < 9 and sl - price >= 6:
            pending_ok = True

        elif sl - price < 6 and sl - price >= 4:
            sl = price + 4

        else:
            normal_sl = True
        

        if winRate(symbol , timeframe ,'sell') > 80:
            tp = price - (( sl - price )*2)
        elif normal_sl == True:
            tp = price - (( sl - price )*5)
        else:
            tp = price - (( sl - price )*1.5)

        new_risk = winRate(symbol , timeframe ,'sell' ,risk_p)

        lot = lot_calculator(symbol , new_risk , price , sl)

        #create order
        if price > sl and position_ok == True and pending_ok == False :
            create_order(symbol , lot , sell , price , sl , tp ,sellcomment)

        if price > sl and pending_ok == True :
            create_order(symbol , lot/2 , sell , price , sl , tp ,sellcomment)
            pending_order(symbol , lot/2 , sell_pending , (price + ((sl - price) /2)) , sl , tp ,sellcomment)
        
       

