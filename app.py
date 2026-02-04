import os
import sys
import yaml
import glob
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

def main():
    st.title("📊 每日金融研报自动化系统")
    st.markdown(f"**当前运行时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    menu = ["🏠 首页概览", "🤖 生成今日研报", "📅 历史研报查看"]
    choice = st.sidebar.selectbox("功能菜单", menu)

    if choice == "🏠 首页概览":
        st.subheader("🎯 核心指数表现")
        col1, col2 = st.columns(2)
        with col1:
            st.info("A股/美股数据获取中...")
            # 示例：data_fetcher.get_a_share_index()
        with col2:
            st.info("技术面分析就绪")

    elif choice == "🤖 生成今日研报":
        if st.button("🚀 开始自动化分析并生成报告", type="primary"):
            with st.spinner("LLM 正在分析市场数据..."):
                try:
                    gen = ReportGenerator()
                    all_data = gen.fetch_all_data()
                    report_md = gen.generate_report(all_data)
                    save_path = gen.save_report(report_md)
                    st.success(f"✅ 报告生成成功！保存路径: {save_path}")
                    st.markdown("---")
                    st.markdown(report_md)
                except Exception as e:
                    st.error(f"生成失败: {str(e)}")

    elif choice == "📅 历史研报查看":
        report_dir = config.get('report', {}).get('output_dir', './reports')
        if os.path.exists(report_dir):
            files = sorted(glob.glob(os.path.join(report_dir, "*.md")), reverse=True)
            if files:
                selected_file = st.selectbox("选择日期", files)
                with open(selected_file, 'r', encoding='utf-8') as f:
                    st.markdown(f.read())
            else:
                st.warning("暂无历史研报文件。")

if __name__ == "__main__":
    main()
