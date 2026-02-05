import os
import sys
import yaml
import glob
import json
from datetime import datetime
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

st.set_page_config(
    page_title="每日金融研报系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<script>
    localStorage.setItem('stActiveTheme', JSON.stringify({"name": "light", "base": "light"}));
    Object.defineProperty(window, 'matchMedia', {
        value: (query) => ({ matches: false, media: query, onchange: null, addListener: () => {}, removeListener: () => {}, addEventListener: () => {}, removeEventListener: () => {}, dispatchEvent: () => {} }),
    });
</script>
""", unsafe_allow_html=True)


def get_api_key():
    """获取API Key"""
    try:
        return st.secrets["api_keys"]["silicon_flow"]
    except (KeyError, FileNotFoundError):
        pass
    env_key = os.getenv("SILICONFLOW_API_KEY")
    if env_key:
        return env_key
    return None


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
    
    with open(report_info['path'], 'r', encoding='utf-8') as f:
        content = f.read()
    
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


def fetch_live_data():
    """获取实时数据"""
    from src.report_generator import ReportGenerator
    gen = ReportGenerator()
    return gen.fetch_all_data()


def stream_ai_analysis(data):
    """流式生成AI分析"""
    from src.report_generator import ReportGenerator
    gen = ReportGenerator()
    for chunk in gen.generate_ai_analysis_stream(data):
        yield chunk


def main():
    st.title("📊 每日金融研报系统")
    st.caption(f"北京时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # API Key 检查
    api_key = get_api_key()
    
    # 侧边栏
    st.sidebar.title("🔧 配置")
    if not api_key:
        st.sidebar.error("⚠️ 未配置API Key")
        api_key_input = st.sidebar.text_input("SiliconFlow API Key", type="password")
        if api_key_input:
            os.environ["SILICONFLOW_API_KEY"] = api_key_input
            st.sidebar.success("已设置")
            st.rerun()
    else:
        st.sidebar.success("✅ API Key已配置")
    
    st.sidebar.markdown("---")
    
    # 菜单
    menu = st.sidebar.radio("功能", ["📈 查看研报", "🤖 生成今日研报"])
    
    if menu == "📈 查看研报":
        reports = get_available_reports()
        
        if not reports:
            st.warning("暂无历史研报")
            return
        
        # 选择日期
        report_dates = [r['date'] for r in reports]
        selected_date = st.selectbox("选择日期", report_dates, index=0)
        
        report_info = next((r for r in reports if r['date'] == selected_date), None)
        
        if report_info:
            content, data = load_report_data(report_info)
            
            st.header(f"📅 {selected_date} 每日市场观察")
            st.caption(f"数据时间: {data.get('update_time', '-')}")
            
            # 市场数据表格
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("A股")
                a_share = data.get('a_share', {})
                for name in ['上证指数', '深证成指', '创业板指']:
                    if name in a_share:
                        idx = a_share[name]
                        change = idx.get('change_pct', 0)
                        st.metric(name, f"{idx.get('price', 0):.2f}", f"{change:+.2f}%")
            
            with col2:
                st.subheader("美股")
                us_stock = data.get('us_stock', {})
                for name in ['道琼斯', '标普500', '纳斯达克']:
                    if name in us_stock:
                        idx = us_stock[name]
                        change = idx.get('change_pct', 0)
                        st.metric(name, f"{idx.get('price', 0):,.2f}", f"{change:+.2f}%")
            
            with col3:
                st.subheader("黄金")
                gold = data.get('gold', {})
                if 'AU9999' in gold:
                    st.metric("AU9999", f"{gold['AU9999'].get('price', '-')}元/克")
                if 'XAU' in gold:
                    st.metric("XAU", f"{gold['XAU'].get('price', '-')}美元/盎司")
            
            # 板块数据
            st.subheader("行业板块")
            sectors = data.get('sectors', {})
            col1, col2 = st.columns(2)
            
            with col1:
                gainers = sectors.get('top_gainers', [])
                if gainers:
                    st.markdown("**领涨**")
                    for g in gainers[:5]:
                        st.text(f"{g.get('板块名称', '-')}: {g.get('涨跌幅', 0):+.2f}%")
            
            with col2:
                losers = sectors.get('top_losers', [])
                if losers:
                    st.markdown("**领跌**")
                    for l in losers[:5]:
                        st.text(f"{l.get('板块名称', '-')}: {l.get('涨跌幅', 0):+.2f}%")
            
            # 红利低波50成分股
            st.subheader("红利低波50指数成分股（前10）")
            dividend = data.get('dividend_index', {})
            components = dividend.get('top_components', [])
            if components:
                comp_data = []
                for c in components[:10]:
                    comp_data.append({
                        '代码': c.get('成分券代码', '-'),
                        '名称': c.get('成分券名称', '-'),
                        '权重': f"{c.get('权重', 0):.2f}%"
                    })
                st.table(comp_data)
            
            st.markdown("---")
            
            # 显示AI分析
            if "## AI分析" in content:
                ai_start = content.find("## AI分析")
                ai_end = content.find("---", ai_start)
                if ai_end == -1:
                    ai_end = len(content)
                ai_content = content[ai_start:ai_end].replace("## AI分析", "").strip()
                
                st.subheader("🤖 AI分析")
                st.markdown(ai_content)
            
            # 下载
            st.download_button(
                label="📥 下载研报",
                data=content,
                file_name=f"report_{selected_date}.md",
                mime="text/markdown"
            )
    
    elif menu == "🤖 生成今日研报":
        st.header("生成今日研报")
        
        if not api_key and not os.getenv("SILICONFLOW_API_KEY"):
            st.error("请先配置API Key")
            return
        
        if st.button("📊 获取实时数据", type="primary"):
            with st.spinner("获取数据中..."):
                try:
                    data = fetch_live_data()
                    st.session_state['today_data'] = data
                    st.success("✅ 数据获取完成")
                except Exception as e:
                    st.error(f"失败: {e}")
        
        if 'today_data' in st.session_state:
            data = st.session_state['today_data']
            
            # 显示数据摘要
            st.subheader("数据摘要")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**A股**")
                for name, idx in data.get('a_share', {}).items():
                    st.text(f"{name}: {idx.get('price', 0):.2f} ({idx.get('change_pct', 0):+.2f}%)")
            
            with col2:
                st.markdown("**美股**")
                for name, idx in data.get('us_stock', {}).items():
                    st.text(f"{name}: {idx.get('price', 0):,.2f} ({idx.get('change_pct', 0):+.2f}%)")
            
            # 流式生成AI分析
            st.markdown("---")
            
            if st.button("🤖 生成AI分析（流式输出）", type="primary"):
                st.subheader("AI分析")
                
                # 创建占位符用于流式输出
                output_placeholder = st.empty()
                full_content = ""
                
                try:
                    for chunk in stream_ai_analysis(data):
                        full_content += chunk
                        output_placeholder.markdown(full_content)
                except Exception as e:
                    st.error(f"生成失败: {e}")


if __name__ == "__main__":
    main()
