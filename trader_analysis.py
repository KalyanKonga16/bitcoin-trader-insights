import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib.ticker as mtick

# ==========================================
# CONFIGURATION
# ==========================================
TRADER_DATA_PATH = 'data/historical_data.csv'
SENTIMENT_DATA_PATH = 'data/fear_greed_index.csv'

# ==========================================
# VISUALIZATION STYLING (PROFESSIONAL UPGRADE)
# ==========================================
# Set a clean, modern theme
sns.set_theme(style="whitegrid", context="talk")

# Custom Professional Palette
sentiment_palette = {
    'Extreme Fear': '#d62728', # Red
    'Fear': '#ff7f0e',         # Orange
    'Greed': '#2ca02c',        # Green
    'Extreme Greed': '#1f77b4' # Blue
}

def add_bar_labels(ax, fmt='{:.2f}'):
    """Adds bold data labels to bars with smart positioning."""
    for p in ax.patches:
        height = p.get_height()
        # If bar is positive, label above. If negative, label below.
        xy_pos = (0, 8) if height >= 0 else (0, -20)
        
        ax.annotate(fmt.format(height),
                    (p.get_x() + p.get_width() / 2., height),
                    ha='center', va='center',
                    xytext=xy_pos,
                    textcoords='offset points',
                    fontsize=11, color='black', fontweight='bold')

# ==========================================
# 1. LOAD AND CLEAN (EXACT WORKING LOGIC)
# ==========================================
def load_and_clean_data():
    print("--- 1. LOADING & DIAGNOSING DATA ---")
    
    # 1. Load Trader Data
    if os.path.exists(TRADER_DATA_PATH):
        trader_df = pd.read_csv(TRADER_DATA_PATH)
    elif os.path.exists('historical_data.csv'):
        trader_df = pd.read_csv('historical_data.csv')
    else:
        print(f"CRITICAL ERROR: Could not find trader data.")
        return None, None

    # 2. Load Sentiment Data
    if os.path.exists(SENTIMENT_DATA_PATH):
        sentiment_df = pd.read_csv(SENTIMENT_DATA_PATH)
    elif os.path.exists('fear_greed_index.csv'):
        sentiment_df = pd.read_csv('fear_greed_index.csv')
    else:
        print(f"CRITICAL ERROR: Could not find sentiment data.")
        return None, None

    # Normalize Columns
    trader_df.columns = [c.lower().strip() for c in trader_df.columns]
    sentiment_df.columns = [c.lower().strip() for c in sentiment_df.columns]

    # --- DATE FIXING ---
    
    # 1. Fix Trader Dates
    if 'timestamp' in trader_df.columns and pd.api.types.is_numeric_dtype(trader_df['timestamp']):
        print("-> Using numeric 'timestamp' column for Trader Data...")
        trader_df['datetime'] = pd.to_datetime(trader_df['timestamp'], unit='ms')
    elif 'timestamp ist' in trader_df.columns:
        print("-> Using string 'timestamp ist' column for Trader Data...")
        trader_df['datetime'] = pd.to_datetime(trader_df['timestamp ist'], dayfirst=True, format='mixed', errors='coerce')
    else:
        print("ERROR: Could not find a recognizable time column in Trader Data.")
        return None, None

    # 2. Fix Sentiment Dates
    if 'date' in sentiment_df.columns:
        print("-> Using 'date' column for Sentiment Data...")
        sentiment_df['date_key_raw'] = pd.to_datetime(sentiment_df['date'], dayfirst=True, format='mixed', errors='coerce')
    elif 'timestamp' in sentiment_df.columns:
        print("-> Using 'timestamp' column for Sentiment Data...")
        sentiment_df['date_key_raw'] = pd.to_datetime(sentiment_df['timestamp'], dayfirst=True, format='mixed', errors='coerce')
    else:
         print("ERROR: Could not find a recognizable date column in Sentiment Data.")
         return None, None

    # --- NORMALIZE TO JUST DATE ---
    trader_df['date_key'] = trader_df['datetime'].dt.normalize()
    sentiment_df['date_key'] = sentiment_df['date_key_raw'].dt.normalize()

    # Drop NaTs
    trader_df = trader_df.dropna(subset=['date_key'])
    sentiment_df = sentiment_df.dropna(subset=['date_key'])

    # --- DIAGNOSTIC PRINT ---
    t_min, t_max = trader_df['date_key'].min(), trader_df['date_key'].max()
    s_min, s_max = sentiment_df['date_key'].min(), sentiment_df['date_key'].max()
    
    print(f"\n[DEBUG] Trader Data Date Range:    {t_min.date()} to {t_max.date()}")
    print(f"[DEBUG] Sentiment Data Date Range: {s_min.date()} to {s_max.date()}")
    
    if t_max < s_min or t_min > s_max:
        print("\nCRITICAL WARNING: The date ranges do NOT overlap.")
        
    return trader_df, sentiment_df

