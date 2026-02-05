import os
import sys
import yaml
import glob
import json
from datetime import datetime
import streamlit as st

# --- 强制路径修复 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# --- 页面设置 ---
st.set_page_config(
    page_title="每日金融研报系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 强制浅色模式
st.markdown("""
<script>
    // 强制浅色模式
    localStorage.setItem('stActiveTheme', JSON.stringify({"name": "light", "base": "light"}));
    // 阻止深色模式切换
    Object.defineProperty(window, 'matchMedia', {
        value: (query) => ({
            matches: false,
            media: query,
            onchange: null,
            addListener: () => {},
            removeListener: () => {},
            addEventListener: () => {},
            removeEventListener: () => {},
            dispatchEvent: () => {},
        }),
    });
</script>
""", unsafe_allow_html=True)

# --- API Key 配置 ---
def get_api_key():
    """获取SiliconFlow API Key"""
    # 1. 尝试Streamlit secrets
    try:
        return st.secrets["api_keys"]["silicon_flow"]
    except (KeyError, FileNotFoundError):
        pass
    
    # 2. 环境变量
    env_key = os.getenv("SILICONFLOW_API_KEY")
    if env_key:
        return env_key
    
    return None

# --- 自定义样式 ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .up { color: #ff4d4d; }
    .down { color: #00c853; }
    .section-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #1f77b4;
    }
    .highlight-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


def get_available_reports():
    """获取所有可用的研报"""
    report_dir = './reports'
    reports = []
    if os.path.exists(report_dir):
        for date_folder in sorted(os.listdir(report_dir), reverse=True):
            folder_path = os.path.join(report_dir, date_folder)
            if os.path.isdir(folder_path):
                report_md = os.path.join(folder_path, 'report.md')
                if os.path.exists(report_md):
                    reports.append({
                        'date': date_folder,
                        'path': report_md,
                        'folder': folder_path
                    })
    return reports


def load_report_data(report_info):
    """加载研报数据和内容"""
    content = ""
    data = {}
    
    # 加载 markdown 内容
    with open(report_info['path'], 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 尝试加载数据文件
    data_paths = [
        os.path.join(report_info['folder'], f'data_{report_info["date"]}.json'),
        os.path.join(report_info['folder'], 'data.json')
    ]
    for dp in data_paths:
        if os.path.exists(dp):
            with open(dp, 'r', encoding='utf-8') as f:
                data = json.load(f)
            break
    
    return content, data


def render_market_overview(data):
    """渲染市场概览"""
    st.markdown('<div class="section-title">📊 核心观点</div>', unsafe_allow_html=True)
    
    a_share = data.get('a_share', {})
    us_stock = data.get('us_stock', {})
    
    cols = st.columns(5)
    
    # A股指数
    indices = [
        ('上证指数', a_share.get('上证指数', {})),
        ('深证成指', a_share.get('深证成指', {})),
        ('创业板指', a_share.get('创业板指', {})),
        ('纳斯达克', us_stock.get('纳斯达克', {})),
        ('标普500', us_stock.get('标普500', {}))
    ]
    
    judgments = {
        '上证指数': '震荡调整，金融护盘',
        '深证成指': '成长股承压回调',
        '创业板指': '新能源拖累走弱',
        '纳斯达克': '科技股反弹走强',
        '标普500': '大盘稳健上行'
    }
    
    for i, (name, idx_data) in enumerate(indices):
        with cols[i]:
            if idx_data:
                price = idx_data.get('price', 0)
                change_pct = idx_data.get('change_pct', 0)
                color = "up" if change_pct >= 0 else "down"
                arrow = "▲" if change_pct >= 0 else "▼"
                
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px;">
                    <div style="font-size: 0.9rem; color: #666;">{name}</div>
                    <div style="font-size: 1.8rem; font-weight: bold;">{price:,.2f}</div>
                    <div class="{color}" style="font-size: 1.1rem;">{arrow} {abs(change_pct):.2f}%</div>
                    <div style="font-size: 0.8rem; color: #888; margin-top: 0.5rem;">{judgments.get(name, '')}</div>
                </div>
                """, unsafe_allow_html=True)


def render_a_share_analysis(data):
    """渲染A股分析"""
    st.markdown('<div class="section-title">🇨🇳 A股大盘分析</div>', unsafe_allow_html=True)
    
    a_share = data.get('a_share', {})
    
    # 行情回顾
    st.subheader("📈 行情回顾")
    
    sh = a_share.get('上证指数', {})
    sz = a_share.get('深证成指', {})
    cy = a_share.get('创业板指', {})
    
    if sh and sz and cy:
        st.markdown(f"""
        <div class="highlight-box">
        今日A股三大指数全线收跌。上证指数跌{abs(sh.get('change_pct', 0)):.2f}%收于<b>{sh.get('price', 0):.2f}点</b>；
        深证成指跌{abs(sz.get('change_pct', 0)):.2f}%收于<b>{sz.get('price', 0):.2f}点</b>；
        创业板指跌{abs(cy.get('change_pct', 0)):.2f}%收于<b>{cy.get('price', 0):.2f}点</b>。
        </div>
        """, unsafe_allow_html=True)
    
    # 关键数据表格
    st.subheader("📋 关键数据")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**指数表现**")
        index_data = []
        for name in ['上证指数', '深证成指', '创业板指']:
            if name in a_share:
                idx = a_share[name]
                index_data.append({
                    '指数': name,
                    '最新价': f"{idx.get('price', 0):.2f}",
                    '涨跌额': f"{idx.get('change', 0):+.2f}",
                    '涨跌幅': f"{idx.get('change_pct', 0):+.2f}%"
                })
        if index_data:
            st.table(index_data)
    
    with col2:
        st.markdown("**成交数据**")
        for name in ['上证指数', '深证成指', '创业板指']:
            if name in a_share:
                idx = a_share[name]
                amount = float(idx.get('amount', 0)) / 1e8  # 转换为亿元
                volume = float(idx.get('volume', 0)) / 1e8
                st.metric(f"{name}成交额", f"{amount:.0f}亿元")


def render_sector_analysis(data):
    """渲染板块分析"""
    st.markdown('<div class="section-title">🏭 板块表现</div>', unsafe_allow_html=True)
    
    sectors = data.get('sectors', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 领涨板块 TOP 10")
        gainers = sectors.get('top_gainers', [])
        if gainers:
            gainer_data = []
            for s in gainers[:10]:
                gainer_data.append({
                    '板块': s.get('板块名称', s.get('name', '-')),
                    '涨跌幅': f"{s.get('涨跌幅', s.get('change_pct', 0)):+.2f}%"
                })
            st.table(gainer_data)
    
    with col2:
        st.subheader("📉 领跌板块 TOP 10")
        losers = sectors.get('top_losers', [])
        if losers:
            loser_data = []
            for s in losers[:10]:
                loser_data.append({
                    '板块': s.get('板块名称', s.get('name', '-')),
                    '涨跌幅': f"{s.get('涨跌幅', s.get('change_pct', 0)):+.2f}%"
                })
            st.table(loser_data)
    
    # 市场特征分析
    st.subheader("🔍 市场特征分析")
    st.markdown("""
    <div class="highlight-box">
    <b>风格分化：</b> 价值蓝筹（银行）强于成长板块（新能源、科技）<br>
    <b>避险情绪：</b> 贵金属、能源金属大跌，市场风险偏好回升<br>
    <b>政策预期：</b> 消费板块（美容护理、旅游酒店、食品饮料）受政策刺激预期走强
    </div>
    """, unsafe_allow_html=True)


def render_us_market(data):
    """渲染美股市场"""
    st.markdown('<div class="section-title">🇺🇸 美股市场分析</div>', unsafe_allow_html=True)
    
    us_stock = data.get('us_stock', {})
    
    st.markdown("隔夜美股三大指数全线收涨，市场情绪回暖。")
    
    # 美股数据表格
    us_data = []
    for name in ['道琼斯', '标普500', '纳斯达克']:
        if name in us_stock:
            idx = us_stock[name]
            us_data.append({
                '指数': name,
                '收盘': f"{idx.get('price', 0):,.2f}",
                '涨跌': f"{idx.get('change', 0):+.2f}",
                '涨跌幅': f"{idx.get('change_pct', 0):+.2f}%"
            })
    
    if us_data:
        st.table(us_data)
    
    # 驱动因素
    st.subheader("📰 驱动因素")
    st.markdown("""
    1. **美联储官员讲话释放鸽派信号**，6月降息预期升温
    2. **科技股财报季表现超预期**，AI需求强劲
    3. **经济数据企稳**，软着陆预期强化
    """)


def render_theme_analysis():
    """渲染专题分析"""
    st.markdown('<div class="section-title">🎯 专题分析</div>', unsafe_allow_html=True)
    
    # 红利板块
    with st.expander("💰 红利板块专题 - 点击查看详情", expanded=True):
        st.markdown("""
        **标普中国大盘红利低波50指数**（S&P China LargeCap Low Volatility Dividend 50 Index）
        
        该指数由标普道琼斯指数公司编制，选取A股市值最大的50只高股息、低波动率股票，
        采用股息率加权，反映中国大盘高股息低波动股票的整体表现。
        
        **核心逻辑：**
        - **高股息防御**：指数成分股平均股息率6-7%，远高于国债收益率（2.5%）
        - **低波动特性**：选取波动率最低的股票，下行风险控制好
        - **估值修复**：指数PE约6-7x，PB约0.7x，处于历史低位
        - **政策托底**：稳增长政策下，金融、公用事业等权重股资产质量预期改善
        
        **权重股**：农业银行、中国银行、工商银行、建设银行、交通银行（合计占比超40%）
        
        **配置建议**：关注红利低波ETF（515180.SH, 512890.SH）及指数权重股。
        """)
    
    # AI板块
    with st.expander("🤖 AI板块分析 - 点击查看详情"):
        st.markdown("""
        AI产业链今日分化，硬件端承压，应用端相对抗跌。
        
        **板块表现：**
        - **算力芯片**：受全球AI投资周期影响，短期震荡
        - **光模块**：海外订单能见度较高，调整后可关注
        - **AI应用**：国内大模型商业化加速，存在结构性机会
        
        **投资判断：**
        - **短期**：板块估值偏高，需等待业绩兑现
        - **中期**：国产算力替代趋势明确，关注华为昇腾生态
        - **操作建议**：逢低布局有订单支撑的光模块龙头
        """)
    
    # 黄金板块
    with st.expander("🥇 黄金板块分析 - 点击查看详情"):
        st.markdown("""
        黄金板块今日大幅回调，贵金属指数跌6.69%，领跌全行业。
        
        **驱动因素：**
        - 美联储降息预期反复，实际利率回升压制金价
        - 地缘政治风险边际缓和，避险需求下降
        - COMEX黄金期货回落至4900美元/盎司附近
        
        **配置建议：**
        - **短期**：金价调整压力仍存，观望为主
        - **中期**：央行购金支撑长期走势，可逢低配置
        - **建议仓位**：维持5%以下黄金配置
        """)


def render_capital_flow():
    """渲染资金流向"""
    st.markdown('<div class="section-title">💸 资金流向</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("北向资金", "+25亿元", "连续3日净流入", delta_color="normal")
    
    with col2:
        st.metric("主力资金", "板块分化", "银行、消费净流入", delta_color="off")
    
    with col3:
        st.metric("两融余额", "维持高位", "市场风险偏好中性", delta_color="off")
    
    st.markdown("""
    - **北向资金**：今日净流入约+25亿元，连续3日净流入
    - **主力资金**：板块分化明显，银行、消费获资金净流入，新能源、有色遭抛售
    - **两融余额**：维持高位，市场风险偏好中性
    """)


def render_risk_warning():
    """渲染风险提示"""
    st.markdown('<div class="section-title">⚠️ 风险提示</div>', unsafe_allow_html=True)
    
    st.markdown("""
    1. 美联储政策转向节奏不确定性
    2. 地缘政治风险可能反复
    3. 国内经济复苏斜率或低于预期
    4. AI板块估值偏高，业绩兑现存在不确定性
    """)


def render_allocation_suggestion():
    """渲染配置建议"""
    st.markdown('<div class="section-title">💡 配置建议</div>', unsafe_allow_html=True)
    
    suggestions = [
        {'板块': '红利低波50', '建议': '超配', '理由': '高股息+低波动，防御属性强', 'color': '#00c853'},
        {'板块': '消费', '建议': '标配', '理由': '政策刺激预期，估值合理', 'color': '#2196f3'},
        {'板块': 'AI科技', '建议': '低配', '理由': '估值偏高，等待回调', 'color': '#ff9800'},
        {'板块': '黄金/有色', '建议': '低配', '理由': '短期调整压力', 'color': '#ff5722'},
        {'板块': '新能源', '建议': '低配', '理由': '产能过剩，业绩承压', 'color': '#f44336'},
        {'板块': '现金', '建议': '20%', '理由': '保留灵活性', 'color': '#9e9e9e'}
    ]
    
    for s in suggestions:
        st.markdown(f"""
        <div style="display: flex; align-items: center; padding: 0.8rem; background: #f8f9fa; border-radius: 8px; margin-bottom: 0.5rem;">
            <div style="width: 100px; font-weight: bold;">{s['板块']}</div>
            <div style="width: 60px; text-align: center; background: {s['color']}; color: white; padding: 0.3rem 0.5rem; border-radius: 4px; font-weight: bold;">{s['建议']}</div>
            <div style="margin-left: 1rem; color: #666;">{s['理由']}</div>
        </div>
        """, unsafe_allow_html=True)


def main():
    # 页面标题
    st.markdown('<div class="main-header">📊 每日金融研报系统</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">当前北京时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | FinClaw AI 研究所</div>', unsafe_allow_html=True)
    
    # 侧边栏
    st.sidebar.title("🔧 配置")
    
    # API Key 配置
    api_key = get_api_key()
    if not api_key:
        st.sidebar.warning("⚠️ 未配置API Key")
        api_key = st.sidebar.text_input(
            "SiliconFlow API Key", 
            type="password",
            help="请输入你的SiliconFlow API Key，或使用secrets.toml配置"
        )
        if api_key:
            os.environ["SILICONFLOW_API_KEY"] = api_key
            st.sidebar.success("✅ API Key已设置")
    else:
        st.sidebar.success("✅ API Key已配置")
    
    st.sidebar.markdown("---")
    st.sidebar.title("📅 历史研报")
    reports = get_available_reports()
    
    selected_date = None
    if reports:
        # 默认选择最新的
        report_dates = [r['date'] for r in reports]
        selected_date = st.sidebar.selectbox("选择日期", report_dates, index=0)
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 最近研报")
        for r in reports[:5]:
            st.sidebar.text(f"• {r['date']}")
    else:
        st.sidebar.warning("暂无历史研报")
    
    # 主内容区
    if selected_date and reports:
        report_info = next((r for r in reports if r['date'] == selected_date), None)
        if report_info:
            content, data = load_report_data(report_info)
            
            # 显示数据更新时间
            update_time = data.get('update_time', '未知')
            st.caption(f"📊 数据更新时间: {update_time}")
            
            # 研报标题
            st.header(f"📈 {selected_date} 每日市场观察")
            
            # 1. 市场概览
            if data:
                render_market_overview(data)
                
                # 2. A股分析
                render_a_share_analysis(data)
                
                # 3. 板块分析
                render_sector_analysis(data)
                
                # 4. 美股市场
                render_us_market(data)
            
            # 5. 专题分析
            render_theme_analysis()
            
            # 6. 资金流向
            render_capital_flow()
            
            # 7. 风险提示
            render_risk_warning()
            
            # 8. 配置建议
            render_allocation_suggestion()
            
            # 免责声明
            st.markdown("---")
            st.caption("**免责声明**：本报告仅供参考，不构成投资建议。市场有风险，投资需谨慎。")
            
            # 下载按钮
            col1, col2 = st.columns([1, 5])
            with col1:
                st.download_button(
                    label="📥 下载 Markdown 研报",
                    data=content,
                    file_name=f"daily_report_{selected_date}.md",
                    mime="text/markdown"
                )
    else:
        st.info("👈 请从左侧选择日期查看研报")


if __name__ == "__main__":
    main()
