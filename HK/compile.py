import os
import datetime as dt
from dateutil.relativedelta import relativedelta
import requests
import pandas as pd
import yfinance as yf
import holidays

sender = os.environ.get('SENDER_NAME')
receiver = os.environ.get('RECEIVER_NAME')
work_dir = os.path.dirname(os.path.abspath(__file__))
cd = os.chdir(work_dir)

now = dt.datetime.now()
today = now.strftime('%Y%m%d')
day_of_week = now.strftime('%A')
date_formatted = now.strftime('%-d %b %Y')
current_date = now.date()

# Check for holidays
us_holidays = holidays.US()
hk_holidays = holidays.HK()
is_holiday = current_date in us_holidays or current_date in hk_holidays
holiday_name = us_holidays.get(current_date) or hk_holidays.get(current_date)

LAT, LON, CITY = map(os.environ.get, ['LAT', 'LON', 'CITY'])
OWM_API_KEY = os.environ.get('OWM_API_KEY')
AV_API_KEY = os.environ.get('AV_API_KEY')
# Stock_tickers = ['NVDA', 'ORCL', 'MSTR']
# Crypto_tickers = ['BTC', 'USDT'] # Format: from BTC to USDT
yf_tickers = ['^GSPC', 'NVDA', 'ORCL', 'MSTR', '^HSI', '9988.HK', '0017.HK', '2202.HK', '000300.SS', '688256.SS', '688795.SS', '688802.SS', '^N225', '^KS11', '000660.KS', '^AXJO', '^TWII', 'TSM', '^STOXX50E', 'ASML', 'BTC-USD', 'JPY=X', 'GC=F', 'CL=F', '^TNX', '^VIX', 'SPAX.PVT', 'OPAI.PVT', 'ANTH.PVT', 'XAAI.PVT']
yf_tickers_indent = ['NVDA', 'ORCL', 'MSTR', '9988.HK', '0017.HK', '2202.HK', '688256.SS', '688795.SS', '688802.SS', '000660.KS', 'TSM', 'ASML']
yf_ticker_urls = {
    '^GSPC': 'https://www.spglobal.com/spdji/en/indices/equity/sp-500/#overview',
    '^HSI': 'https://www.hsi.com.hk/eng',
    '0017.HK': 'https://finance.yahoo.com/quote/0017.HK/',
    '2202.HK': 'https://finance.yahoo.com/quote/2202.HK/',
    '688256.SS': 'https://finance.yahoo.com/quote/688256.SS/',
    '688795.SS': 'https://finance.yahoo.com/quote/688795.SS/',
    '688802.SS': 'https://finance.yahoo.com/quote/688802.SS/'
}

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
        data = yf.download(tickers, period='1d', progress=False)
    elif period == '1mo':
        data = yf.download(tickers, period='1mo', progress=False)
    elif period == 'ytd':
        # Get last trading day of previous year
        prev_year = dt.datetime.now().year - 1
        dec_start = f"{prev_year}-12-20"
        dec_end = f"{prev_year}-12-31"
        dec_data = yf.download(tickers, start=dec_start, end=dec_end, keepna=True)
        last_trading_day = dec_data.index[-1].strftime('%Y-%m-%d')
        
        data = yf.download(tickers, start=last_trading_day, keepna=True)
    else:
        raise ValueError("period must be '1d', '1mo', or 'ytd'")
    
    return data

yf_data = get_yf(yf_tickers, period='ytd')
# print("Index type:", type(yf_data.index))
# print("Sample index values:", yf_data.index[:5])
print(yf_data['Close'].tail(3))

