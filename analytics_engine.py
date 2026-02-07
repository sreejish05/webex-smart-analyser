import json
import pandas as pd
import os
from datetime import datetime

class ChatAnalyst:
    def __init__(self, json_path):
        self.filepath = json_path
        print(f"📂 Loading data from: {json_path}...")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.raw_messages = data.get('messages', [])
        
        # Convert to Pandas DataFrame for super-fast analysis
        self.df = pd.DataFrame(self.raw_messages)
        
        # Convert timestamps to actual DateTime objects
        if not self.df.empty:
            self.df['created'] = pd.to_datetime(self.df['created'])
            self.df['date'] = self.df['created'].dt.date
            self.df['hour'] = self.df['created'].dt.hour

    def show_basic_stats(self):
        if self.df.empty:
            print("❌ No messages to analyze.")
            return

        print("\n" + "="*40)
        print(f"📊 ANALYTICS REPORT")
        print("="*40)
        print(f"Total Messages:  {len(self.df)}")
        print(f"Date Range:      {self.df['created'].min().date()} to {self.df['created'].max().date()}")
        print(f"Participants:    {self.df['senderName'].nunique()} unique people")
        print(f"Attachments:     {self.df['has_attachments'].sum()} files shared")
        print("="*40 + "\n")

    def get_top_talkers(self, top_n=5):
        """Who sent the most messages?"""
        print(f"🏆 TOP {top_n} CONTRIBUTORS")
        print("-" * 30)
        counts = self.df['senderName'].value_counts().head(top_n)
        for name, count in counts.items():
            print(f"{count:<5} | {name}")
        print("-" * 30 + "\n")

    def get_activity_timeline(self):
        """Which days were the busiest?"""
        print(f"📅 BUSIEST DAYS")
        print("-" * 30)
        daily_counts = self.df['date'].value_counts().head(5)
        for date, count in daily_counts.items():
            print(f"{date} | {count} msgs")
        print("-" * 30 + "\n")

# --- Main Execution ---
if __name__ == "__main__":
    # 1. List available data files
    files = [f for f in os.listdir("data") if f.endswith(".json")]
    
    if not files:
        print("❌ No data found in 'data/' folder. Run harvester first!")
        exit()

    print("Available Datasets:")
    for i, f in enumerate(files):
        print(f"[{i+1}] {f}")
    
    # 2. Select file
    try:
        idx = int(input("\n👉 Select file to analyze: ")) - 1
        selected_file = os.path.join("data", files[idx])
        
        # 3. Run Analysis
        analyst = ChatAnalyst(selected_file)
        analyst.show_basic_stats()
        analyst.get_top_talkers()
        analyst.get_activity_timeline()
        
    except (ValueError, IndexError):
        print("❌ Invalid selection.")
