import os
import datetime as dt
from dateutil.relativedelta import relativedelta
import requests
import pandas as pd
import yfinance as yf

sender = os.environ.get('SENDER_NAME')
receiver = os.environ.get('RECEIVER_NAME')
work_dir = os.path.dirname(os.path.abspath(__file__))
cd = os.chdir(work_dir)

now = dt.datetime.now()
today = now.strftime('%Y%m%d')
day_of_week = now.strftime('%A')
date_formatted = now.strftime('%-d %b %Y')
LAT, LON, CITY = map(os.environ.get, ['LAT', 'LON', 'CITY'])
OWM_API_KEY = os.environ.get('OWM_API_KEY')
AV_API_KEY = os.environ.get('AV_API_KEY')
# Stock_tickers = ['NVDA', 'ORCL', 'MSTR']
# Crypto_tickers = ['BTC', 'USDT'] # Format: from BTC to USDT
yf_tickers = ['^GSPC', 'NVDA', 'ORCL', 'MSTR', '^HSI', '9988.HK', '688795.SS']

# filename_email_body = f'Email Body by Date/email_body_{today}.html'
filename_email_send = f'output.html'

def get_weather():
    print('Enquiring weather...')
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric&lang=en"
    try:
        res = requests.get(url, timeout=10).json()
        
        current_temp = int(res['main']['temp'])
        high_temp = int(res['main']['temp_max'])
        low_temp = int(res['main']['temp_min'])
        feels_like = int(res['main']['feels_like'])

        return {
            'feels_like': feels_like,
            # "temp": current_temp,
            # "high": high_temp,
            # "low": low_temp,
            "desc": res['weather'][0]['main'],
            "weather_icon": f"https://openweathermap.org/img/wn/{res['weather'][0]['icon']}@2x.png"
        }
    except Exception as e:
        print(f"Weather equiry failed: {e}")
        return None
weather_data = get_weather()
feels_like = weather_data['feels_like'] if weather_data else 'N/A'
desc = weather_data['desc'] if weather_data else ''
weather_icon = weather_data['weather_icon'] if weather_data else ''

# def get_markets(tickers=Stock_tickers):
#     print('Enquiring market data...')
#     market_data = pd.DataFrame()
#     for ticker in tickers:
#         url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={AV_API_KEY}'
#         try:
#             response = requests.get(url, timeout=10).json()
#             today_data = response['Global Quote']
#             closed_price = round(float(today_data['05. price']))
#             change_percent = round(float(today_data['10. change percent'].strip('%')), 1)
#             as_of = today_data['07. latest trading day']
#             new_row = pd.DataFrame([{'Ticker': ticker, 'Price': closed_price, 'Change_pct': change_percent, 'AsOf': as_of}])
#             market_data = pd.concat([market_data, new_row], ignore_index=True)
#         except Exception as e:
#             print(f"{ticker} enquiry failed: {e}")
#             new_row = pd.DataFrame([{'Ticker': ticker, 'Price': None, 'Change_pct': None, 'AsOf': None}])
#             market_data = pd.concat([market_data, new_row], ignore_index=True)
#     return market_data

# Stock_data = get_markets()

def get_yf(tickers, period='ytd'):
    """
    Fetch historical price data from Yahoo Finance.
    
    Args:
        tickers: A single ticker string or list of ticker strings
        period: '1d', '1mo', or 'ytd'
    
    Returns:
        DataFrame with historical price data
    """
    if period == '1d':
        data = yf.download(tickers, period='1d')
    elif period == '1mo':
        data = yf.download(tickers, period='1mo')
    elif period == 'ytd':
        # Get last trading day of previous year
        prev_year = dt.datetime.now().year - 1
        dec_start = f"{prev_year}-12-20"
        dec_end = f"{prev_year}-12-31"
        dec_data = yf.download(tickers, start=dec_start, end=dec_end)
        last_trading_day = dec_data.index[-1].strftime('%Y-%m-%d')
        
        data = yf.download(tickers, start=last_trading_day)
    else:
        raise ValueError("period must be '1d', '1mo', or 'ytd'")
    
    return data