def aggregate_returns(df, tickers):
    close = df['Close']
    
    # Last price - handle missing values by going back in time
    last = close.iloc[-1].copy()
    stale_data = {}  # Track which tickers have stale data
    
    for ticker in tickers:
        if pd.isna(last[ticker]):
            # Search backwards for the first non-missing value
            for i in range(len(close) - 1, -1, -1):
                if pd.notna(close.iloc[i][ticker]):
                    last[ticker] = close.iloc[i][ticker]
                    # Mark as stale if the last valid price is earlier than yesterday (i.e., i < len(close) - 2)
                    if i < len(close) - 2:
                        stale_data[ticker] = True
                    break
    
    # 1D return - search backwards for missing values
    close_1d = close.iloc[-2].copy()
    for ticker in tickers:
        if pd.isna(close_1d[ticker]):
            # Search backwards for the first non-missing value
            for i in range(len(close) - 2, -1, -1):
                if pd.notna(close.iloc[i][ticker]):
                    close_1d[ticker] = close.iloc[i][ticker]
                    break
    
    return_1d = (last / close_1d - 1) * 100
    
    # MTD return - find last trading day of previous month
    current_date = pd.Timestamp.now()
    prev_month_first = (current_date.replace(day=1) - pd.Timedelta(days=1)).replace(day=1)
    prev_month = prev_month_first.month
    prev_month_year = prev_month_first.year
    
    # Get all data from previous month and take last available day
    prev_month_data = close[(close.index.year == prev_month_year) & (close.index.month == prev_month)]
    
    if not prev_month_data.empty:
        close_mtd = prev_month_data.iloc[-1].copy()
        # Search backwards for tickers with missing data in last month
        for ticker in tickers:
            if pd.isna(close_mtd[ticker]):
                for i in range(len(prev_month_data) - 1, -1, -1):
                    if pd.notna(prev_month_data.iloc[i][ticker]):
                        close_mtd[ticker] = prev_month_data.iloc[i][ticker]
                        break
    else:
        close_mtd = close.iloc[0].copy()
    
    return_mtd = (last / close_mtd - 1) * 100
    
    # YTD return - find last trading day of previous year
    prev_year = dt.datetime.now().year - 1
    prev_year_data = close[close.index.year == prev_year]
    
    if not prev_year_data.empty:
        close_ytd = prev_year_data.iloc[-1].copy()
        # Search backwards for tickers with missing data in previous year
        for ticker in tickers:
            if pd.isna(close_ytd[ticker]):
                for i in range(len(prev_year_data) - 1, -1, -1):
                    if pd.notna(prev_year_data.iloc[i][ticker]):
                        close_ytd[ticker] = prev_year_data.iloc[i][ticker]
                        break
    else:
        close_ytd = close.iloc[0].copy()
    
    return_ytd = (last / close_ytd - 1) * 100
    
    # For ^TNX and ^VIX, calculate absolute differences instead
    if '^TNX' in tickers:
        return_1d['^TNX'] = last['^TNX'] - close_1d['^TNX']
        return_mtd['^TNX'] = last['^TNX'] - close_mtd['^TNX']
        return_ytd['^TNX'] = last['^TNX'] - close_ytd['^TNX']
    if '^VIX' in tickers:
        return_1d['^VIX'] = last['^VIX'] - close_1d['^VIX']
        return_mtd['^VIX'] = last['^VIX'] - close_mtd['^VIX']
        return_ytd['^VIX'] = last['^VIX'] - close_ytd['^VIX']
    
    # Build summary table
    summary = pd.DataFrame({
        'Last': last,
        '1D': return_1d,
        'MTD': return_mtd,
        'YTD': return_ytd
    })
    
    # Reorder to match original ticker order
    summary = summary.reindex(tickers)
    
    # Format Last column without asterisk
    summary['Last'] = summary.apply(
        lambda row: f"{row['Last']:.2f}" if row.name in ['^TNX', '^VIX'] and pd.notna(row['Last'])
        else (f"{row['Last']:,.0f}" if pd.notna(row['Last']) else "N/A"),
        axis=1
    )
    
    # Format percentages, handling NaN values
    # For ^TNX and ^VIX, format as absolute difference instead of percentage
    summary['1D'] = summary.apply(
        lambda row: "-" if row.name in ['^TNX', '^VIX'] and pd.notna(row['1D']) and row['1D'] == 0.00
        else (f"{row['1D']:+.2f}" if row.name in ['^TNX', '^VIX'] and pd.notna(row['1D'])
        else ("-" if pd.notna(row['1D']) and row['1D'] == 0.00 else (f"{row['1D']:.1f}%" if pd.notna(row['1D']) else "-"))),
        axis=1
    )
    summary['MTD'] = summary.apply(
        lambda row: f"{row['MTD']:+.2f}" if row.name in ['^TNX', '^VIX'] and pd.notna(row['MTD'])
        else ("-" if pd.notna(row['MTD']) and row['MTD'] == 0.00 else (f"{row['MTD']:.0f}%" if pd.notna(row['MTD']) else "-")),
        axis=1
    )
    summary['YTD'] = summary.apply(
        lambda row: f"{row['YTD']:+.2f}" if row.name in ['^TNX', '^VIX'] and pd.notna(row['YTD'])
        else ("-" if pd.notna(row['YTD']) and row['YTD'] == 0.00 else (f"{row['YTD']:.0f}%" if pd.notna(row['YTD']) else "-")),
        axis=1
    )
    
    return summary, stale_data

yf_summary, stale_tickers = aggregate_returns(yf_data, yf_tickers)
print(yf_summary.head(3))

