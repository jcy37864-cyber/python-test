import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="위치도 분석 시스템 v2.3", layout="wide")

# CSS: 성적서 느낌의 디자인
st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .status-ok { background-color: #f0fff4; border: 1px solid #c3e6cb; padding: 15px; border-radius: 8px; color: #155724; font-weight: bold; }
    .status-ng { background-color: #fff5f5; border: 1px solid #f5c6cb; padding: 15px; border-radius: 8px; color: #721c24; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 성적서 기반 위치도 통합 분석 시스템")

# --- 2. 템플릿 제작 및 다운로드 기능 ---
def get_position_template():
    # 성적서 이미지의 데이터 구조를 그대로 템플릿화
    points = ["E", "F", "G", "H", "I", "J", "K", "L"]
    template_df = pd.DataFrame({
        "Point": points,
        "Base_Tol": [0.30] * 8,       # 파란색 원 (기본공차)
        "True_X": [-55.70, -35.80, -14.80, 5.10, -45.50, -5.10, -55.70, 5.10], # 이론치 X
        "True_Y": [-38.80, -38.80, -38.80, -38.80, -54.70, -54.70, -70.30, -70.30], # 이론치 Y
        "Measured_X": [0.0] * 8,      # 실제 측정 X (직접 입력)
        "Measured_Y": [0.0] * 8,      # 실제 측정 Y (직접 입력)
        "Hole_Size": [0.50] * 8       # 실제 구멍 지름 (MMC 보너스 계산용)
    })
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        template_df.to_excel(writer, index=False, sheet_name='Input_Data')
    return output.getvalue()

# --- 3. 상단 대쉬보드 (파일 업로드 및 템플릿) ---
with st.expander("📂 데이터 입력 및 템플릿 다운로드", expanded=True):
    col_dl, col_ul = st.columns([1, 2])
    
    with col_dl:
        st.write("1. 먼저 양식을 다운로드하세요.")
        st.download_button(
            label="📄 위치도 입력 템플릿 받기",
            data=get_position_template(),
            file_name="Position_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        mmc_ref = st.number_input("MMC 기준 치수 (최소지름)", value=0.500, format="%.3f")

    with col_ul:
        st.write("2. 치수를 기입한 파일을 업로드하세요.")
        uploaded_file = st.file_uploader("파일 업로드 (XLSX)", type=["xlsx"])

# 데이터 처리
if uploaded_file:
    df = pd.read_excel(uploaded_file)
else:
    # 파일이 없을 때는 기본 샘플 데이터 표시
    points = ["E", "F", "G", "H", "I", "J", "K", "L"]
    sample_data = {
        "Point": points,
        "Base_Tol": [0.30] * 8,
        "True_X": [-55.70, -35.80, -14.80, 5.10, -45.50, -5.10, -55.70, 5.10],
        "True_Y": [-38.80, -38.80, -38.80, -38.80, -54.70, -54.70, -70.30, -70.30],
        "Measured_X": [-55.712, -35.795, -14.805, 5.102, -45.520, -5.095, -55.731, 5.115],
        "Measured_Y": [-38.815, -38.802, -38.795, -38.810, -54.712, -54.690, -70.315, -70.305],
        "Hole_Size": [0.556, 0.524, 0.532, 0.550, 0.510, 0.505, 0.560, 0.545]
    }
    df = pd.DataFrame(sample_data)

# --- 4. 계산 로직 ---
df['Dev_X'] = df['Measured_X'] - df['True_X']
df['Dev_Y'] = df['Measured_Y'] - df['True_Y']
df['Actual_Pos'] = 2 * np.sqrt(df['Dev_X']**2 + df['Dev_Y']**2)
df['Bonus'] = (df['Hole_Size'] - mmc_ref).clip(lower=0)
df['Final_Tol'] = df['Base_Tol'] + df['Bonus']
df['Status'] = np.where(df['Actual_Pos'] <= df['Final_Tol'], "OK", "NG")
df['Usage'] = (df['Actual_Pos'] / df['Final_Tol']) * 100

# --- 5. 시각화 (손그림 디자인) ---
st.markdown('<div class="stBox">', unsafe_allow_html=True)
st.subheader("🌐 통합 위치 편차 분포 (과녁 차트)")

fig = go.Figure()

# 중심 축
fig.add_vline(x=0, line_width=1.5, line_color="black")
fig.add_hline(y=0, line_width=1.5, line_color="black")

# 손그림 요소 구현
# 1. 파란색 원 (기본 공차 ø0.3)
fig.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, 
             line=dict(color="blue", width=2))

# 2. 보라색 영역 (MMC 적용 최종 한계선)
max_tol = df['Final_Tol'].max()
fig.add_shape(type="circle", x0=-max_tol/2, y0=-max_tol/2, x1=max_tol/2, y1=max_tol/2, 
             line=dict(color="purple", width=2), fillcolor="rgba(148, 103, 189, 0.1)")

# 3. 빨간색 원 (경고 라인)
fig.add_shape(type="circle", x0=-0.25, y0=-0.25, x1=0.25, y1=0.25, 
             line=dict(color="red", width=1, dash="dot"))

# 포인트 데이터
for _, row in df.iterrows():
    p_color = '#10b981' if row['Status'] == "OK" else '#ef4444'
    fig.add_trace(go.Scatter(
        x=[row['Dev_X']], y=[row['Dev_Y']],
        name=row['Point'], mode='markers+text',
        text=[row['Point']], textposition="top center",
        marker=dict(size=12, color=p_color, line=dict(width=1, color='white'))
    ))

fig.update_layout(
    xaxis=dict(range=[-0.3, 0.3], title="X 편차"),
    yaxis=dict(range=[-0.3, 0.3], title="Y 편차", scaleanchor="x", scaleratio=1),
    height=700, template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 6. 상세 테이블 ---
st.subheader("📋 분석 상세 데이터")
st.dataframe(df[['Point', 'Actual_Pos', 'Final_Tol', 'Status', 'Usage']].style.format({'Usage': '{:.1f}%'}))
