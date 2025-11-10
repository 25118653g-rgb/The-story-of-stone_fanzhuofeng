# jiamu_streamlit_app.py
import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
from collections import defaultdict
import numpy as np
from math import cos, sin, pi

# 设置页面配置
st.set_page_config(
    page_title="《紅樓夢》賈母社交網絡分析",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.8rem;
        color: #3498db;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        margin-bottom: 1rem;
    }
    .character-card {
        background-color: #e8f4f8;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


class JiaMuStreamlitApp:
    def __init__(self, data_path):
        self.data_path = data_path
        self.load_data()
        self.setup_colors()

    def load_data(self):
        """加载数据"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.step3_data = json.load(f)

            # 重建网络
            if self.step3_data['network']:
                self.G = nx.node_link_graph(self.step3_data['network'])
            else:
                self.G = None

            self.metrics = self.step3_data['metrics']
            self.df_metrics = pd.DataFrame(self.step3_data['df_metrics']) if self.step3_data['df_metrics'] else None
            self.relationship_type_analysis = self.step3_data.get('relationship_type_analysis', {})

            st.success("数据加载成功！")
        except Exception as e:
            st.error(f"数据加载失败: {e}")
            self.G = None

    def setup_colors(self):
        """设置颜色方案"""
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

    def get_character_type(self, character):
        """获取角色类型"""
        for type_name, characters in self.character_types.items():
            if character in characters:
                return type_name
        return 'other'

    def create_central_network_plot(self):
        """创建以贾母为中心的网络图"""
        if self.G is None:
            st.error("网络数据不可用")
            return None

        # 提取与贾母直接相连的节点
        jiamu_neighbors = list(self.G.neighbors('賈母'))

        if not jiamu_neighbors:
            st.error("贾母没有直接相连的节点")
            return None

        # 创建子图
        central_nodes = ['賈母'] + jiamu_neighbors
        subgraph = self.G.subgraph(central_nodes)

        # 计算圆形布局
        pos = {}
        pos['賈母'] = (0, 0)  # 贾母在中心

        # 其他节点均匀分布在圆周上
        radius = 2.0
        angle_step = 2 * pi / len(jiamu_neighbors)

        for i, node in enumerate(jiamu_neighbors):
            angle = i * angle_step
            x = radius * cos(angle)
            y = radius * sin(angle)
            pos[node] = (x, y)

        # 准备节点数据
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        node_color = []
        node_names = []

        for node in subgraph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_names.append(node)

            # 节点大小基于与贾母的关系强度
            if node == '賈母':
                size = 50
                color = self.colors['jiamu']
                node_text.append(f"<b>賈母</b><br>(核心人物)<br>度: {self.G.degree(node)}")
            else:
                weight = self.G['賈母'][node]['weight']
                size = max(20, weight * 5)

                # 根据角色类型设置颜色
                char_type = self.get_character_type(node)
                if char_type in self.colors:
                    color = self.colors[char_type]
                else:
                    color = '#CCCCCC'

                type_names = {
                    'family_male': '家族男性',
                    'family_female': '家族女性',
                    'servants': '僕人',
                    'guests': '客人',
                    'other': '其他'
                }

                node_text.append(f"<b>{node}</b><br>({type_names[char_type]})<br>關係強度: {weight}")

            node_size.append(size)
            node_color.append(color)

        # 创建节点轨迹
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_names,
            textposition="middle center",
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=2, color='darkblue')
            ),
            textfont=dict(size=12, color="black"),
            hovertemplate='%{text}<extra></extra>'
        )

        # 提取边信息（只显示与贾母相连的边）
        edge_x = []
        edge_y = []

        for edge in subgraph.edges():
            if '賈母' in edge:
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

        # 创建边轨迹
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color=self.colors['edge']),
            hoverinfo='none',
            mode='lines'
        )

        # 创建图表
        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
                            title=dict(
                                text='《紅樓夢》賈母中心關係網絡圖',
                                font=dict(size=20),
                                x=0.5,
                                xanchor='center'
                            ),
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=20, l=20, r=20, t=60),
                            annotations=[
                                dict(
                                    text="紅色: 賈母, 青色: 家族男性, 藍色: 家族女性, 綠色: 僕人, 黃色: 客人",
                                    showarrow=False,
                                    xref="paper", yref="paper",
                                    x=0.5, y=-0.1,
                                    xanchor='center',
                                    font=dict(size=12)
                                )
                            ],
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-3, 3]),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-3, 3]),
                            width=800,
                            height=700
                        ))

        return fig

    def create_relationship_strength_chart(self):
        """创建关系强度图表"""
        if self.df_metrics is None:
            st.error("指标数据不可用")
            return None

        # 筛选出与贾母有直接关系的角色，按关系强度排序
        jiamu_related = self.df_metrics[self.df_metrics['weight_to_jiamu'] > 0].copy()
        jiamu_related = jiamu_related.sort_values('weight_to_jiamu', ascending=True)  # 升序排列

        # 取前15个角色
        top_15 = jiamu_related.head(15)

        # 为每个角色分配颜色
        colors = []
        for character in top_15['character']:
            char_type = self.get_character_type(character)
            if char_type in self.colors:
                colors.append(self.colors[char_type])
            else:
                colors.append('#CCCCCC')

        # 创建水平条形图
        fig = px.bar(
            top_15,
            x='weight_to_jiamu',
            y='character',
            orientation='h',
            title='賈母與各角色關係強度排名（前15名）',
            labels={'weight_to_jiamu': '關係強度', 'character': '角色'},
            color_discrete_sequence=colors
        )

        fig.update_layout(
            height=600,
            showlegend=False,
            xaxis_title='關係強度',
            yaxis_title='角色'
        )

        return fig

    def create_relationship_type_chart(self):
        """创建关系类型图表"""
        if not self.relationship_type_analysis:
            st.error("关系类型分析数据不可用")
            return None

        # 准备数据
        labels = ['家族男性', '家族女性', '僕人', '客人']
        values = [
            self.relationship_type_analysis['family_male']['total_weight'],
            self.relationship_type_analysis['family_female']['total_weight'],
            self.relationship_type_analysis['servants']['total_weight'],
            self.relationship_type_analysis['guests']['total_weight']
        ]

        colors = [
            self.colors['family_male'],
            self.colors['family_female'],
            self.colors['servants'],
            self.colors['guests']
        ]

        # 创建饼图
        fig = px.pie(
            values=values,
            names=labels,
            title='賈母與不同類型角色的關係強度分佈',
            color_discrete_sequence=colors
        )

        fig.update_traces(textinfo='percent+label+value')

        return fig

    def create_centrality_comparison_chart(self):
        """创建中心性指标对比图"""
        if self.df_metrics is None:
            st.error("指标数据不可用")
            return None

        # 筛选出与贾母有直接关系的角色
        jiamu_related = self.df_metrics[self.df_metrics['weight_to_jiamu'] > 0].copy()

        # 取前10个角色
        top_10 = jiamu_related.head(10)

        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('度中心性', '中介中心性', '接近中心性', '特徵向量中心性'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        # 度中心性
        fig.add_trace(
            go.Bar(x=top_10['character'],
                   y=top_10['degree_centrality'],
                   marker_color='lightblue',
                   name='度中心性'),
            row=1, col=1
        )

        # 中介中心性
        fig.add_trace(
            go.Bar(x=top_10['character'],
                   y=top_10['betweenness_centrality'],
                   marker_color='lightgreen',
                   name='中介中心性'),
            row=1, col=2
        )

        # 接近中心性
        fig.add_trace(
            go.Bar(x=top_10['character'],
                   y=top_10['closeness_centrality'],
                   marker_color='lightcoral',
                   name='接近中心性'),
            row=2, col=1
        )

        # 特征向量中心性
        fig.add_trace(
            go.Bar(x=top_10['character'],
                   y=top_10['eigenvector_centrality'],
                   marker_color='lightsalmon',
                   name='特徵向量中心性'),
            row=2, col=2
        )

        fig.update_layout(
            height=800,
            showlegend=False,
            title_text='賈母社交網絡中心性指標對比分析'
        )

        return fig

    def display_network_statistics(self):
        """显示网络统计信息"""
        if self.G is None:
            st.error("网络数据不可用")
            return

        # 获取网络统计信息
        node_count = self.G.number_of_nodes()
        edge_count = self.G.number_of_edges()
        network_density = nx.density(self.G)
        average_degree = sum(dict(self.G.degree()).values()) / node_count

        # 贾母的度
        jiamu_degree = self.G.degree('賈母')

        # 与贾母关系最强的角色
        jiamu_neighbors = list(self.G.neighbors('賈母'))
        neighbor_strengths = []
        for neighbor in jiamu_neighbors:
            weight = self.G['賈母'][neighbor]['weight']
            neighbor_strengths.append((neighbor, weight))

        neighbor_strengths.sort(key=lambda x: x[1], reverse=True)
        top_relationships = neighbor_strengths[:10]

        # 创建列布局
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("節點數量", node_count)

        with col2:
            st.metric("邊數量", edge_count)

        with col3:
            st.metric("網絡密度", f"{network_density:.4f}")

        with col4:
            st.metric("平均度", f"{average_degree:.2f}")

        # 显示贾母中心性指标
        st.subheader("賈母中心性指標")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("度中心性", f"{self.metrics['jiamu_metrics']['degree_centrality']:.4f}")

        with col2:
            st.metric("中介中心性", f"{self.metrics['jiamu_metrics']['betweenness_centrality']:.4f}")

        with col3:
            st.metric("接近中心性", f"{self.metrics['jiamu_metrics']['closeness_centrality']:.4f}")

        with col4:
            st.metric("特徵向量中心性", f"{self.metrics['jiamu_metrics']['eigenvector_centrality']:.4f}")

        # 显示与贾母关系最强的角色
        st.subheader("與賈母關係最強的角色（前10名）")

        for i, (char, weight) in enumerate(top_relationships, 1):
            char_type = self.get_character_type(char)
            type_color = self.colors.get(char_type, '#CCCCCC')

            st.markdown(f"""
            <div class="character-card">
                <strong>{i}. {char}</strong> - 關係強度: {weight} 
                <span style="color: {type_color}; font-weight: bold;">({char_type})</span>
            </div>
            """, unsafe_allow_html=True)

    def run(self):
        """运行Streamlit应用"""
        # 应用标题
        st.markdown('<div class="main-header">《紅樓夢》賈母社交網絡分析</div>', unsafe_allow_html=True)

        # 侧边栏
        st.sidebar.title("導航選單")
        app_section = st.sidebar.radio(
            "選擇分析模塊",
            ["網絡概覽", "關係網絡圖", "關係強度分析", "中心性指標", "關於項目"]
        )

        # 根据选择显示不同内容
        if app_section == "網絡概覽":
            self.show_network_overview()
        elif app_section == "關係網絡圖":
            self.show_network_diagram()
        elif app_section == "關係強度分析":
            self.show_relationship_analysis()
        elif app_section == "中心性指標":
            self.show_centrality_metrics()
        elif app_section == "關於項目":
            self.show_about()

    def show_network_overview(self):
        """显示网络概览"""
        st.markdown('<div class="section-header">網絡概覽</div>', unsafe_allow_html=True)

        # 显示网络统计信息
        self.display_network_statistics()

        # 显示关系类型分析
        st.markdown('<div class="section-header">關係類型分析</div>', unsafe_allow_html=True)

        if self.relationship_type_analysis:
            col1, col2 = st.columns(2)

            with col1:
                # 创建关系类型图表
                fig = self.create_relationship_type_chart()
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                # 显示关系类型统计
                st.subheader("關係類型統計")

                for type_name, analysis in self.relationship_type_analysis.items():
                    type_cn = {
                        'family_male': '家族男性',
                        'family_female': '家族女性',
                        'servants': '僕人',
                        'guests': '客人'
                    }.get(type_name, type_name)

                    st.metric(
                        f"{type_cn}關係強度",
                        f"{analysis['total_weight']}",
                        f"涉及{analysis['character_count']}個角色"
                    )
        else:
            st.warning("關係類型分析數據不可用")

    def show_network_diagram(self):
        """显示网络图"""
        st.markdown('<div class="section-header">賈母中心關係網絡圖</div>', unsafe_allow_html=True)

        # 创建网络图
        fig = self.create_central_network_plot()
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("無法生成關係網絡圖")

        # 网络图说明
        st.markdown("""
        ### 圖表說明
        - **紅色節點**: 賈母（核心人物）
        - **青色節點**: 家族男性角色
        - **藍色節點**: 家族女性角色
        - **綠色節點**: 僕人角色
        - **黃色節點**: 客人角色
        - **節點大小**: 表示與賈母的關係強度
        - **連線**: 表示角色之間的關係

        ### 交互功能
        - **鼠標懸停**: 查看角色詳細信息
        - **縮放**: 使用鼠標滾輪縮放圖表
        - **拖拽**: 拖拽圖表查看不同部分
        """)

    def show_relationship_analysis(self):
        """显示关系强度分析"""
        st.markdown('<div class="section-header">關係強度分析</div>', unsafe_allow_html=True)

        # 创建关系强度图表
        fig = self.create_relationship_strength_chart()
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("無法生成關係強度圖表")

        # 显示详细的关系数据
        if self.df_metrics is not None:
            st.markdown('<div class="section-header">詳細關係數據</div>', unsafe_allow_html=True)

            # 筛选出与贾母有直接关系的角色
            jiamu_related = self.df_metrics[self.df_metrics['weight_to_jiamu'] > 0].copy()
            jiamu_related = jiamu_related.sort_values('weight_to_jiamu', ascending=False)

            # 显示数据表格
            st.dataframe(
                jiamu_related[['character', 'weight_to_jiamu', 'degree', 'degree_centrality']].head(20),
                use_container_width=True
            )

    def show_centrality_metrics(self):
        """显示中心性指标"""
        st.markdown('<div class="section-header">中心性指標分析</div>', unsafe_allow_html=True)

        # 创建中心性指标对比图
        fig = self.create_centrality_comparison_chart()
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("無法生成中心性指標圖表")

        # 中心性指标说明
        st.markdown("""
        ### 中心性指標說明
        - **度中心性 (Degree Centrality)**: 衡量節點的直接連接數量，反映節點的活躍程度
        - **中介中心性 (Betweenness Centrality)**: 衡量節點在網絡中作為橋樑的重要性，反映信息控制能力
        - **接近中心性 (Closeness Centrality)**: 衡量節點到其他節點的平均距離，反映信息傳遞效率
        - **特徵向量中心性 (Eigenvector Centrality)**: 衡量節點與重要節點連接的程度，反映節點的影響力

        ### 分析解讀
        賈母在各項中心性指標中都表現出很高的值，這表明她在《紅樓夢》社交網絡中處於核心位置：
        - 高**度中心性**表明賈母與眾多角色有直接聯繫
        - 高**中介中心性**表明賈母在信息傳遞中扮演關鍵角色
        - 高**接近中心性**表明賈母能夠快速接觸到網絡中的其他角色
        - 高**特徵向量中心性**表明賈母與網絡中的重要角色有緊密聯繫
        """)

    def show_about(self):
        """显示关于项目的信息"""
        st.markdown('<div class="section-header">關於項目</div>', unsafe_allow_html=True)

        st.markdown("""
        ### 項目簡介
        本項目通過社交網絡分析(Social Network Analysis, SNA)方法，對《紅樓夢》中賈母的社交關係進行量化分析。
        通過提取文本中的人物共現關係，構建賈母的社交網絡，並使用多種網絡指標分析賈母在賈府社交結構中的地位和作用。

        ### 分析方法
        1. **文本預處理**: 對《紅樓夢》1-40回文本進行清洗和人物名稱標準化
        2. **關係提取**: 基於共現分析提取賈母與其他角色的互動關係
        3. **網絡構建**: 使用NetworkX構建賈母的社交網絡
        4. **指標計算**: 計算度中心性、中介中心性、接近中心性、特徵向量中心性等網絡指標
        5. **可視化分析**: 使用Plotly創建交互式可視化圖表

        ### 技術棧
        - **Python**: 主要編程語言
        - **NetworkX**: 社交網絡分析庫
        - **Plotly**: 交互式可視化庫
        - **Streamlit**: Web應用框架
        - **Pandas**: 數據處理庫

        ### 數據來源
        - 分析基於《紅樓夢》1-40回文本
        - 文本來源: 中國哲學書電子化計劃

        ### 項目意義
        通過量化分析方法，揭示傳統文學作品中的人物關係結構，為文學研究提供新的視角和方法。
        特別關注賈母這一重要角色，分析她在家族社交網絡中的核心地位和作用機制。
        """)

        # 显示数据统计
        if self.G is not None:
            st.markdown("""
            ### 數據統計
            """)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("分析章回", "1-40回")

            with col2:
                st.metric("網絡節點數", self.G.number_of_nodes())

            with col3:
                st.metric("關係邊數", self.G.number_of_edges())


# 主函数
def main():
    # 应用标题
    st.markdown('<div class="main-header">《紅樓夢》賈母社交網絡分析</div>', unsafe_allow_html=True)

    # 数据路径
    data_path = "output/step3_data.json"

    # 检查数据文件是否存在
    if not os.path.exists(data_path):
        st.error(f"数据文件不存在: {data_path}")
        st.info("请先运行数据分析脚本生成数据文件")
        return

    # 初始化应用
    app = JiaMuStreamlitApp(data_path)

    # 运行应用
    app.run()


if __name__ == "__main__":
    main()