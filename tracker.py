import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os

# --- CONFIGURATION ---
URL = "https://www.maizetix.com/games/398"
TARGET_PRICE = 70.00
CSV_FILENAME = "ticket_prices.csv"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK") 

def get_current_lowest_price(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Check stats box
        lowest_price_box = soup.find('div', string='Lowest Price')
        if lowest_price_box:
            price_text = lowest_price_box.find_next_sibling('div', class_='info-stats-number').text
            return float(price_text.replace('$', ''))

        # Fallback to table
        prices = []
        for row in soup.select('.games-table tbody tr'):
            cols = row.find_all('td')
            if len(cols) > 1:
                try:
                    prices.append(float(cols[1].text.strip().replace('$', '')))
                except ValueError:
                    continue
        
        return min(prices) if prices else None
            
    except Exception:
        return None

def log_price(price):
    file_exists = os.path.isfile(CSV_FILENAME)
    with open(CSV_FILENAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Price"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), price])

def send_discord_message(price, is_alert):
    if not WEBHOOK_URL:
        return
    
    # Format the message depending on whether it's an alert or just an update
    if is_alert:
        content = f"🚨 **TICKET DROP ALERT!** 🚨\nMichigan vs MSU is down to **${price:.2f}**!\nBuy here: {URL}"
    else:
        content = f"ℹ️ **Hourly Update:** The current lowest price is **${price:.2f}**."
        
    data = {
        "content": content
    }
    requests.post(WEBHOOK_URL, json=data)

def main():
    current_price = get_current_lowest_price(URL)
    
    if current_price is not None:
        log_price(current_price)
        
        # Check the price and send the appropriate message type
        if current_price < TARGET_PRICE:
            send_discord_message(current_price, is_alert=True)
        else:
            send_discord_message(current_price, is_alert=False)

if __name__ == "__main__":
    main()
