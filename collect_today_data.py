#!/usr/bin/env python3
"""
今日数据收集脚本 - 2026-02-05
使用可用的新浪财经接口获取真实数据
"""

import akshare as ak
import requests
import json
from datetime import datetime
import os

# 创建数据目录
data_dir = "reports/2026-02-05"
os.makedirs(data_dir, exist_ok=True)

data = {
    "date": "2026-02-05",
    "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "a_share": {},
    "us_stock": {},
    "sectors": {},
    "gold": {}
}

print("="*60)
print(f"📊 数据收集 - {data['date']}")
print("="*60)

# 1. A股主要指数
print("\n1️⃣ 获取A股指数...")
try:
    df_index = ak.stock_zh_index_spot_sina()
    for idx_name in ['上证指数', '深证成指', '创业板指']:
        row = df_index[df_index['名称'] == idx_name].iloc[0]
        data['a_share'][idx_name] = {
            'price': float(row['最新价']),
            'change': float(row['涨跌额']),
            'change_pct': float(row['涨跌幅']),
            'volume': str(row['成交量']),
            'amount': str(row['成交额'])
        }
        print(f"   {idx_name}: {row['最新价']:.2f} ({row['涨跌幅']:+.2f}%)")
except Exception as e:
    print(f"   ❌ A股指数获取失败: {e}")

# 2. 美股指数
print("\n2️⃣ 获取美股指数...")
try:
    headers = {'Referer': 'https://finance.sina.com.cn'}
    us_symbols = [
        ('int_nasdaq', '纳斯达克'),
        ('int_sp500', '标普500'),
        ('int_dji', '道琼斯')
    ]
    for symbol, name in us_symbols:
        url = f"https://hq.sinajs.cn/list={symbol}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200 and 'hq_str' in r.text:
            # 解析: var hq_str_int_nasdaq="纳斯达克,22484.07,99.37,0.44";
            content = r.text.split('"')[1]
            parts = content.split(',')
            if len(parts) >= 4:
                data['us_stock'][name] = {
                    'price': float(parts[1]),
                    'change': float(parts[2]),
                    'change_pct': float(parts[3])
                }
                print(f"   {name}: {parts[1]} ({parts[3]}%)")
except Exception as e:
    print(f"   ❌ 美股指数获取失败: {e}")

# 3. 板块数据 - 尝试新浪财经的板块接口
print("\n3️⃣ 获取板块数据...")
try:
    # 行业板块资金流向
    df_sector = ak.stock_sector_fund_flow_rank_em()
    print(f"   获取到 {len(df_sector)} 个板块数据")
    
    # 领涨板块（今日涨幅前10）
    top_gainers = df_sector.nlargest(10, '今日涨跌幅')
    data['sectors']['top_gainers'] = []
    for _, row in top_gainers.iterrows():
        data['sectors']['top_gainers'].append({
            'name': row['名称'],
            'change_pct': float(row['今日涨跌幅']),
            'fund_flow': float(row['今日主力净流入-净额']) if '今日主力净流入-净额' in row else 0
        })
    
    print("   领涨板块Top5:")
    for s in data['sectors']['top_gainers'][:5]:
        print(f"     {s['name']}: {s['change_pct']:+.2f}%")
        
except Exception as e:
    print(f"   ❌ 板块数据获取失败: {e}")
    # 使用备用数据
    data['sectors']['top_gainers'] = []

# 4. 黄金价格
print("\n4️⃣ 获取黄金价格...")
try:
    # 使用新浪财经黄金T+D接口
    headers = {'Referer': 'https://finance.sina.com.cn'}
    url = "https://hq.sinajs.cn/list=hf_GC"
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code == 200:
        content = r.text
        print(f"   黄金期货数据: {content[:100]}")
        # 解析COMEX黄金数据
        data['gold']['comex'] = {'note': '数据待解析', 'raw': content[:200]}
    
    # 国内黄金
    url2 = "https://hq.sinajs.cn/list=AU0"
    r2 = requests.get(url2, headers=headers, timeout=10)
    if r2.status_code == 200:
        print(f"   国内黄金: {r2.text[:100]}")
        data['gold']['domestic'] = {'raw': r2.text[:200]}
        
except Exception as e:
    print(f"   ❌ 黄金数据获取失败: {e}")

# 保存数据
print("\n💾 保存数据...")
with open(f"{data_dir}/data_2026-02-05.json", 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n✅ 数据已保存到: {data_dir}/data_2026-02-05.json")
print("="*60)

# 打印摘要
print("\n📋 数据摘要:")
print(f"   A股指数: {len(data['a_share'])} 个")
print(f"   美股指数: {len(data['us_stock'])} 个")
print(f"   板块数据: {len(data['sectors'].get('top_gainers', []))} 个")
print(f"   黄金数据: {'已获取' if data['gold'] else '未获取'}")
