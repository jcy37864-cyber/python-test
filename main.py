import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="정밀 위치도 분석 시스템", layout="wide")

st.title("🎯 위치도(Position) 및 MMC 통합 분석 시스템")

# --- 1. 사이드바: 공정 파라미터 설정 ---
with st.sidebar:
    st.header("⚙️ 공차 설정")
    base_tolerance = st.number_input("기본 위치도 공차 (ø)", value=0.5, step=0.1)
    use_mmc = st.checkbox("MMC(최대실체조건) 적용", value=True)
    if use_mmc:
        mmc_size = st.number_input("MMC 기준 치수 (최소 구멍 지름)", value=0.5, format="%.3f")

# --- 2. 데이터 입력 (예시 구조) ---
st.subheader("📝 측정 데이터 입력")
# 실제로는 파일 업로드로 대체 가능합니다.
data = {
    "Point": ["UL", "UR", "DL", "DR"],
    "True_X": [-50.60, 0.00, -64.30, 13.70],
    "True_Y": [0.00, 0.00, -92.50, -92.50],
    "Measured_X": [-50.684, 0.000, -64.289, 13.731],
    "Measured_Y": [0.000, 0.000, -92.497, -92.586],
    "Hole_Size": [0.556, 0.524, 0.532, 0.550]  # MMC 계산용 실제 지름
}
df = pd.DataFrame(data)

# --- 3. 위치도 및 MMC 보너스 계산 로직 ---
df['Deviation_X'] = df['Measured_X'] - df['True_X']
df['Deviation_Y'] = df['Measured_Y'] - df['True_Y']
# 위치도 계산: 2 * sqrt(dx^2 + dy^2)
df['Actual_Position'] = 2 * np.sqrt(df['Deviation_X']**2 + df['Deviation_Y']**2)

if use_mmc:
    df['Bonus'] = (df['Hole_Size'] - mmc_size).clip(lower=0)
    df['Final_Tolerance'] = base_tolerance + df['Bonus']
else:
    df['Final_Tolerance'] = base_tolerance

df['Status'] = np.where(df['Actual_Position'] <= df['Final_Tolerance'], "OK", "NG")
df['Usage_Rate'] = (df['Actual_Position'] / df['Final_Tolerance']) * 100

# --- 4. 시각화 (과녁 그래프) ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 위치 편차 분포 (과녁 차트)")
    # 모든 포인트를 원점(0,0) 기준으로 정렬하여 분포 확인
    fig_target = go.Figure()
    
    # 공차 원 그리기
    max_tol = df['Final_Tolerance'].max()
    fig_target.add_shape(type="circle", x0=-base_tolerance/2, y0=-base_tolerance/2, x1=base_tolerance/2, y1=base_tolerance/2,
                         line_color="Red", line_dash="dash", name="Base Tolerance")
    
    # 측정 포인트 점 찍기
    for i, row in df.iterrows():
        fig_target.add_trace(go.Scatter(
            x=[row['Deviation_X']], y=[row['Deviation_Y']],
            mode='markers+text',
            name=row['Point'],
            text=[row['Point']],
            textposition="top center",
            marker=dict(size=12, color='Green' if row['Status'] == "OK" else 'Red')
        ))

    fig_target.update_layout(
        xaxis=dict(title="X 편차", range=[-0.5, 0.5]),
        yaxis=dict(title="Y 편차", range=[-0.5, 0.5], scaleanchor="x", scaleratio=1),
        width=600, height=600, template="plotly_white"
    )
    st.plotly_chart(fig_target)

with col2:
    st.subheader("📊 공차 소진율 (%)")
    fig_bar = px.bar(df, x='Point', y='Usage_Rate', color='Status',
                     color_discrete_map={'OK': '#10b981', 'NG': '#e11d48'},
                     range_y=[0, 120])
    fig_bar.add_hline(y=100, line_dash="dash", line_color="red")
    st.plotly_chart(fig_bar, use_container_width=True)

# --- 5. 결과 테이블 ---
st.subheader("📋 상세 분석 데이터")
st.dataframe(df.style.format({
    'Actual_Position': '{:.4f}',
    'Final_Tolerance': '{:.4f}',
    'Usage_Rate': '{:.1f}%'
}).apply(lambda x: ['background-color: #ffcccc' if v == "NG" else '' for v in x], subset=['Status']))
