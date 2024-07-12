import requests
from datetime import datetime, timedelta
import csv
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Replace this with your actual Alpha Vantage API key
api_key = os.getenv('ALPHA_VANTAGE_API_KEY')

# Path to the default SP500 CSV file
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# DEFAULT_CSV_PATH = os.path.join(BASE_DIR, 'constants', 'sp500.csv')
# USER_STOCK_CSV_PATH = os.path.join(BASE_DIR, 'constants', 'user_stock_data.csv')

DEFAULT_CSV_PATH = "https://stock-insight-api.onrender.com/constants/sp500.csv"
USER_STOCK_CSV_PATH = "https://stock-insight-api.onrender.com/constants/user_stock_data.csv"
app.logger.info(f"Attempting to write to: {DEFAULT_CSV_PATH}")

def get_stock_data(symbol, days=90):
    base_url = "https://www.alphavantage.co/query"

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key,
        "outputsize": "full"  # This will give you up to 20+ years of data
    }

    print(f"Making request to {base_url} with params:")
    print(params)

    response = requests.get(base_url, params=params)

    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")  

    if response.status_code == 200:
        data = response.json()

        # Extract the last 90 days of data
        time_series = data.get("Time Series (Daily)", {})
        dates = sorted(time_series.keys(), reverse=True)[:days]

        result = []
        for date in dates:
            values = time_series[date]
            result.append({
                "Date": date,
                "Open": values['1. open'],
                "High": values['2. high'],
                "Low": values['3. low'],
                "Close": values['4. close']
            })

        # Sort the result in reverse order (earliest to latest)
        result.sort(key=lambda x: x["Date"])

        return result
    else:
        print(f"Error response body: {response.text}")
        return None

# def get_stock_data(symbol, days=90):
#     base_url = "https://api.finage.co.uk/history/stock/open-close"
    
#     end_date = datetime.now()
#     start_date = end_date - timedelta(days=days)
    
#     result = []
#     for i in range(days):
#         date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
#         params = {
#             "stock": symbol,
#             "date": date,
#             "apikey": api_key
#         }
        
#         print(f"Making request to {base_url} with params:")
#         print(params)
        
#         response = requests.get(base_url, params=params)
        
#         print(f"Response status code: {response.status_code}")
#         print(f"Response content: {response.text}")
        
#         if response.status_code == 200:
#             data = response.json()
            
#             if data:
#                 result.append({
#                     "Date": data['date'],
#                     "Open": str(data['open']),
#                     "High": str(data['high']),
#                     "Low": str(data['low']),
#                     "Close": str(data['close'])
#                 })
#         else:
#             print(f"Error response body: {response.text}")
    
#     # Sort the result (earliest to latest)
#     result.sort(key=lambda x: x["Date"])
#     return result if result else None

def save_to_csv(data, filename):
    print(f"Attempting to write to: {os.path.abspath(filename)}")
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Date', 'Open', 'High', 'Low', 'Close']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in data:
            writer.writerow(row)

@app.route('/api/stock')
def fetch_stock_data():
    symbol = request.args.get('symbol')

    if not symbol:
        return jsonify({"message": "Using default SP500 data", "csvPath": DEFAULT_CSV_PATH, "success": True})

    try:
        stock_data = get_stock_data(symbol)

        if stock_data:
            try:
                save_to_csv(stock_data, USER_STOCK_CSV_PATH)
                return jsonify({"message": f"Data saved for {symbol}", "csvPath": "https://stock-insight-api.onrender.com/constants/user_stock_data.csv", "success": True})
            except Exception as e:
                app.logger.error(f"Error saving CSV: {str(e)}")
                return jsonify({"message": f"Failed to save data for {symbol}", "error": str(e), "success": False}), 500
        else:
            return jsonify({"message": "No data retrieved from API", "success": False}), 400
    except Exception as e:
        app.logger.error(f"Error in fetch_stock_data: {str(e)}")
        return jsonify({"message": "Failed to retrieve stock data", "error": str(e), "success": False}), 500

@app.route('/api/something')
def returnSomething():
    print("This is working")
    return "This is working"

@app.route('/constants/<path:filename>')
def serve_csv(filename):
    # return send_from_directory(os.path.join(BASE_DIR, 'constants'), filename)
    return send_from_directory('constants', filename)

if __name__ == '__main__':
    app.run(debug=True)

