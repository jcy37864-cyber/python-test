import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO

# --- 1. 라이브러리 및 페이지 설정 (최상단에 위치해야 함) ---
st.set_page_config(page_title="정밀 위치도 분석 시스템 v2.2", layout="wide")

# CSS 디자인 정의
st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .status-ok { background-color: #f0fff4; border: 1px solid #c3e6cb; padding: 15px; border-radius: 8px; color: #155724; font-weight: bold; }
    .status-ng { background-color: #fff5f5; border: 1px solid #f5c6cb; padding: 15px; border-radius: 8px; color: #721c24; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 위치도(Position) 및 MMC 통합 분석 시스템")

# --- 2. 데이터 입력 섹션 ---
with st.expander("📂 데이터 입력 및 설정", expanded=True):
    col_input, col_cfg = st.columns([3, 1])
    
    with col_cfg:
        mmc_ref = st.number_input("MMC 기준 치수 (ø)", value=0.500, format="%.3f", help="보너스 공차 계산을 위한 최소 구멍 크기")
        
    with col_input:
        # 성적서 패턴 기반 샘플 데이터
        raw_data = {
            "Point": ["E", "F", "G", "H", "I", "J", "K", "L"],
            "Base_Tol": [0.30] * 8,
            "True_X": [-55.70, -35.80, -14.80, 5.10, -45.50, -5.10, -55.70, 5.10],
            "True_Y": [-38.80, -38.80, -38.80, -38.80, -54.70, -54.70, -70.30, -70.30],
            "Measured_X": [-55.735, -35.802, -14.800, 5.105, -45.520, -5.095, -55.731, 5.115],
            "Measured_Y": [-38.815, -38.801, -38.799, -38.810, -54.712, -54.690, -70.315, -70.305],
            "Hole_Size": [0.556, 0.524, 0.532, 0.550, 0.510, 0.505, 0.560, 0.545]
        }
        df = st.data_editor(pd.DataFrame(raw_data), num_rows="dynamic", use_container_width=True)

# --- 3. 계산 로직 ---
if not df.empty:
    df['Dev_X'] = df['Measured_X'] - df['True_X']
    df['Dev_Y'] = df['Measured_Y'] - df['True_Y']
    df['Actual_Pos'] = 2 * np.sqrt(df['Dev_X']**2 + df['Dev_Y']**2)
    df['Bonus'] = (df['Hole_Size'] - mmc_ref).clip(lower=0)
    df['Final_Tol'] = df['Base_Tol'] + df['Bonus']
    df['Status'] = np.where(df['Actual_Pos'] <= df['Final_Tol'], "OK", "NG")
    df['Usage'] = (df['Actual_Pos'] / df['Final_Tol']) * 100

    # --- 4. 시각화 (손그림 디자인 구현) ---
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🌐 통합 위치 편차 분포 (과녁 차트)")
    
    fig = go.Figure()

    # 가이드 라인 (X, Y축)
    fig.add_vline(x=0, line_width=1, line_color="#cbd5e1")
    fig.add_hline(y=0, line_width=1, line_color="#cbd5e1")

    # [손그림 반영 1] 파란색 원: 기본 공차 (ø0.3)
    fig.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, 
                 line=dict(color="blue", width=2))

    # [손그림 반영 2] 보라색 영역: MMC 포함 최대 공차
    max_tol = df['Final_Tol'].max()
    fig.add_shape(type="circle", x0=-max_tol/2, y0=-max_tol/2, x1=max_tol/2, y1=max_tol/2, 
                 line=dict(color="purple", width=2), fillcolor="rgba(148, 103, 189, 0.1)")

    # [손그림 반영 3] 빨간색 원: 한계 경고선
    limit_line = max_tol * 0.6
    fig.add_shape(type="circle", x0=-limit_line, y0=-limit_line, x1=limit_line, y1=limit_line, 
                 line=dict(color="red", width=1, dash="dot"))

    # 측정 포인트 플로팅
    for _, row in df.iterrows():
        point_color = '#10b981' if row['Status'] == "OK" else '#ef4444'
        fig.add_trace(go.Scatter(
            x=[row['Dev_X']], y=[row['Dev_Y']],
            name=row['Point'], mode='markers+text',
            text=[row['Point']], textposition="top center",
            marker=dict(size=12, color=point_color, line=dict(width=1, color='white')),
            hovertemplate=f"<b>Point {row['Point']}</b><br>위치도: {row['Actual_Pos']:.4f}<br>상태: {row['Status']}<extra></extra>"
        ))

    fig.update_layout(
        xaxis=dict(range=[-0.3, 0.3], title="X 편차"),
        yaxis=dict(range=[-0.3, 0.3], title="Y 편차", scaleanchor="x", scaleratio=1),
        height=700, template="plotly_white", showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 5. 리포트 및 결과 테이블 ---
    col_table, col_summary = st.columns([2, 1])
    
    with col_summary:
        st.subheader("📝 판정 요약")
        ng_list = df[df['Status'] == "NG"]['Point'].tolist()
        if not ng_list:
            st.markdown('<div class="status-ok">✅ 전 포인트 합격</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-ng">🚨 부적합 발생: {ng_list}</div>', unsafe_allow_html=True)
            
        # 엑셀 다운로드 기능
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 분석 결과 엑셀 저장", output.getvalue(), "Position_Analysis.xlsx", use_container_width=True)

    with col_table:
        st.subheader("📋 분석 상세 데이터")
        st.dataframe(df[['Point', 'Actual_Pos', 'Final_Tol', 'Status', 'Usage']].style.format({'Usage': '{:.1f}%'}))
