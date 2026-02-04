#!/usr/bin/env python3
"""
Streamlit 前端应用 - 每日研报系统
修复了 Python 3.13 下的导入路径兼容性问题
"""

import os
import sys
import yaml
import glob
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- 路径兼容性修复 ---
# 确保项目根目录和 src 目录都在 sys.path 中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入自定义模块
try:
    from src.data_fetcher import data_fetcher
    from src.technical_analysis import technical_analyzer
    from src.report_generator import ReportGenerator
except ModuleNotFoundError:
    # 备选导入方案：针对某些部署环境的路径差异
    from data_fetcher import data_fetcher
    from technical_analysis import technical_analyzer
    from report_generator import ReportGenerator

# --- 页面配置 ---
st.set_page_config(
    page_title="每日研报系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 加载配置 ---
@st.cache_resource
def load_config():
    config_path = os.path.join(current_dir, 'config.yaml')
    if not os.path.exists(config_path):
        # 如果不存在则尝试从示例创建或报错
        st.error("未找到 config.yaml 配置文件，请检查项目根目录。")
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

# --- 自定义 CSS 样式 ---
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; margin-bottom: 1rem; }
    .sub-header { font-size: 1.5rem; font-weight: 600; color: #2c3e50; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; }
    .report-container { background-color: white; border: 1px solid #ddd; border-radius: 8px; padding: 2rem; margin-top: 1rem; color: black; }
    .positive { color: #e74c3c; font-weight: bold; }
    .negative { color: #27ae60; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def render_header():
    st.markdown('<div class="main-header">📊 每日市场研报系统</div>', unsafe_allow_html=True)
    st.markdown(f"**当前时间:** {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    st.markdown("---")

def render_sidebar():
    with st.sidebar:
        st.header("⚙️ 功能菜单")
        page = st.radio("选择页面", ["🏠 首页", "📈 实时行情", "📰 研报查看", "🤖 生成研报", "⚙️ 系统设置"])
        st.markdown("---")
        if st.button("🔄 刷新系统缓存"):
            st.cache_data.clear()
            st.rerun()
        return page

def render_home():
    st.markdown('<div class="sub-header">🎯 市场概览</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🇨🇳 A股市场")
        try:
            a_share = data_fetcher.get_a_share_index()
            if not a_share.empty:
                for _, row in a_share.head(3).iterrows():
                    color = "positive" if row['change_pct'] >= 0 else "negative"
                    st.markdown(f"{row['name']}: **{row['price']:.2f}** <span class='{color}'>{row['change_pct']:+.2f}%</span>", unsafe_allow_html=True)
        except Exception as e: st.error(f"A股数据获取失败")
    
    with col2:
        st.markdown("#### 🇺🇸 美股市场")
        try:
            nasdaq = data_fetcher.get_nasdaq_overview()
            if nasdaq:
                nq = nasdaq.get('nasdaq_index', {})
                color = "positive" if nq.get('change_pct', 0) >= 0 else "negative"
                st.markdown(f"纳斯达克: **{nq.get('current', 0):.2f}** <span class='{color}'>{nq.get('change_pct', 0):+.2f}%</span>", unsafe_allow_html=True)
        except Exception as e: st.error(f"美股数据获取失败")

    with col3:
        st.markdown("#### 🪙 黄金市场")
        try:
            gold = data_fetcher.get_gold_price()
            if gold:
                gc = gold.get('comex_gold', {})
                color = "positive" if gc.get('change_pct', 0) >= 0 else "negative"
                st.markdown(f"COMEX黄金: **${gc.get('current', 0):.2f}** <span class='{color}'>{gc.get('change_pct', 0):+.2f}%</span>", unsafe_allow_html=True)
        except Exception as e: st.error(f"黄金数据获取失败")

def render_realtime():
    st.markdown('<div class="sub-header">📈 实时行情监控</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["上证指数", "板块热点"])
    with tab1:
        try:
            df = data_fetcher.get_a_share_daily("000001", days=60)
            if not df.empty:
                df = technical_analyzer.calculate_all_indicators(df)
                fig = go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
                fig.update_layout(xaxis_rangeslider_visible=False, title="上证指数走势")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e: st.error(f"图表加载失败: {e}")

def render_reports():
    st.markdown('<div class="sub-header">📰 研报库</div>', unsafe_allow_html=True)
    report_dir = config.get('report', {}).get('output_dir', './reports')
    if not os.path.exists(report_dir):
        st.info("尚未生成任何研报。")
        return
    reports = sorted(glob.glob(os.path.join(report_dir, "*.md")), reverse=True)
    if reports:
        selected = st.selectbox("选择历史研报", reports, format_func=lambda x: os.path.basename(x))
        with open(selected, 'r', encoding='utf-8') as f:
            st.markdown(f'<div class="report-container">{f.read()}</div>', unsafe_allow_html=True)
    else:
        st.warning("文件夹内暂无 Markdown 研报。")

def render_generate():
    st.markdown('<div class="sub-header">🤖 智能研报生成器</div>', unsafe_allow_html=True)
    if st.button("🚀 立即获取数据并生成今日研报", type="primary"):
        with st.spinner("LLM 正在分析市场数据..."):
            try:
                generator = ReportGenerator()
                data = generator.fetch_all_data()
                report = generator.generate_report(data)
                path = generator.save_report(report)
                st.success(f"研报已生成并保存！")
                st.markdown(report)
            except Exception as e:
                st.error(f"生成失败: {e}")

def main():
    render_header()
    page = render_sidebar()
    if "首页" in page: render_home()
    elif "实时行情" in page: render_realtime()
    elif "研报查看" in page: render_reports()
    elif "生成研报" in page: render_generate()
    else: st.info("系统设置模块暂未开放前端修改，请直接编辑 config.yaml")

if __name__ == "__main__":
    main()
