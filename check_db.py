
import pandas as pd
from database import DatabaseManager

db = DatabaseManager()
print("--- XAGUSD Swings ---")
df = db.load_swings('XAGUSD')
if not df.empty:
    print(df.tail())
    print("Min Price:", df['end_price'].min())
    print("Max Price:", df['end_price'].max())
else:
    print("No swings for XAGUSD")

print("\n--- XAUUSD Swings ---")
df2 = db.load_swings('XAUUSD')
if not df2.empty:
    print(df2.tail())
else:
    print("No swings for XAUUSD")
