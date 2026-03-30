import streamlit as st
from streamlit_autorefresh import st_autorefresh
import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import warnings

warnings.filterwarnings('ignore')

# ==========================================
# 1. 页面配置与自动刷新 (专门为粉丝挂机设计)
# ==========================================
st.set_page_config(page_title="Alpha Sniper 宏观指挥部", page_icon="🦅", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #050505; color: #e0e0e0; }
    .stMetric { background-color: #111111; border: 1px dashed #444; padding: 20px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 设定每 5 分钟 (300000 毫秒) 自动刷新一次页面
st_autorefresh(interval=300000, limit=None, key="fan_dashboard_refresh")

st.title("🦅 Alpha Sniper | 宏观作战指挥部")
st.caption(f"🔄 实时监控中 | 数据每 5 分钟自动更新 | 当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.write("---")

# ==========================================
# 2. 核心数据引擎 (带 5 分钟缓存，防封 IP)
# ==========================================
@st.cache_data(ttl=300) 
def get_macro_data():
    """
    为了保证网页秒开，这里使用基于上证指数的拟合版 VIX (零延迟体验)
    实盘个股的 T0_Count 运算量太大，留给你本地的私密雷达使用。
    """
    # A. 拉取大盘日线 (取近 200 天展示)
    df = ak.stock_zh_index_daily_em(symbol="sh000001")
    df['date'] = pd.to_datetime(df['date'])
    df = df.tail(260).copy() 
    
    # B. 计算 AMV (活跃市值指数)
    df['volume'] = pd.to_numeric(df['volume'])
    df['AMV_MA20'] = df['volume'].rolling(20).mean()
    df['AMV_Index'] = ((df['volume'] - df['AMV_MA20']) / (df['AMV_MA20'] + 1e-8)) * 300.0
    df['AMV_Index'] = df['AMV_Index'].clip(-100, 100)
    
    # C. 计算 DIY_VIX (宏观拟合版恐慌指数)
    df['Pct_Chg'] = df['close'].pct_change()
    df['Vol_Std'] = df['Pct_Chg'].rolling(20).std() * (252**0.5) * 100
    df['MA20'] = df['close'].rolling(20).mean()
    df['DIY_VIX'] = (df['Vol_Std'] - 16) * 10 - ((df['close'] - df['MA20']) / df['MA20'] * 200)
    df['DIY_VIX'] = df['DIY_VIX'].clip(-100, 100)
    
    return df.dropna().tail(200)

# ==========================================
# 3. 提取实时数据与状态判定
# ==========================================
try:
    df = get_macro_data()
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    vix_pass = curr['DIY_VIX'] >= -50
    amv_pass = curr['AMV_Index'] >= -50

    # ==========================================
    # 4. 顶层仪表盘 (黑金风格数字展示)
    # ==========================================
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("DIY_VIX (情绪面)", f"{curr['DIY_VIX']:.1f}", f"{curr['DIY_VIX']-prev['DIY_VIX']:.1f}", delta_color="inverse")
    with col2:
        st.metric("AMV_Index (资金面)", f"{curr['AMV_Index']:.1f}", f"{curr['AMV_Index']-prev['AMV_Index']:.1f}")
    with col3:
        if vix_pass and amv_pass:
            st.metric("司令部总阀门", "🟢 允许狙击")
        else:
            st.metric("司令部总阀门", "🚨 强制空仓")

    # ==========================================
    # 5. 核心图表：三线共振可视化
    # ==========================================
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 曲线1：上证指数 (主轴 - 白色半透明)
    fig.add_trace(go.Scatter(x=df['date'], y=df['close'], name="上证指数", line=dict(color='rgba(255, 255, 255, 0.6)', width=2)), secondary_y=False)
    
    # 曲线2：DIY_VIX (副轴 - 红色)
    fig.add_trace(go.Scatter(x=df['date'], y=df['DIY_VIX'], name="DIY_VIX (恐慌度)", line=dict(color='#FF3333', width=2)), secondary_y=True)
    
    # 曲线3：AMV_Index (副轴 - 青色)
    fig.add_trace(go.Scatter(x=df['date'], y=df['AMV_Index'], name="AMV (活跃度)", line=dict(color='#00FFFF', width=1.8)), secondary_y=True)

    # 绘制风控红线与黄金爆破线
    fig.add_hline(y=-50, line_dash="dash", line_color="#FF9900", secondary_y=True, annotation_text="熔断禁区线 (-50)")
    fig.add_hline(y=50, line_dash="dash", line_color="#00FF00", secondary_y=True, annotation_text="黄金爆破线 (+50)")
    fig.add_hline(y=0, line_color="#444", secondary_y=True)

    fig.update_layout(
        height=500, template="plotly_dark", hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    fig.update_yaxes(title_text="上证指数", secondary_y=False, showgrid=False)
    fig.update_yaxes(title_text="指标强度 (-100 ~ 100)", secondary_y=True, range=[-110, 110], gridcolor='#222')

    st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # 6. 底部 AI 状态判词 (增强粉丝粘性)
    # ==========================================
    st.markdown("### 🏹 当前盘面解读")
    if curr['DIY_VIX'] > 50 and curr['AMV_Index'] > -50:
        st.success("🔥 **发现【黄金爆破共振】**：大盘极度恐慌但仍有流动性承接，这是核心资产的左侧钻石底！")
    elif curr['DIY_VIX'] < -50:
        st.error("⚠️ **警告【钝刀子阴跌】**：情绪低于 -50，市场处于阴跌状态，信号虽有但无爆发力，建议空仓。")
    elif curr['AMV_Index'] < -50:
        st.error("💤 **警告【流动性陷阱】**：市场成交极度萎缩，反弹缺乏支撑，请保持克制。")
    else:
        st.info("✅ **状态【中性安全】**：宏观指标健康，量化狙击手可按部就班寻找极冰标的。")

except Exception as e:
    st.error(f"数据加载中或遇到网络波动，请稍后自动刷新... (错误代码: {e})")

# 页脚声明
st.markdown("---")
st.caption("© 2026 董子量化研发团队 | 风险提示：本雷达仅供宏观水温监控，不构成投资建议。")
