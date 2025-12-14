import os
import datetime as dt
import requests
import pandas as pd

sender = 'Yaya'
receiver = 'Gatsby'
work_dir = os.path.dirname(os.path.abspath(__file__))
cd = os.chdir(work_dir)

now = dt.datetime.now()
today = now.strftime('%Y%m%d')
day_of_week = now.strftime('%A')
date_formatted = now.strftime('%-d %b %Y')
[LAT, LON, CITY] = ['22.285072445851448', '114.22469109446133', 'Hong Kong']
OWM_API_KEY = '0d41faf265e4a5f66790a763d44d2ecd'
AV_API_KEY = '0TM43G8VWTHFT4BQ'
Stock_tickers = ['NVDA', 'MSTR']
Crypto_tickers = ['BTC', 'USDT'] # Format: from BTC to USDT

filename_email_body = f'Email Body by Date/email_body_{today}.html'

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

def get_markets(tickers=Stock_tickers):
    print('Enquiring market data...')
    market_data = pd.DataFrame()
    for ticker in tickers:
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={AV_API_KEY}'
        try:
            response = requests.get(url, timeout=10).json()
            today_data = response['Global Quote']
            closed_price = round(float(today_data['05. price']))
            change_percent = round(float(today_data['10. change percent'].strip('%')), 1)
            as_of = today_data['07. latest trading day']
            new_row = pd.DataFrame([{'Ticker': ticker, 'Price': closed_price, 'Change_pct': change_percent, 'AsOf': as_of}])
            market_data = pd.concat([market_data, new_row], ignore_index=True)
        except Exception as e:
            print(f"{ticker} enquiry failed: {e}")
            new_row = pd.DataFrame([{'Ticker': ticker, 'Price': None, 'Change_pct': None, 'AsOf': None}])
            market_data = pd.concat([market_data, new_row], ignore_index=True)
    return market_data

Stock_data = get_markets()

html_content = f"""
<!DOCTYPE html>
<html>
<head>
<body style="margin:0; padding:0; background:#faf8f6;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#faf8f6; padding:40px 20px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" style="max-width:600px; background:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,0.05); font-family:'Georgia', serif; color:#333333;">
          
          <!-- Header with soft gradient -->
          <tr>
            <td style="background:linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); padding:60px 40px; text-align:center;">
              <h1 style="margin:0; font-size:32px; color:#5d4037; font-weight:normal;">
                Daily Check-in
              </h1>
            </td>
          </tr>
          
          <!-- Body -->
          <tr>
            <td style="padding:50px 40px; font-size:18px; line-height:1.7; color:#4a4a4a; background:#f9f6f0">
              Good <strong>{day_of_week}</strong> morning, {receiver}! It’s <strong>{date_formatted}</strong>, and {CITY}'s got {desc}, feeling like {feels_like}°C.<br><br>
                Market update:<br><br>
                <table border="1" style="border-collapse:collapse; width:80%; margin: 0 auto;"><tr><th style="text-align: center;">Ticker</th><th style="text-align: center;">Price</th><th style="text-align: center;">1D %</th><th style="text-align: center;">As Of</th></tr>{''.join([f'<tr><td style="text-align: center;">{row.Ticker}</td><td style="text-align: center;">{row.Price}</td><td style="text-align: center;">{row.Change_pct}</td><td style="text-align: center;">{row.AsOf}</td></tr>' for row in Stock_data.itertuples()])}</table>
                <br><br>
              <p style="margin:0; font-size:24px; color:#d97706; font-style:italic; text-align:center;">
                Your day starts now — own it!
              </p>
            </td>
          </tr>
          
          <!-- Signature -->
          <tr>
            <td style="background:#fffaf0; padding:40px; text-align:center; font-size:18px; color:#8b6f47;">
              Love,<br>
              <span style="font-size:26px; color:#d97706;">{sender} ♡</span>
            </td>
          </tr>
          
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


with open(filename_email_body, 'w') as f:
    f.write(html_content)

print(f"Email body saved to {filename_email_body}")
print('DONE.')
