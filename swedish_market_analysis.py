import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta

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
    threshold_date = threshold_price = None

    for date, price in zip(df['Date'], df['Closingprice']):
        if current_market is None or current_market == 'Bull':
            if price > peak:
                peak = price
                peak_date = date
            elif price <= peak * (1 - threshold):
                if current_market == 'Bull':
                    markets.append(('Bull', trough_date, peak_date, trough, peak, threshold_date, threshold_price))
                current_market = 'Bear'
                trough = price
                trough_date = date
                threshold_date = date
                threshold_price = price
        
        if current_market is None or current_market == 'Bear':
            if price < trough:
                trough = price
                trough_date = date
            elif price >= trough * (1 + threshold):
                if current_market == 'Bear':
                    markets.append(('Bear', peak_date, trough_date, peak, trough, threshold_date, threshold_price))
                current_market = 'Bull'
                peak = price
                peak_date = date
                threshold_date = date
                threshold_price = price

    # Add the last market
    if current_market == 'Bull':
        markets.append(('Bull', trough_date, df.iloc[-1]['Date'], trough, df.iloc[-1]['Closingprice'], threshold_date, threshold_price))
    elif current_market == 'Bear':
        markets.append(('Bear', peak_date, df.iloc[-1]['Date'], peak, df.iloc[-1]['Closingprice'], threshold_date, threshold_price))

    return markets

def display_market_plots(df, markets, save_plots=False):
    for i, (market_type, start_date, end_date, start_price, end_price, threshold_date, threshold_price) in enumerate(markets):
        market_data = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(market_data['Date'], market_data['Closingprice'], 
                color='green' if market_type == 'Bull' else 'red',
                linewidth=2)
        
        # Add marker for 20% threshold
        if threshold_date and threshold_price:
            ax.plot(threshold_date, threshold_price, 'bo', markersize=10, 
                    label='20% Threshold Point')
            ax.axvline(x=threshold_date, color='blue', linestyle='--', alpha=0.5)
        
        # Determine appropriate date locator and formatter based on market duration
        duration = end_date - start_date
        if duration <= timedelta(days=90):  # For markets up to ~3 months
            locator = mdates.WeekdayLocator(byweekday=mdates.MO)
            formatter = mdates.DateFormatter('%Y-%m-%d')
        elif duration <= timedelta(days=365):  # For markets up to a year
            locator = mdates.MonthLocator()
            formatter = mdates.DateFormatter('%Y-%m')
        elif duration <= timedelta(days=365*2):  # For markets up to 2 years
            locator = mdates.MonthLocator(interval=3)
            formatter = mdates.DateFormatter('%Y-%m')
        else:  # For markets longer than 2 years
            locator = mdates.YearLocator()
            formatter = mdates.DateFormatter('%Y')
        
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Improve y-axis
        ax.yaxis.set_major_locator(plt.MaxNLocator(10))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        
        ax.set_title(f"{market_type} Market {i+1}: {start_date.date()} to {end_date.date()}", fontsize=14)
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Price", fontsize=12)
        
        ax.grid(True, linestyle='--', alpha=0.7)
        
        if threshold_date and threshold_price:
            ax.legend()
        
        plt.tight_layout()
        
        if save_plots:
            plt.savefig(f"{market_type.lower()}_market_{i+1}.png", dpi=300, bbox_inches='tight')
        else:
            plt.show()
        
        plt.close(fig)

def save_market_info(df, markets, file_path):
    with open(file_path, 'w') as f:
        f.write("Identified Bull and Bear Markets:\n")
        for i, (market_type, start_date, end_date, start_price, end_price, threshold_date, threshold_price) in enumerate(markets):
            change = (end_price - start_price) / start_price * 100 if market_type == 'Bull' else (start_price - end_price) / start_price * 100
            f.write(f"{market_type} Market {i+1}: {start_date.date()} to {end_date.date()} (Start: {start_price:.2f}, End: {end_price:.2f}, Change: {change:.2f}%)\n")
            
            f.write(f"\nDebug info for {market_type} Market {i+1}:\n")
            f.write(f"Start date: {start_date}, End date: {end_date}\n")
            f.write(f"Start price: {start_price:.2f}, End price: {end_price:.2f}\n")
            f.write(f"20% Threshold date: {threshold_date.date() if threshold_date else 'N/A'}\n")
            
            # Carefully handle threshold_price formatting
            if threshold_price is not None and isinstance(threshold_price, (int, float)):
                f.write(f"20% Threshold price: {threshold_price:.2f}\n")
            else:
                f.write(f"20% Threshold price: N/A\n")
            
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

save_market_info(df, markets, 'market_analysis_results.txt')
display_market_plots(df, markets, save_plots=False)  # Set to True to save plots instead of displaying

print("Analysis complete. Results saved to 'market_analysis_results.txt'")