# ==========================================
# 2. ANALYZE & VISUALIZE (UPGRADED PLOTS)
# ==========================================
def analyze_and_visualize(trader_df, sentiment_df):
    print("\n--- 2. MERGING & MAPPING ---")
    
    # Merge
    merged_df = pd.merge(trader_df, sentiment_df, on='date_key', how='inner')
    print(f"Merged Rows: {merged_df.shape[0]}")
    
    if merged_df.empty:
        print("ERROR: Merged DataFrame is still empty.")
        return

    # --- INTELLIGENT COLUMN MAPPING ---
    
    # 1. PnL Mapping
    pnl_col = next((c for c in merged_df.columns if 'closed pnl' in c or 'closed_pnl' in c or 'pnl' in c), None)
    if pnl_col:
        if merged_df[pnl_col].dtype == object:
             merged_df['pnl_clean'] = pd.to_numeric(merged_df[pnl_col].astype(str).str.replace(',', '').str.replace('$', ''), errors='coerce')
        else:
             merged_df['pnl_clean'] = merged_df[pnl_col]
    else:
        print("WARNING: PnL column not found.")

    # 2. Leverage Mapping
    lev_col = next((c for c in merged_df.columns if 'leverage' in c), None)
    if lev_col:
        merged_df['lev_clean'] = pd.to_numeric(merged_df[lev_col], errors='coerce')
    else:
        merged_df['lev_clean'] = None

    # 3. Sentiment Value Mapping
    val_col = next((c for c in merged_df.columns if 'value' in c and 'size' not in c), None)
    if val_col:
        merged_df['sentiment_value'] = merged_df[val_col]
        def get_bucket(val):
            try:
                v = float(val)
                if v < 25: return 'Extreme Fear'
                elif v < 50: return 'Fear'
                elif v < 75: return 'Greed'
                else: return 'Extreme Greed'
            except: return 'Unknown'
        merged_df['sentiment_bucket'] = merged_df['sentiment_value'].apply(get_bucket)

    # ==========================================
    # --- 3. GENERATING PLOTS (PROFESSIONAL) ---
    # ==========================================
    print("\n--- 3. GENERATING PROFESSIONAL PLOTS ---")
    if not os.path.exists('images'):
        os.makedirs('images')

    # --- Plot 1: PnL by Sentiment ---
    if 'pnl_clean' in merged_df.columns and 'sentiment_bucket' in merged_df.columns:
        perf = merged_df.groupby('sentiment_bucket')['pnl_clean'].mean()
        order = ['Extreme Fear', 'Fear', 'Greed', 'Extreme Greed']
        perf = perf.reindex([x for x in order if x in perf.index])
        
        plt.figure(figsize=(12, 8))
        ax = sns.barplot(x=perf.index, y=perf.values, palette=sentiment_palette)
        
        # Professional Typography
        plt.title('Average Trader PnL per Sentiment Zone', fontsize=18, fontweight='bold', pad=20)
        plt.ylabel('Average PnL (USD)', fontsize=14, fontweight='bold', labelpad=10)
        
        # Adding Padding to X-Axis Label to prevent merging
        plt.xlabel('Market Sentiment', fontsize=14, fontweight='bold', labelpad=20)
        
        # Adding Padding to Tick Labels (The words "Extreme Fear", etc.)
        ax.tick_params(axis='x', pad=10)
        
        # Strong zero line
        plt.axhline(0, color='black', linewidth=1.5, linestyle='--')
        
        # Clean look
        sns.despine(left=True)
        add_bar_labels(ax, fmt='${:.2f}')
        
        plt.tight_layout()
        plt.savefig('images/pnl_by_sentiment.png', dpi=300)
        print("-> Saved professional images/pnl_by_sentiment.png")
    
    # --- Plot 2: Leverage ---
    if 'lev_clean' in merged_df.columns and merged_df['lev_clean'].notna().any():
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x=merged_df['sentiment_value'], y=merged_df['lev_clean'], alpha=0.5, s=100,
                        hue=merged_df['sentiment_value'], palette='viridis', edgecolor='w')
        
        plt.title('Leverage Usage vs. Fear & Greed Index', fontsize=18, fontweight='bold', pad=20)
        plt.xlabel('Fear & Greed Index', fontsize=14, fontweight='bold', labelpad=15)
        plt.ylabel('Leverage (x)', fontsize=14, fontweight='bold', labelpad=10)
        
        sns.despine()
        plt.legend([],[], frameon=False)
        plt.tight_layout()
        plt.savefig('images/leverage_vs_sentiment.png', dpi=300)
        print("-> Saved professional images/leverage_vs_sentiment.png")
    else:
        print("-> Leverage column missing. Skipping leverage plot.")

    # --- Plot 3: Win Rate ---
    if 'pnl_clean' in merged_df.columns and 'sentiment_bucket' in merged_df.columns:
        merged_df['is_win'] = merged_df['pnl_clean'] > 0
        win_rate = merged_df.groupby('sentiment_bucket')['is_win'].mean()
        order = ['Extreme Fear', 'Fear', 'Greed', 'Extreme Greed']
        win_rate = win_rate.reindex([x for x in order if x in win_rate.index])

        plt.figure(figsize=(12, 8))
        ax = sns.barplot(x=win_rate.index, y=win_rate.values, color='#008080') # Teal
        
        plt.title('Win Rate by Market Sentiment', fontsize=18, fontweight='bold', pad=20)
        plt.ylabel('Win Rate (%)', fontsize=14, fontweight='bold', labelpad=10)
        plt.xlabel('Market Sentiment', fontsize=14, fontweight='bold', labelpad=20)
        ax.tick_params(axis='x', pad=10)
        
        plt.ylim(0, 1.1)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        
        sns.despine(left=True)
        add_bar_labels(ax, fmt='{:.1%}')
        
        plt.tight_layout()
        plt.savefig('images/win_rate_by_sentiment.png', dpi=300)
        print("-> Saved professional images/win_rate_by_sentiment.png")

    print("\nSUCCESS: Analysis Finished.")

if __name__ == "__main__":
    t_df, s_df = load_and_clean_data()
    if t_df is not None and s_df is not None:
        analyze_and_visualize(t_df, s_df)