import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# --- 디자인 설정 ---
st.set_page_config(layout="wide")
st.title("🎯 멀티 포인트 위치도 통합 분석 시스템")

# --- 1. 데이터 로드 부분 (포인트가 많으므로 리스트화) ---
# 실제로는 엑셀 업로드 시 반복되는 패턴(위치도, X, Y)을 자동으로 추출하도록 구현합니다.
points = ["E", "F", "G", "H", "I", "J", "K", "L"]
# 샘플 데이터 (성적서 수치 기반)
data = {
    "Point": points,
    "True_X": [-55.70, -35.80, -14.80, 5.10, -45.50, -5.10, -55.70, 5.10],
    "True_Y": [-38.80, -38.80, -38.80, -38.80, -54.70, -54.70, -70.30, -70.30],
    "Measured_X": [-55.712, -35.789, -14.805, 5.102, -45.520, -5.095, -55.731, 5.115],
    "Measured_Y": [-38.815, -38.802, -38.795, -38.810, -54.712, -54.690, -70.315, -70.305],
    "Bonus": [0.05, 0.03, 0.04, 0.02, 0.06, 0.01, 0.05, 0.04], # MMC 보너스 가상 데이터
    "Base_Tol": [0.30] * 8
}
df = pd.DataFrame(data)

# --- 2. 위치도 계산 로직 ---
df['Dev_X'] = df['Measured_X'] - df['True_X']
df['Dev_Y'] = df['Measured_Y'] - df['True_Y']
df['Actual_Pos'] = 2 * np.sqrt(df['Dev_X']**2 + df['Dev_Y']**2)
df['Final_Tol'] = df['Base_Tol'] + df['Bonus']
df['Status'] = np.where(df['Actual_Pos'] <= df['Final_Tol'], "OK", "NG")
df['Usage'] = (df['Actual_Pos'] / df['Final_Tol']) * 100

# --- 3. 시각화 레이아웃 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📍 전 포인트 편차 분포")
    fig = go.Figure()
    # 공차 한계선 (기준 0.3)
    fig.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, 
                  line=dict(color="Red", dash="dash"))
    # 포인트 찍기
    fig.add_trace(go.Scatter(x=df['Dev_X'], y=df['Dev_Y'], mode='markers+text',
                             text=df['Point'], textposition="top right",
                             marker=dict(size=10, color=df['Usage'], colorscale='RdYlGn_r', showscale=True)))
    fig.update_layout(xaxis_title="X 편차", yaxis_title="Y 편차", height=500, width=500)
    st.plotly_chart(fig)

with col2:
    st.subheader("📊 포인트별 공차 소진율")
    fig_bar = px.bar(df, x='Point', y='Usage', color='Usage', 
                     color_continuous_scale='RdYlGn_r', range_y=[0, 100])
    fig_bar.add_hline(y=100, line_dash="dash", line_color="red")
    st.plotly_chart(fig_bar)

# --- 4. 요약 리포트 ---
st.subheader("📝 종합 분석 결과")
ng_points = df[df['Status'] == "NG"]['Point'].tolist()
if not ng_points:
    st.success(f"✅ 모든 포인트 ({len(df)}개) 규격 내 만족")
else:
    st.error(f"🚨 부적합 포인트 발견: {ng_points}")

st.table(df[['Point', 'Actual_Pos', 'Final_Tol', 'Status', 'Usage']])