def get_color_for_value(value_str, ticker):
    """
    Generate background color for a return value.
    Returns RGB color string for use in HTML style attribute.
    """
    # Handle N/A and dash
    if value_str in ['-', 'N/A']:
        return 'background-color: transparent;'
    
    # Extract numeric value
    try:
        # Remove % sign and convert to float
        value = float(value_str.replace('%', '').replace('+', ''))
    except:
        return 'background-color: transparent;'
    
    # Determine the scale based on ticker
    if ticker == '^TNX':
        # For ^TNX, use ±0.5 as the cap
        cap = 0.5
    elif ticker == '^VIX':
        # For ^VIX, use ±10 as the cap
        cap = 10.0
    else:
        # For regular tickers, use ±20% as the cap
        cap = 20.0
    
    # Normalize value to -1 to 1 range
    normalized = max(-1.0, min(1.0, value / cap))
    
    # For ^TNX and ^VIX, reverse the color logic (increases are red, decreases are green)
    if ticker in ['^TNX', '^VIX']:
        normalized = -normalized
    
    # Generate color
    if normalized > 0:
        # Green scale: from neutral (240,240,240) to green (0,150,0)
        intensity = int(normalized * 255)
        red = max(240 - int(normalized * 240), 0)
        green = min(240 + int(normalized * 15), 255)
        blue = max(240 - int(normalized * 240), 0)
    elif normalized < 0:
        # Red scale: from neutral (240,240,240) to red (200,0,0)
        intensity = abs(normalized)
        red = min(240 + int(intensity * 15), 255)
        green = max(240 - int(intensity * 240), 0)
        blue = max(240 - int(intensity * 240), 0)
    else:
        # Zero: neutral gray
        red, green, blue = 240, 240, 240
    
    return f'background-color: rgb({red},{green},{blue});'

# Set greeting and signoff based on day of week and holidays
if is_holiday:
    holiday_suffix = f" {holiday_name}"
    signoff_message = "Enjoy your holiday!"
else:
    holiday_suffix = ""
    if day_of_week == 'Sunday':
        signoff_message = "Enjoy your weekend!"
    elif day_of_week == 'Saturday':
        signoff_message = "Enjoy your weekend!"
    elif day_of_week == 'Monday':
        signoff_message = "Wish you a great week ahead!"
    else:
        signoff_message = "Your day starts now — own it!"

market_message = "Here's your customised Market Roundup:"

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
              Good <strong>{day_of_week}</strong> morning, {receiver}! It's <strong>{date_formatted}</strong></strong>{holiday_suffix}</strong>, and {CITY}'s got {desc}, feeling like {feels_like}°C.<br><br>
                {market_message}<br><br>
                <table border="1" style="border-collapse:collapse; width:100%; margin: 0 auto; font-size:14px;"><tr><th style="text-align: center; padding:8px;">Ticker</th><th style="text-align: center; padding:8px;">Last</th><th style="text-align: center; padding:8px;">1D</th><th style="text-align: center; padding:8px;">MTD</th><th style="text-align: center; padding:8px;">YTD</th></tr>{''.join([f'<tr><td style="text-align: left; padding:6px; padding-left:{"20px" if ticker in yf_tickers_indent else "6px"};"><a href="{yf_ticker_urls[ticker]}" style="color: #0066cc; text-decoration: none;">{ticker}</a>{"*" if ticker in stale_tickers else ""}</td><td style="text-align: right; padding:6px;">{row["Last"]}</td><td style="text-align: right; padding:6px; {get_color_for_value(row["1D"], ticker)}">{row["1D"]}</td><td style="text-align: right; padding:6px; {get_color_for_value(row["MTD"], ticker)}">{row["MTD"]}</td><td style="text-align: right; padding:6px; {get_color_for_value(row["YTD"], ticker)}">{row["YTD"]}</td></tr>' if ticker in yf_ticker_urls else f'<tr><td style="text-align: left; padding:6px; padding-left:{"20px" if ticker in yf_tickers_indent else "6px"};">{ticker}{"*" if ticker in stale_tickers else ""}</td><td style="text-align: right; padding:6px;">{row["Last"]}</td><td style="text-align: right; padding:6px; {get_color_for_value(row["1D"], ticker)}">{row["1D"]}</td><td style="text-align: right; padding:6px; {get_color_for_value(row["MTD"], ticker)}">{row["MTD"]}</td><td style="text-align: right; padding:6px; {get_color_for_value(row["YTD"], ticker)}">{row["YTD"]}</td></tr>' for ticker, row in yf_summary.iterrows()])}</table>
                <br><p style="margin:0; font-size:12px; color:#888; font-style:italic;">* for delayed</p>
                <br><br>
              <p style="margin:0; font-size:20px; color:#d97706; font-style:italic; text-align:center;">
                {signoff_message}
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
