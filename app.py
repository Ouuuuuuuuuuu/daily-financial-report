#!/usr/bin/env python3
"""
Streamlit前端应用
展示每日研报和历史数据
"""

import os
import sys
import yaml
import glob
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 添加src到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.data_fetcher import data_fetcher
from src.technical_analysis import technical_analyzer
from src.report_generator import ReportGenerator

# 页面配置
st.set_page_config(
    page_title="每日研报系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 加载配置
@st.cache_resource
def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .positive { color: #e74c3c; }
    .negative { color: #27ae60; }
    .report-container {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 2rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def render_header():
    """渲染页面头部"""
    st.markdown('<div class="main-header">📊 每日市场研报系统</div>', unsafe_allow_html=True)
    st.markdown(f"**当前时间:** {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    st.markdown("---")

def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.header("⚙️ 功能菜单")
        
        page = st.radio(
            "选择页面",
            ["🏠 首页", "📈 实时行情", "📰 研报查看", "🤖 生成研报", "⚙️ 系统设置"]
        )
        
        st.markdown("---")
        st.markdown("### 📊 快捷功能")
        
        if st.button("🔄 刷新数据"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📅 历史研报")
        
        # 列出历史研报
        report_dir = config.get('report', {}).get('output_dir', './reports')
        if os.path.exists(report_dir):
            reports = sorted(glob.glob(os.path.join(report_dir, "*.md")), reverse=True)
            for report in reports[:5]:
                report_name = os.path.basename(report).replace("daily_report_", "").replace(".md", "")
                st.markdown(f"- {report_name}")
        
        return page

def render_home():
    """渲染首页"""
    st.markdown('<div class="sub-header">🎯 市场概览</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🇨🇳 A股市场")
        try:
            a_share = data_fetcher.get_a_share_index()
            if not a_share.empty:
                for _, row in a_share.head(3).iterrows():
                    change_color = "positive" if row['change_pct'] >= 0 else "negative"
                    st.markdown(f"""
                    **{row['name']}**  
                    {row['price']:.2f} 
                    <span class="{change_color}">{row['change_pct']:+.2f}%</span>
                    """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"获取A股数据失败: {e}")
    
    with col2:
        st.markdown("#### 🇺🇸 美股市场")
        try:
            nasdaq = data_fetcher.get_nasdaq_overview()
            if nasdaq:
                nq = nasdaq.get('nasdaq_index', {})
                change = nq.get('change_pct', 0)
                change_color = "positive" if change >= 0 else "negative"
                st.markdown(f"""
                **纳斯达克指数**  
                {nq.get('current', 'N/A'):.2f}
                <span class="{change_color}">{change:+.2f}%</span>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"获取美股数据失败: {e}")
    
    with col3:
        st.markdown("#### 🪙 黄金市场")
        try:
            gold = data_fetcher.get_gold_price()
            if gold:
                gc = gold.get('comex_gold', {})
                change = gc.get('change_pct', 0)
                change_color = "positive" if change >= 0 else "negative"
                st.markdown(f"""
                **COMEX黄金**  
                ${gc.get('current', 'N/A'):.2f}/oz
                <span class="{change_color}">{change:+.2f}%</span>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"获取黄金数据失败: {e}")
    
    st.markdown("---")
    st.markdown('<div class="sub-header">📊 市场热力图</div>', unsafe_allow_html=True)
    
    try:
        sector_flow = data_fetcher.get_sector_flow()
        if not sector_flow.empty:
            fig = px.bar(
                sector_flow.head(10),
                x='名称',
                y='今日涨跌幅',
                color='今日涨跌幅',
                color_continuous_scale='RdYlGn_r',
                title='板块涨跌幅排行'
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"无法加载板块数据: {e}")

def render_realtime():
    """渲染实时行情页面"""
    st.markdown('<div class="sub-header">📈 实时行情监控</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["A股指数", "美股", "AI板块", "红利板块"])
    
    with tab1:
        st.markdown("### 上证指数走势")
        try:
            df = data_fetcher.get_a_share_daily("000001", days=60)
            if not df.empty:
                df = technical_analyzer.calculate_all_indicators(df)
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df['date'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name='K线'
                ))
                fig.add_trace(go.Scatter(x=df['date'], y=df['MA5'], name='MA5', line=dict(color='orange')))
                fig.add_trace(go.Scatter(x=df['date'], y=df['MA20'], name='MA20', line=dict(color='blue')))
                fig.update_layout(title="上证指数 K线图", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                
                # 技术指标
                signals = technical_analyzer.get_latest_signals(df)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("RSI", f"{signals.get('RSI_VALUE', 'N/A')}", signals.get('RSI', 'N/A'))
                with col2:
                    st.metric("MACD", f"{signals.get('MACD_VALUE', 'N/A')}", signals.get('MACD', 'N/A'))
                with col3:
                    st.metric("KDJ-J", f"{signals.get('KDJ_J', 'N/A')}", signals.get('KDJ', 'N/A'))
                with col4:
                    st.metric("均线排列", signals.get('MA_TREND', 'N/A'))
        except Exception as e:
            st.error(f"加载图表失败: {e}")
    
    with tab2:
        st.markdown("### 纳斯达克指数")
        try:
            nasdaq_data = data_fetcher.get_nasdaq_data(["^IXIC"], period="1mo")
            if "^IXIC" in nasdaq_data:
                df = nasdaq_data["^IXIC"]
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['Close'],
                    mode='lines',
                    name='纳斯达克指数',
                    line=dict(color='purple')
                ))
                fig.update_layout(title="纳斯达克指数走势", xaxis_title="日期", yaxis_title="点位")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"加载美股数据失败: {e}")
    
    with tab3:
        st.markdown("### AI板块热点")
        try:
            ai_leaders = data_fetcher.get_ai_leaders()
            if not ai_leaders.empty:
                st.dataframe(ai_leaders, use_container_width=True)
        except Exception as e:
            st.error(f"加载AI板块失败: {e}")
    
    with tab4:
        st.markdown("### 红利ETF表现")
        try:
            dividend_etfs = data_fetcher.get_dividend_etfs()
            for name, df in dividend_etfs.items():
                if not df.empty:
                    latest = df.iloc[-1]
                    change = ((latest['close'] / df.iloc[-2]['close']) - 1) * 100 if len(df) > 1 else 0
                    st.metric(name, f"{latest['close']:.3f}", f"{change:+.2f}%")
        except Exception as e:
            st.error(f"加载红利数据失败: {e}")

def render_reports():
    """渲染研报查看页面"""
    st.markdown('<div class="sub-header">📰 研报库</div>', unsafe_allow_html=True)
    
    report_dir = config.get('report', {}).get('output_dir', './reports')
    
    if not os.path.exists(report_dir):
        st.warning("暂无研报，请先生成研报")
        return
    
    reports = sorted(glob.glob(os.path.join(report_dir, "*.md")), reverse=True)
    
    if not reports:
        st.warning("暂无研报，请先生成研报")
        return
    
    selected_report = st.selectbox(
        "选择研报日期",
        options=reports,
        format_func=lambda x: os.path.basename(x).replace("daily_report_", "").replace(".md", "")
    )
    
    if selected_report:
        with open(selected_report, 'r', encoding='utf-8') as f:
            content = f.read()
        
        st.markdown('<div class="report-container">', unsafe_allow_html=True)
        st.markdown(content)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 下载按钮
        st.download_button(
            label="📥 下载研报",
            data=content,
            file_name=os.path.basename(selected_report),
            mime="text/markdown"
        )

def render_generate():
    """渲染生成研报页面"""
    st.markdown('<div class="sub-header">🤖 生成新研报</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 生成设置")
        api_key = st.text_input("API密钥", value=os.getenv('OPENAI_API_KEY', ''), type="password")
        model = st.selectbox("模型", ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "deepseek-chat"])
        
    with col2:
        st.markdown("### 数据选项")
        include_a_share = st.checkbox("包含A股分析", value=True)
        include_nasdaq = st.checkbox("包含纳斯达克分析", value=True)
        include_gold = st.checkbox("包含黄金分析", value=True)
        include_ai = st.checkbox("包含AI板块分析", value=True)
        include_dividend = st.checkbox("包含红利板块分析", value=True)
    
    if st.button("🚀 开始生成研报", type="primary"):
        with st.spinner("正在获取数据和生成研报..."):
            try:
                # 设置环境变量
                if api_key:
                    os.environ['OPENAI_API_KEY'] = api_key
                
                # 生成研报
                generator = ReportGenerator()
                
                # 显示进度
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("正在获取市场数据...")
                progress_bar.progress(25)
                
                data = generator.fetch_all_data()
                
                status_text.text("正在分析技术指标...")
                progress_bar.progress(50)
                
                status_text.text("正在生成研报内容...")
                progress_bar.progress(75)
                
                report = generator.generate_report(data)
                
                status_text.text("正在保存研报...")
                progress_bar.progress(90)
                
                filepath = generator.save_report(report)
                
                progress_bar.progress(100)
                status_text.text("完成！")
                
                st.success(f"✅ 研报生成成功！已保存至: {filepath}")
                
                # 显示生成的研报
                with st.expander("查看生成的研报", expanded=True):
                    st.markdown(report)
                    
            except Exception as e:
                st.error(f"生成研报失败: {e}")
                st.exception(e)

def render_settings():
    """渲染设置页面"""
    st.markdown('<div class="sub-header">⚙️ 系统设置</div>', unsafe_allow_html=True)
    
    st.markdown("### API配置")
    st.markdown("""
    请在 `config.yaml` 文件中配置以下API密钥：
    
    1. **OpenAI API Key** - 用于生成研报内容
    2. **Tushare Token** - 可选，用于高级A股数据（需要注册）
    """)
    
    st.markdown("### 数据配置")
    st.json(config.get('data_sources', {}))
    
    st.markdown("### 定时任务")
    st.code("""
# 编辑crontab
crontab -e

# 添加每日12:00运行（仅工作日）
0 12 * * 1-5 cd /path/to/financial-report-system && python cron_job.py >> logs/cron.log 2>&1
""", language="bash")

# 主程序
def main():
    render_header()
    page = render_sidebar()
    
    if "首页" in page:
        render_home()
    elif "实时行情" in page:
        render_realtime()
    elif "研报查看" in page:
        render_reports()
    elif "生成研报" in page:
        render_generate()
    elif "系统设置" in page:
        render_settings()

if __name__ == "__main__":
    main()
