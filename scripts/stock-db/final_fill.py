#!/usr/bin/env python3
"""快速补完剩余股票数据"""
import baostock as bs
import pandas as pd
from datetime import datetime
from pathlib import Path
import json
import time

print("=" * 60)
print("🚀 最终补完模式")
print("=" * 60)

# 登录
lg = bs.login()
print(f"[{datetime.now().strftime('%H:%M:%S')}] 登录: {lg.error_msg}")

# 获取数据
stock_basic = Path('~/StockData/parquet/stock_basic.parquet').expanduser()
daily_path = Path('~/StockData/parquet/daily').expanduser()

df_basic = pd.read_parquet(stock_basic)

# 已有数据
existing_codes = set()
for f in daily_path.rglob("*.parquet"):
    try:
        df = pd.read_parquet(f)
        if 'ts_code' in df.columns:
            existing_codes.update(df['ts_code'].unique())
    except:
        pass

df_basic['ts_code'] = df_basic['symbol'].apply(lambda x: x + '.SH' if x.startswith('6') else x + '.SZ')
missing_df = df_basic[~df_basic['ts_code'].isin(existing_codes)]
missing_codes = missing_df['ts_code'].tolist()

total = len(missing_codes)
print(f"需补: {total} 只股票")

success = 0
fail = 0
batch_data = []
start_time = time.time()
last_save = time.time()

for i, ts_code in enumerate(missing_codes):
    if ts_code.endswith('.SH'):
        bs_code = 'sh.' + ts_code.replace('.SH', '')
    else:
        bs_code = 'sz.' + ts_code.replace('.SZ', '')
    
    try:
        rs = bs.query_history_k_data_plus(bs_code,
            "date,code,open,high,low,close,preclose,volume,amount,turn,pctChg",
            start_date='2020-01-01', end_date='2025-02-25', frequency="d", adjustflag="3")
        
        data = []
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            data.append({
                'trade_date': pd.to_datetime(row[0]),
                'ts_code': ts_code,
                'open': float(row[2]),
                'high': float(row[3]),
                'low': float(row[4]),
                'close': float(row[5]),
                'pre_close': float(row[6]),
                'vol': float(row[7]),
                'amount': float(row[8]),
                'turnover_rate': float(row[9]) if row[9] else None,
                'pct_chg': float(row[10]) if row[10] else None,
                'data_source': 'baostock',
                'year': pd.to_datetime(row[0]).year,
                'month': pd.to_datetime(row[0]).month
            })
        
        if data:
            batch_data.extend(data)
            success += 1
        else:
            fail += 1
    except Exception as e:
        fail += 1
    
    # 每100只显示进度
    if (i + 1) % 100 == 0 or i == total - 1:
        elapsed = time.time() - start_time
        speed = (i + 1) / elapsed * 60
        print(f"[{i+1}/{total}] 成功:{success} 失败:{fail} 速度:{speed:.1f}只/分钟")
    
    # 每30秒保存一次
    if time.time() - last_save > 30 and batch_data:
        df_batch = pd.DataFrame(batch_data)
        for (year, month), group in df_batch.groupby(['year', 'month']):
            partition_path = daily_path / f"year={year}" / f"month={month:02d}"
            partition_path.mkdir(parents=True, exist_ok=True)
            parquet_file = partition_path / "data.parquet"
            
            if parquet_file.exists():
                existing = pd.read_parquet(parquet_file)
                combined = pd.concat([existing, group], ignore_index=True)
                combined = combined.drop_duplicates(subset=['ts_code', 'trade_date'])
                combined.to_parquet(parquet_file, index=False, compression='zstd')
            else:
                group.to_parquet(parquet_file, index=False, compression='zstd')
        
        print(f"  💾 已保存 {len(df_batch)} 条记录")
        batch_data = []
        last_save = time.time()

# 最终保存
if batch_data:
    df_batch = pd.DataFrame(batch_data)
    for (year, month), group in df_batch.groupby(['year', 'month']):
        partition_path = daily_path / f"year={year}" / f"month={month:02d}"
        partition_path.mkdir(parents=True, exist_ok=True)
        parquet_file = partition_path / "data.parquet"
        
        if parquet_file.exists():
            existing = pd.read_parquet(parquet_file)
            combined = pd.concat([existing, group], ignore_index=True)
            combined = combined.drop_duplicates(subset=['ts_code', 'trade_date'])
            combined.to_parquet(parquet_file, index=False, compression='zstd')
        else:
            group.to_parquet(parquet_file, index=False, compression='zstd')

bs.logout()

# 更新进度
progress_file = Path('~/StockData/meta/init_progress.json').expanduser()
with open(progress_file) as f:
    progress = json.load(f)
progress['daily']['completed'] = True
progress['daily']['count'] = len(existing_codes) + success
with open(progress_file, 'w') as f:
    json.dump(progress, f, indent=2, default=str)

print("=" * 60)
print(f"✅ 完成！成功:{success} 失败:{fail}")
print(f"总覆盖率: {(len(existing_codes) + success) / len(df_basic) * 100:.1f}%")
print("=" * 60)
