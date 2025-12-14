import os
import requests

work_dir = os.path.dirname(os.path.abspath(__file__))
cd = os.chdir(work_dir)
AV_API_KEY = '0TM43G8VWTHFT4BQ'

def get_listing_status(AV_API_KEY):
    base_url = "https://www.alphavantage.co/query"
    function = "LISTING_STATUS"

    api_url = f"{base_url}?function={function}&apikey={AV_API_KEY}"

    response = requests.get(api_url)

    if response.status_code == 200:
        return response.text
    else:
        return None

Ticker_data = get_listing_status(AV_API_KEY)

if Ticker_data:
    print('Saving CSV...')
    with open('Alpha Vantage Tickers.csv', 'w') as f:
        f.write(Ticker_data)
    print('DONE.')
else:
    print('Failed')