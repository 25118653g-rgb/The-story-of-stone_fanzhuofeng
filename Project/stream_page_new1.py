# streamlit_app_fixed.py
import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from collections import defaultdict

# 正确导入plotly并获取版本信息
try:
    import plotly  # 首先导入plotly主模块
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots

    PLOTLY_AVAILABLE = True
    PLOTLY_VERSION = plotly.__version__  # 正确获取版本
except ImportError:
    PLOTLY_AVAILABLE = False
    PLOTLY_VERSION = None

# 检查networkx
try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

# 页面配置
st.set_page_config(
    page_title="《紅樓夢》賈母社交網絡分析",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


class JiaMuAnalyzer:
    def __init__(self):
        self.data_loaded = False
        self.data = None
        self.G = None

    def load_data(self):
        """加载数据"""
        try:
            data_path = "output/step3_data.json"
            if not os.path.exists(data_path):
                st.warning("数据文件不存在，将使用演示数据")
                return False

            with open(data_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

            # 重建网络（如果networkx可用）
            if NETWORKX_AVAILABLE and self.data.get('network'):
                self.G = nx.node_link_graph(self.data['network'])

            self.data_loaded = True
            return True
        except Exception as e:
            st.error(f"数据加载失败: {e}")
            return False

    def show_environment_check(self):
        """显示环境检查 - 修复版本"""
        st.sidebar.title("🔧 環境檢查")

        # 修复版本检查代码
        libraries = {
            'streamlit': st.__version__,
            'pandas': pd.__version__,
            'numpy': np.__version__,
            'networkx': '可用' if NETWORKX_AVAILABLE else '不可用',
            'plotly': PLOTLY_VERSION if PLOTLY_AVAILABLE else '不可用'
        }

        for lib, version in libraries.items():
            if version and version != '不可用':
                st.sidebar.success(f"✅ {lib}: {version}")
            else:
                st.sidebar.error(f"❌ {lib}: {version}")

        # 数据状态
        if self.data_loaded:
            st.sidebar.success("✅ 數據加載成功")
        else:
            st.sidebar.warning("⚠ 數據未加載")

    def show_network_stats(self):
        """显示网络统计信息"""
        st.header("📊 網絡統計")

        if not self.data_loaded:
            st.info("請先加載數據")
            return

        # 基本统计
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if self.G:
                st.metric("節點數量", self.G.number_of_nodes())
            else:
                st.metric("節點數量", "N/A")

        with col2:
            if self.G:
                st.metric("邊數量", self.G.number_of_edges())
            else:
                st.metric("邊數量", "N/A")

        with col3:
            if self.G:
                density = nx.density(self.G) if NETWORKX_AVAILABLE else 0
                st.metric("網絡密度", f"{density:.4f}")
            else:
                st.metric("網絡密度", "N/A")

        with col4:
            if self.G and '賈母' in self.G:
                degree = self.G.degree('賈母')
                st.metric("賈母的度", degree)
            else:
                st.metric("賈母的度", "N/A")

    def show_relationship_analysis(self):
        """显示关系分析"""
        st.header("🤝 關係分析")

        if not self.data_loaded or not PLOTLY_AVAILABLE:
            st.warning("請先加載數據並確保Plotly可用")
            return

        # 获取关系数据
        df_metrics = pd.DataFrame(self.data['df_metrics']) if self.data.get('df_metrics') else None

        if df_metrics is None:
            st.warning("無關係數據可用")
            return

        # 筛选与贾母有关系的角色
        jiamu_related = df_metrics[df_metrics['weight_to_jiamu'] > 0].copy()
        jiamu_related = jiamu_related.sort_values('weight_to_jiamu', ascending=True)

        # 取前10名
        top_10 = jiamu_related.head(10)

        # 创建水平条形图
        fig = px.bar(
            top_10,
            x='weight_to_jiamu',
            y='character',
            orientation='h',
            title='賈母關係強度排名（前10名）',
            labels={'weight_to_jiamu': '關係強度', 'character': '角色'}
        )

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    def show_simple_network_viz(self):
        """显示简化的网络可视化"""
        st.header("🌐 網絡可視化")

        if not self.data_loaded or not PLOTLY_AVAILABLE:
            st.warning("可視化功能不可用")
            return

        if self.G is None or '賈母' not in self.G:
            st.warning("網絡數據不完整")
            return

        # 获取贾母的邻居
        neighbors = list(self.G.neighbors('賈母'))
        if not neighbors:
            st.warning("賈母沒有直接相連的角色")
            return

        # 创建简单的饼图显示关系类型分布
        neighbor_data = []
        for neighbor in neighbors:
            weight = self.G['賈母'][neighbor]['weight']
            # 简单分类
            if '賈' in neighbor:
                char_type = '家族成員'
            elif '人' in neighbor or '兒' in neighbor:
                char_type = '僕人'
            else:
                char_type = '客人'

            neighbor_data.append({
                'character': neighbor,
                'weight': weight,
                'type': char_type
            })

        df_neighbors = pd.DataFrame(neighbor_data)
        type_summary = df_neighbors.groupby('type')['weight'].sum().reset_index()

        # 创建饼图
        fig = px.pie(
            type_summary,
            values='weight',
            names='type',
            title='賈母關係類型分佈'
        )

        st.plotly_chart(fig, use_container_width=True)

        # 显示邻居列表
        st.subheader("與賈母直接相連的角色")
        for i, row in df_neighbors.iterrows():
            st.write(f"- **{row['character']}** ({row['type']}): 關係強度 {row['weight']}")

    def show_about(self):
        """显示关于信息"""
        st.header("ℹ️ 關於項目")

        st.markdown("""
        ### 項目簡介
        本系統對《紅樓夢》中賈母的社交網絡進行量化分析。

        ### 技術棧
        - **Streamlit**: Web應用框架
        - **Plotly**: 數據可視化
        - **NetworkX**: 社交網絡分析
        - **Pandas**: 數據處理

        ### 數據來源
        - 《紅樓夢》1-40回文本分析
        - 基於共現關係和對話關係提取
        """)

        # 显示文件结构
        with st.expander("項目文件結構"):
            st.code("""
            your-repo/
            ├── requirements.txt          # 依賴列表
            ├── streamlit_app.py         # 主應用文件
            ├── output/                  # 數據目錄
            │   └── step3_data.json     # 分析數據
            └── README.md               # 項目說明
            """)

        # 显示requirements.txt内容
        with st.expander("requirements.txt內容"):
            st.code("""
            streamlit>=1.22.0
            pandas>=1.5.0
            networkx>=3.0
            plotly>=5.0.0
            numpy>=1.21.0
            """)

    def run(self):
        """运行主应用"""
        st.title("📖《紅樓夢》賈母社交網絡分析系統")
        st.markdown("---")

        # 加载数据
        if not self.data_loaded:
            with st.spinner("正在加載數據..."):
                self.load_data()

        # 侧边栏导航
        st.sidebar.title("📋 導航選單")
        app_section = st.sidebar.radio(
            "選擇分析模塊",
            ["🏠 首頁", "📊 網絡統計", "🤝 關係分析", "🌐 網絡可視化", "ℹ️ 關於項目"]
        )

        # 显示环境检查
        self.show_environment_check()

        # 根据选择显示内容
        if app_section == "🏠 首頁":
            self.show_homepage()
        elif app_section == "📊 網絡統計":
            self.show_network_stats()
        elif app_section == "🤝 關係分析":
            self.show_relationship_analysis()
        elif app_section == "🌐 網絡可視化":
            self.show_simple_network_viz()
        elif app_section == "ℹ️ 關於項目":
            self.show_about()

    def show_homepage(self):
        """显示首页"""
        st.header("歡迎使用賈母社交網絡分析系統")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("""
            ### 系統功能

            🔍 **人物關係分析**
            - 賈母與各角色的關係強度量化
            - 社交網絡結構可視化
            - 中心性指標計算

            📈 **數據可視化**
            - 交互式關係圖表
            - 關係強度排名
            - 網絡統計分析

            📊 **統計分析**
            - 網絡密度計算
            - 角色重要性排名
            - 關係類型分佈
            """)

        with col2:
            st.subheader("系統狀態")

            # 状态检查
            status_items = [
                ("Python環境", "✅ 正常"),
                ("數據加載", "✅ 成功" if self.data_loaded else "⚠ 加載中"),
                ("NetworkX", "✅ 可用" if NETWORKX_AVAILABLE else "❌ 不可用"),
                ("Plotly", "✅ 可用" if PLOTLY_AVAILABLE else "❌ 不可用")
            ]

            for item, status in status_items:
                if status.startswith("✅"):
                    st.success(f"{item}: {status}")
                elif status.startswith("⚠"):
                    st.warning(f"{item}: {status}")
                else:
                    st.error(f"{item}: {status}")

        # 快速功能入口
        st.markdown("---")
        st.subheader("快速開始")

        cols = st.columns(3)
        with cols[0]:
            if st.button("📊 查看網絡統計"):
                st.session_state.section = "網絡統計"
        with cols[1]:
            if st.button("🤝 分析關係"):
                st.session_state.section = "關係分析"
        with cols[2]:
            if st.button("🌐 可視化網絡"):
                st.session_state.section = "網絡可視化"


def main():
    # 初始化session state
    if 'section' not in st.session_state:
        st.session_state.section = "首頁"

    # 创建并运行应用
    app = JiaMuAnalyzer()
    app.run()


if __name__ == "__main__":
    main()
