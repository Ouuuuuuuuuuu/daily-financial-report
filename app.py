import os
import sys
import yaml
import glob
import json
from datetime import datetime
import streamlit as st

# --- 强制路径修复 ---
# 将根目录和 src 目录同时加入搜索路径，防止不同部署环境下的路径迷失
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# --- 安全导入自定义模块 ---
try:
    from src.data_fetcher import data_fetcher
    from src.technical_analysis import technical_analyzer
    from src.report_generator import ReportGenerator
except (ImportError, ModuleNotFoundError):
    # 备选：如果已经在 src 路径下运行
    from data_fetcher import data_fetcher
    from technical_analysis import technical_analyzer
    from report_generator import ReportGenerator

# --- 页面设置 ---
st.set_page_config(page_title="每日研报系统", page_icon="📊", layout="wide")

# 加载配置
@st.cache_resource
def load_config():
    p = os.path.join(current_dir, 'config.yaml')
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

config = load_config()


def get_available_reports():
    """获取所有可用的研报（按日期目录组织）"""
    report_dir = './reports'
    reports = []
    if os.path.exists(report_dir):
        # 遍历 reports 下的所有日期目录
        for date_folder in sorted(os.listdir(report_dir), reverse=True):
            folder_path = os.path.join(report_dir, date_folder)
            if os.path.isdir(folder_path):
                # 检查目录下是否有 report.md 或 report.json
                report_md = os.path.join(folder_path, 'report.md')
                report_json = os.path.join(folder_path, 'data.json')
                report_json2 = os.path.join(folder_path, f'data_{date_folder}.json')
                
                if os.path.exists(report_md):
                    reports.append({
                        'date': date_folder,
                        'path': report_md,
                        'type': 'markdown'
                    })
    return reports


def display_report_card(date, data_summary):
    """显示研报卡片"""
    with st.container():
        st.markdown(f"""
        <div style="padding: 1rem; border-radius: 0.5rem; border: 1px solid #e0e0e0; margin-bottom: 1rem;">
            <h4 style="margin: 0;">📅 {date}</h4>
            <p style="margin: 0.5rem 0; color: #666;">{data_summary}</p>
        </div>
        """, unsafe_allow_html=True)


def main():
    st.title("📊 每日金融研报自动化系统")
    st.markdown(f"**当前北京时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    menu = ["🏠 首页概览", "📅 历史研报查看"]
    choice = st.sidebar.selectbox("功能菜单", menu)

    if choice == "🏠 首页概览":
        st.subheader("🎯 最新研报")
        
        reports = get_available_reports()
        if reports:
            latest = reports[0]
            col1, col2 = st.columns([2, 1])
            with col1:
                st.success(f"✅ 最新研报日期: **{latest['date']}**")
            with col2:
                if st.button("查看最新研报"):
                    st.session_state['selected_date'] = latest['date']
                    st.rerun()
            
            # 显示最新研报预览
            with open(latest['path'], 'r', encoding='utf-8') as f:
                content = f.read()
                # 只显示核心观点部分
                if '## 核心观点' in content:
                    core_view = content.split('## ')[1].split('## ')[0] if '## ' in content[content.find('## 核心观点'):] else ""
                    st.markdown("---")
                    st.markdown("#### 📌 核心观点")
                    st.markdown(content[:content.find('## A股大盘分析')])
            
            st.markdown("---")
            st.subheader("📊 最近研报列表")
            cols = st.columns(3)
            for i, report in enumerate(reports[:6]):
                with cols[i % 3]:
                    st.info(f"📅 {report['date']}")
                    if st.button(f"查看 {report['date']}", key=f"btn_{report['date']}"):
                        st.session_state['selected_date'] = report['date']
                        st.rerun()
        else:
            st.warning("暂无历史研报。")
            
        # 市场状态
        st.markdown("---")
        st.subheader("🌍 市场状态")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("上证指数", "4083.03", "-0.47%", delta_color="inverse")
        with col2:
            st.metric("深证成指", "13988.29", "-1.19%", delta_color="inverse")
        with col3:
            st.metric("创业板指", "3271.78", "-1.20%", delta_color="inverse")

    elif choice == "📅 历史研报查看":
        st.subheader("📚 历史研报库")
        
        reports = get_available_reports()
        if not reports:
            st.warning("暂无历史研报文件。")
            return
        
        # 选择日期
        report_dates = [r['date'] for r in reports]
        
        # 如果有 session state 中选中的日期，使用它
        default_index = 0
        if 'selected_date' in st.session_state and st.session_state['selected_date'] in report_dates:
            default_index = report_dates.index(st.session_state['selected_date'])
        
        selected_date = st.selectbox("选择日期", report_dates, index=default_index)
        
        # 找到选中的研报
        selected_report = next((r for r in reports if r['date'] == selected_date), None)
        
        if selected_report:
            # 读取并显示研报内容
            with open(selected_report['path'], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 显示数据更新时间（如果有数据文件）
            data_json_path = os.path.join('./reports', selected_date, f'data_{selected_date}.json')
            data_json_path_alt = os.path.join('./reports', selected_date, 'data.json')
            
            if os.path.exists(data_json_path):
                with open(data_json_path, 'r', encoding='utf-8') as f:
                    data_info = json.load(f)
                    if 'update_time' in data_info:
                        st.caption(f"📊 数据更新时间: {data_info['update_time']}")
            elif os.path.exists(data_json_path_alt):
                with open(data_json_path_alt, 'r', encoding='utf-8') as f:
                    data_info = json.load(f)
                    if 'update_time' in data_info:
                        st.caption(f"📊 数据更新时间: {data_info['update_time']}")
            
            st.markdown("---")
            st.markdown(content)
            
            # 提供下载按钮
            st.download_button(
                label="📥 下载 Markdown 研报",
                data=content,
                file_name=f"daily_report_{selected_date}.md",
                mime="text/markdown"
            )

if __name__ == "__main__":
    main()
