# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from collections import defaultdict
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# 尝试导入networkx，如果失败则提供友好提示
try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    st.error("❌ NetworkX库未安装，请检查requirements.txt文件")

# 页面配置
st.set_page_config(
    page_title="《紅樓夢》賈母社交網絡分析",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


class JiaMuStreamlitApp:
    def __init__(self):
        self.data_loaded = False
        self.step3_data = None
        self.G = None
        self.metrics = None
        self.df_metrics = None
        self.relationship_type_analysis = None

        # 设置颜色方案
        self.colors = {
            'jiamu': '#FF6B6B',  # 贾母 - 红色
            'family_male': '#4ECDC4',  # 家族男性 - 青色
            'family_female': '#45B7D1',  # 家族女性 - 蓝色
            'servants': '#96CEB4',  # 仆人 - 绿色
            'guests': '#FFE66D',  # 客人 - 黄色
            'edge': '#D9D9D9'  # 边 - 灰色
        }

        # 定义角色类型
        self.character_types = {
            'family_male': ['賈政', '賈赦', '賈璉', '賈寶玉', '賈蓉', '賈薔', '賈蘭', '賈芸', '賈芹', '賈環', '賈瑞'],
            'family_female': ['王夫人', '邢夫人', '王熙鳳', '賈探春', '賈迎春', '賈惜春', '賈元春'],
            'servants': ['花襲人', '鴛鴦', '晴雯', '麝月', '秋紋', '碧痕', '平兒', '紫鵑'],
            'guests': ['林黛玉', '薛寶釵', '史湘雲', '妙玉', '李紈', '秦可卿', '香菱']
        }

    def load_data(self):
        """加载分析数据"""
        try:
            data_path = "output/step3_data.json"
            if not os.path.exists(data_path):
                st.error(f"❌ 数据文件不存在: {data_path}")
                return False

            with open(data_path, 'r', encoding='utf-8') as f:
                self.step3_data = json.load(f)

            # 重建网络（如果networkx可用）
            if NETWORKX_AVAILABLE and self.step3_data.get('network'):
                self.G = nx.node_link_graph(self.step3_data['network'])
            else:
                self.G = None

            self.metrics = self.step3_data.get('metrics', {})
            self.df_metrics = pd.DataFrame(self.step3_data['df_metrics']) if self.step3_data.get('df_metrics') else None
            self.relationship_type_analysis = self.step3_data.get('relationship_type_analysis', {})

            self.data_loaded = True
            return True

        except Exception as e:
            st.error(f"❌ 数据加载失败: {e}")
            return False

    def get_character_type(self, character):
        """获取角色类型"""
        for type_name, characters in self.character_types.items():
            if character in characters:
                return type_name
        return 'other'

    def show_environment_check(self):
        """显示环境检查结果"""
        st.sidebar.title("環境檢查")

        # 检查依赖库
        libraries = {
            'streamlit': st.__version__ if 'st' in globals() else None,
            'pandas': pd.__version__ if 'pd' in globals() else None,
            'networkx': '可用' if NETWORKX_AVAILABLE else '不可用',
            'plotly': go.__version__ if 'go' in globals() else None
        }

        for lib, status in libraries.items():
            if status:
                st.sidebar.success(f"✅ {lib}: {status}")
            else:
                st.sidebar.error(f"❌ {lib}: 不可用")

        # 检查数据加载
        if self.data_loaded:
            st.sidebar.success("✅ 數據加載成功")
        else:
            st.sidebar.warning("⚠ 數據未加載")

    def show_network_overview(self):
        """显示网络概览"""
        st.header("📊 網絡概覽")

        if not self.data_loaded:
            st.warning("請先加載數據")
            return

        # 基本统计信息
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
                density = nx.density(self.G) if self.G else 0
                st.metric("網絡密度", f"{density:.4f}")
            else:
                st.metric("網絡密度", "N/A")

        with col4:
            if self.G and '賈母' in self.G:
                degree = self.G.degree('賈母')
                st.metric("賈母的度", degree)
            else:
                st.metric("賈母的度", "N/A")

        # 贾母中心性指标
        st.subheader("賈母中心性指標")
        if self.metrics and 'jiamu_metrics' in self.metrics:
            jm_metrics = self.metrics['jiamu_metrics']
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("度中心性", f"{jm_metrics.get('degree_centrality', 0):.4f}")
            with col2:
                st.metric("中介中心性", f"{jm_metrics.get('betweenness_centrality', 0):.4f}")
            with col3:
                st.metric("接近中心性", f"{jm_metrics.get('closeness_centrality', 0):.4f}")
            with col4:
                st.metric("特徵向量中心性", f"{jm_metrics.get('eigenvector_centrality', 0):.4f}")

    def show_relationship_analysis(self):
        """显示关系分析"""
        st.header("🤝 關係分析")

        if not self.data_loaded or self.df_metrics is None:
            st.warning("請先加載數據")
            return

        # 关系强度排名
        jiamu_related = self.df_metrics[self.df_metrics['weight_to_jiamu'] > 0].copy()
        jiamu_related = jiamu_related.sort_values('weight_to_jiamu', ascending=False)
        top_10 = jiamu_related.head(10)

        # 创建条形图
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

        # 显示详细数据
        st.subheader("詳細關係數據")
        st.dataframe(top_10[['character', 'weight_to_jiamu', 'degree', 'degree_centrality']])

    def show_network_visualization(self):
        """显示网络可视化"""
        st.header("🌐 網絡可視化")

        if not self.data_loaded or not NETWORKX_AVAILABLE or self.G is None:
            if not NETWORKX_AVAILABLE:
                st.error("❌ NetworkX庫不可用，無法生成網絡圖")
                st.info("請確保requirements.txt中包含networkx>=3.0")
            else:
                st.warning("網絡數據不可用")
            return

        # 简单的网络统计图
        if self.G and '賈母' in self.G:
            # 获取贾母的邻居
            neighbors = list(self.G.neighbors('賈母'))
            neighbor_data = []

            for neighbor in neighbors:
                weight = self.G['賈母'][neighbor]['weight']
                char_type = self.get_character_type(neighbor)
                neighbor_data.append({
                    'character': neighbor,
                    'weight': weight,
                    'type': char_type
                })

            df_neighbors = pd.DataFrame(neighbor_data)

            # 按类型分组
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
                char_type_cn = {
                    'family_male': '家族男性',
                    'family_female': '家族女性',
                    'servants': '僕人',
                    'guests': '客人',
                    'other': '其他'
                }.get(row['type'], row['type'])

                st.write(f"- **{row['character']}** ({char_type_cn}): 關係強度 {row['weight']}")

    def show_centrality_analysis(self):
        """显示中心性分析"""
        st.header("📈 中心性分析")

        if not self.data_loaded or self.df_metrics is None:
            st.warning("請先加載數據")
            return

        # 中心性指标对比
        centrality_metrics = ['degree_centrality', 'betweenness_centrality', 'closeness_centrality',
                              'eigenvector_centrality']
        metric_names = {
            'degree_centrality': '度中心性',
            'betweenness_centrality': '中介中心性',
            'closeness_centrality': '接近中心性',
            'eigenvector_centrality': '特徵向量中心性'
        }

        # 筛选有数据的角色
        valid_chars = self.df_metrics[self.df_metrics['weight_to_jiamu'] > 0].head(8)

        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[metric_names[metric] for metric in centrality_metrics]
        )

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

        for i, metric in enumerate(centrality_metrics):
            row = i // 2 + 1
            col = i % 2 + 1

            fig.add_trace(
                go.Bar(
                    x=valid_chars['character'],
                    y=valid_chars[metric],
                    name=metric_names[metric],
                    marker_color=colors[i]
                ),
                row=row, col=col
            )

        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    def show_about(self):
        """显示关于信息"""
        st.header("ℹ️ 關於項目")

        st.markdown("""
        ### 項目簡介
        本項目對《紅樓夢》中賈母的社交網絡進行量化分析，使用社交網絡分析(SNA)方法揭示人物關係結構。

        ### 技術棧
        - **Python**: 主要編程語言
        - **NetworkX**: 社交網絡分析
        - **Plotly**: 交互式可視化
        - **Streamlit**: Web應用框架
        - **Pandas**: 數據處理

        ### 數據來源
        - 分析基於《紅樓夢》1-40回文本
        - 使用共現分析和對話關係提取

        ### 部署說明
        1. 確保`requirements.txt`包含所有依賴庫
        2. 數據文件應位於`output/step3_data.json`
        3. 應用會自動檢查環境和加載數據
        """)

        # 显示文件结构
        with st.expander("項目文件結構"):
            st.code("""
            your-repo/
            ├── requirements.txt          # 依賴庫列表
            ├── streamlit_app.py         # 主應用文件
            ├── output/                  # 數據目錄
            │   └── step3_data.json     # 分析數據
            └── README.md               # 項目說明
            """)

        # 故障排除指南
        with st.expander("故障排除"):
            st.markdown("""
            ### 常見問題解決方案

            **1. ModuleNotFoundError: No module named 'networkx'**
            - 解決方案: 確保`requirements.txt`包含`networkx>=3.0`

            **2. 數據文件加載失敗**
            - 解決方案: 檢查`output/step3_data.json`文件是否存在

            **3. Streamlit Cloud部署失敗**
            - 解決方案: 檢查requirements.txt格式和依賴版本兼容性
            """)

    def run(self):
        """运行主应用"""
        # 应用标题
        st.title("📖《紅樓夢》賈母社交網絡分析系統")
        st.markdown("---")

        # 侧边栏导航
        st.sidebar.title("導航選單")
        app_section = st.sidebar.radio(
            "選擇分析模塊",
            ["🏠 首頁", "📊 網絡概覽", "🤝 關係分析", "🌐 網絡可視化", "📈 中心性分析", "ℹ️ 關於項目"]
        )

        # 显示环境检查
        self.show_environment_check()

        # 加载数据（只在需要时加载）
        if not self.data_loaded:
            with st.spinner("正在加載數據..."):
                self.load_data()

        # 根据选择显示不同内容
        if app_section == "🏠 首頁":
            self.show_homepage()
        elif app_section == "📊 網絡概覽":
            self.show_network_overview()
        elif app_section == "🤝 關係分析":
            self.show_relationship_analysis()
        elif app_section == "🌐 網絡可視化":
            self.show_network_visualization()
        elif app_section == "📈 中心性分析":
            self.show_centrality_analysis()
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
            - 中心性指標計算與對比

            📈 **數據可視化**
            - 交互式網絡圖
            - 關係強度排名圖表
            - 中心性指標對比分析

            📊 **統計分析**
            - 網絡密度計算
            - 角色重要性排名
            - 關係類型分佈分析
            """)

        with col2:
            # 快速状态检查
            st.subheader("系統狀態")

            status_items = [
                ("Python環境", "✅ 正常", "❌ 異常"),
                ("數據加載", "✅ 成功" if self.data_loaded else "⚠ 加載中", "❌ 失敗"),
                ("NetworkX", "✅ 可用" if NETWORKX_AVAILABLE else "❌ 不可用", ""),
                ("可視化庫", "✅ 就緒", "❌ 缺失")
            ]

            for item, success, failure in status_items:
                if success.startswith("✅") or success.startswith("⚠"):
                    st.success(success)
                else:
                    st.error(failure)

        # 功能简介
        st.markdown("---")
        st.subheader("快速開始")

        tab1, tab2, tab3 = st.tabs(["📊 查看統計", "🤝 分析關係", "🌐 可視化網絡"])

        with tab1:
            st.markdown("""
            **網絡概覽模塊**提供：
            - 基本網絡統計信息
            - 賈母中心性指標
            - 網絡密度分析
            """)
            if st.button("前往網絡概覽"):
                st.session_state.page = "網絡概覽"

        with tab2:
            st.markdown("""
            **關係分析模塊**提供：
            - 賈母與各角色關係強度排名
            - 詳細關係數據表格
            - 關係類型分佈分析
            """)
            if st.button("前往關係分析"):
                st.session_state.page = "關係分析"

        with tab3:
            st.markdown("""
            **網絡可視化模塊**提供：
            - 交互式關係網絡圖
            - 角色類型分佈可視化
            - 中心性指標對比圖表
            """)
            if st.button("前往網絡可視化"):
                st.session_state.page = "網絡可視化"


# 主函数
def main():
    # 初始化应用
    app = JiaMuStreamlitApp()

    # 运行应用
    app.run()


if __name__ == "__main__":
    # 初始化session state
    if 'page' not in st.session_state:
        st.session_state.page = "首頁"

    main()