yf_data = get_yf(yf_tickers, period='ytd')
# print(yf_data['Close'])

def aggregate_returns(df, tickers):
    close = df['Close']
    
    # Last price
    last = close.iloc[-1]
    
    # 1D return
    return_1d = (close.iloc[-1] / close.iloc[-2] - 1) * 100
    
    # 1M return - find the closest trading day to one month ago
    one_month_ago = dt.datetime.now() - relativedelta(months=1)
    close_1m = close[close.index <= one_month_ago].iloc[-1]
    return_1m = (close.iloc[-1] / close_1m - 1) * 100
    
    # YTD return - find last trading day of previous year
    prev_year = dt.datetime.now().year - 1
    prev_year_data = close[close.index.year == prev_year]
    close_ytd = prev_year_data.iloc[-1]
    return_ytd = (close.iloc[-1] / close_ytd - 1) * 100
    
    # Build summary table
    summary = pd.DataFrame({
        'Last': last,
        '1D': return_1d,
        '1M': return_1m,
        'YTD': return_ytd
    })
    
    # Reorder to match original ticker order
    summary = summary.reindex(tickers)
    
    summary['1D'] = summary['1D'].apply(lambda x: f"{x:.1f}%")
    summary['1M'] = summary['1M'].apply(lambda x: f"{x:.1f}%")
    summary['YTD'] = summary['YTD'].apply(lambda x: f"{x:.0f}%")
    
    return summary

yf_summary = aggregate_returns(yf_data, yf_tickers)


print('Compiling email body...')
html_content = f"""
<!DOCTYPE html>
<html>
<head>
<body style="margin:0; padding:0; background:#faf8f6;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#faf8f6; padding:20px 10px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width:500px; background:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,0.05); font-family:'Georgia', serif; color:#333333;">
          
          <!-- Header with soft gradient -->
          <tr>
            <td style="background:linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); padding:40px 30px; text-align:center;">
              <h1 style="margin:0; font-size:28px; color:#5d4037; font-weight:normal;">
                Daily Check-in
              </h1>
            </td>
          </tr>
          
          <!-- Body -->
          <tr>
            <td style="padding:35px 30px; font-size:16px; line-height:1.6; color:#4a4a4a; background:#f9f6f0">
              Good <strong>{day_of_week}</strong> morning, {receiver}! It's <strong>{date_formatted}</strong>, and {CITY}'s got {desc}, feeling like {feels_like}°C.<br><br>
                Market update:<br><br>
                <table border="1" style="border-collapse:collapse; width:100%; margin: 0 auto; font-size:14px;"><tr><th style="text-align: center; padding:8px;">Ticker</th><th style="text-align: center; padding:8px;">Last</th><th style="text-align: center; padding:8px;">1D</th><th style="text-align: center; padding:8px;">1M</th><th style="text-align: center; padding:8px;">YTD</th></tr>{''.join([f'<tr><td style="text-align: center; padding:6px;">{ticker}</td><td style="text-align: center; padding:6px;">{row["Last"]:,.0f}</td><td style="text-align: center; padding:6px;">{row["1D"]}</td><td style="text-align: center; padding:6px;">{row["1M"]}</td><td style="text-align: center; padding:6px;">{row["YTD"]}</td></tr>' for ticker, row in yf_summary.iterrows()])}</table>
                <br><br>
              <p style="margin:0; font-size:20px; color:#d97706; font-style:italic; text-align:center;">
                Your day starts now — own it!
              </p>
            </td>
          </tr>
          
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


with open(filename_email_send, 'w') as f:
    f.write(html_content)

# print(f"Email body saved to {filename_email_body}")
print(f"Compiled: {filename_email_send}")
print('DONE.')
