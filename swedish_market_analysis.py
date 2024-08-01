import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def read_data(file_path):
    df = pd.read_csv(file_path, sep=';', skiprows=1, parse_dates=['Date'])
    df['Closingprice'] = pd.to_numeric(df['Closingprice'].str.replace(',', ''), errors='coerce')
    df = df[df['Closingprice'] != 0]  # Remove rows with zero prices
    df = df.dropna(subset=['Closingprice'])
    df = df.sort_values('Date')
    return df

def identify_markets(df, threshold=0.20):
    markets = []
    current_market = None
    peak = trough = df.iloc[0]['Closingprice']
    peak_date = trough_date = df.iloc[0]['Date']

    for date, price in zip(df['Date'], df['Closingprice']):
        if current_market is None or current_market == 'Bull':
            if price > peak:
                peak = price
                peak_date = date
            elif price <= peak * (1 - threshold):
                if current_market == 'Bull':
                    markets.append(('Bull', trough_date, peak_date, trough, peak))
                current_market = 'Bear'
                trough = price
                trough_date = date
        
        if current_market is None or current_market == 'Bear':
            if price < trough:
                trough = price
                trough_date = date
            elif price >= trough * (1 + threshold):
                if current_market == 'Bear':
                    markets.append(('Bear', peak_date, trough_date, peak, trough))
                current_market = 'Bull'
                peak = price
                peak_date = date

    # Add the last market
    if current_market == 'Bull':
        markets.append(('Bull', trough_date, df.iloc[-1]['Date'], trough, df.iloc[-1]['Closingprice']))
    elif current_market == 'Bear':
        markets.append(('Bear', peak_date, df.iloc[-1]['Date'], peak, df.iloc[-1]['Closingprice']))

    return markets

def plot_markets(df, markets):
    for i, (market_type, start_date, end_date, start_price, end_price) in enumerate(markets):
        market_data = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        
        plt.figure(figsize=(10, 6))
        plt.plot(market_data['Date'], market_data['Closingprice'], 
                 color='green' if market_type == 'Bull' else 'red')
        plt.title(f"{market_type} Market {i+1}: {start_date.date()} to {end_date.date()}")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.grid(True)
        plt.savefig(f"{market_type.lower()}_market_{i+1}.png")
        plt.close()

def save_market_info(markets, file_path):
    with open(file_path, 'w') as f:
        f.write("Identified Bull and Bear Markets:\n")
        for i, (market_type, start_date, end_date, start_price, end_price) in enumerate(markets):
            change = (end_price - start_price) / start_price * 100 if market_type == 'Bull' else (start_price - end_price) / start_price * 100
            f.write(f"{market_type} Market {i+1}: {start_date.date()} to {end_date.date()} (Start: {start_price:.2f}, End: {end_price:.2f}, Change: {change:.2f}%)\n")
            
            f.write(f"\nDebug info for {market_type} Market {i+1}:\n")
            f.write(f"Start date: {start_date}, End date: {end_date}\n")
            f.write(f"Start price: {start_price:.2f}, End price: {end_price:.2f}\n")
            market_data = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
            f.write(f"Min price in period: {market_data['Closingprice'].min():.2f}\n")
            f.write(f"Max price in period: {market_data['Closingprice'].max():.2f}\n")
            f.write(f"Percentage change: {change:.2f}%\n\n")

# Main execution
file_path = '_SE0000744195_2024-07-03.csv'
df = read_data(file_path)

print("Data summary:")
print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
print(f"Price range: {df['Closingprice'].min():.2f} to {df['Closingprice'].max():.2f}")
print(f"Number of rows: {len(df)}")

markets = identify_markets(df)

save_market_info(markets, 'market_analysis_results.txt')
plot_markets(df, markets)

print("Market information has been saved to 'market_analysis_results.txt'")
print("All market plots have been saved as PNG files in the current directory.")