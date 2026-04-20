import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="정밀 위치도 분석 시스템 v2.0", layout="wide")

st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stHeader { font-size: 1.5rem; font-weight: bold; margin-bottom: 10px; color: #1e293b; }
    .status-ok { background-color: #f0fff4; border: 1px solid #c3e6cb; padding: 10px; border-radius: 8px; color: #155724; font-weight: bold; }
    .status-ng { background-color: #fff5f5; border: 1px solid #f5c6cb; padding: 10px; border-radius: 8px; color: #721c24; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 멀티 캐비티 위치도 통합 분석 시스템 v2.0")

# --- [구조화] 데이터 입력 섹션 (나중에 이 부분만 메뉴별로 분기 가능) ---
with st.expander("📂 데이터 업로드 및 템플릿", expanded=True):
    col_file, col_temp = st.columns([3, 1])
    with col_file:
        # 성적서 양식에 맞춘 데이터 구조
        st.subheader("📝 성적서 기반 위치도 데이터 입력")
        
        # 샘플 데이터 (성적서 이미지 기반 패턴 인식 로직을 거친 결과 테이블)
        points = ["E", "F", "G", "H", "I", "J", "K", "L"]
        data = {
            "Point": points,
            "Base_Tol": [0.30] * 8, # 파란색 원의 지름
            "True_X": [-55.70, -35.80, -14.80, 5.10, -45.50, -5.10, -55.70, 5.10],
            "True_Y": [-38.80, -38.80, -38.80, -38.80, -54.70, -54.70, -70.30, -70.30],
            "Measured_X": [-55.735, -35.802, -14.800, 5.105, -45.520, -5.095, -55.731, 5.115],
            "Measured_Y": [-38.815, -38.801, -38.799, -38.810, -54.712, -54.690, -70.315, -70.305],
            "Hole_Size": [0.556, 0.524, 0.532, 0.550, 0.510, 0.505, 0.560, 0.545]  # MMC 계산용 실제 지름
        }
        df_edit = pd.data_editor(pd.DataFrame(data), num_rows="dynamic", use_container_width=True)

    with col_temp:
        st.markdown("**공통 설정**")
        mmc_size = st.number_input("MMC 기준 치수 (ø)", value=0.500, format="%.3f")

# 데이터 로딩 실패 시 방지 로직
if df_edit.empty:
    st.warning("데이터를 입력해 주세요.")
    st.stop()

# --- 2. 위치도 및 MMC 계산 로직 ---
df_edit['Dev_X'] = df_edit['Measured_X'] - df_edit['True_X']
df_edit['Dev_Y'] = df_edit['Measured_Y'] - df_edit['True_Y']
df_edit['Actual_Position'] = 2 * np.sqrt(df_edit['Dev_X']**2 + df_edit['Dev_Y']**2)

# MMC 보너스 계산 (지름 기준으로 clipLower=0)
df_edit['Bonus'] = (df_edit['Hole_Size'] - mmc_size).clip(lower=0)
df_edit['Final_Tolerance'] = df_edit['Base_Tol'] + df_edit['Bonus']
df_edit['Usage_Rate'] = (df_edit['Actual_Position'] / df_edit['Final_Tolerance']) * 100
df_edit['Status'] = np.where(df_edit['Actual_Position'] <= df_edit['Final_Tolerance'], "OK", "NG")

# --- 3. [복구] 통합 과녁 그래프 (손그림 디자인 구현) ---
st.markdown('<div class="stBox">', unsafe_allow_html=True)
st.subheader("🌐 전 캐비티 통합 위치 편차 분포 (손그림 디자인)")

fig_target = go.Figure()

# 중심 십자선 (X, Y축)
fig_target.add_shape(type="line", x0=-0.3, y0=0, x1=0.3, y1=0, line=dict(color="black", width=2))
fig_total.add_shape(type="line", x0=0, y0=-0.3, x1=0, y1=0.3, line=dict(color="black", width=2))

# 1. 파란색 원 (기준 공차 ø)
fig_target.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, 
                     line=dict(color="blue", width=2, dash="dash"), name="Base Tol (ø0.3)")

# 2. 보라색 영역 및 테두리 (MMC 공차 øø)
# 가장 큰 MMC 공차 øø를 기준으로 보라색 영역을 표현
max_bonus = df_edit['Bonus'].max()
max_final_tol = df_edit['Final_Tolerance'].max()
fig_target.add_shape(type="circle", x0=-max_final_tol/2, y0=-max_final_tol/2, x1=max_final_tol/2, y1=max_final_tol/2, 
                     line=dict(color="purple", width=3), fillcolor="rgba(148, 103, 189, 0.1)", name="Max MMC Tol")

# 3. 빨간색 원 (NG 경고 øø)
# 최종 합격선 øø를 벗어나면 빨간색으로 표시
fig_target.add_shape(type="circle", x0=-0.3, y0=-0.3, x1=0.3, y1=0.3, 
                     line=dict(color="red", width=2, dash="dash"), name="NG Line")

# 포인트 데이터 찍기 (A~L)
for i, row in df_edit.iterrows():
    point_color = 'rgba(0,0,0,0)' if row['Status'] == "NG" else '#10b981'
    fig_target.add_trace(go.Scatter(x=[row['Dev_X']], y=[row['Dev_Y']], name=f"{row['Point']}",
                                     mode='markers+text',
                                     text=[row['Point']], textposition="top center",
                                     marker=dict(size=10, color=point_color, symbol='circle',
                                                 line=dict(width=2, color='red' if row['Status'] == "NG" else 'green'))
                                     hovertemplate=f"Point: {row['Point']}<br>XDev: %{x}<br>YDev: %{y}<extra></extra>"
                                    ))

fig_target.update_layout(xaxis_title="X 편차", yaxis_title="Y 편차", height=600, width=600, plot_bgcolor='white',
                        hovermode="closest", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig_target, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 4. 포인트별 소진율 바 차트 ---
st.markdown('<div class="stBox">', unsafe_allow_html=True)
st.subheader("📊 포인트별 공차 소진율 (%)")
fig_bar = px.bar(df_edit, x='Point', y='Usage_Rate', color='Status',
                 color_discrete_map={'OK': '#10b981', 'NG': '#e11d48'},
                 range_y=[0, 110])
fig_bar.add_hline(y=100, line_dash="dash", line_color="red")
fig_bar.update_layout(yaxis_title="Usage (%)", xaxis_title="Point")
st.plotly_chart(fig_bar, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 5. 상세 분석 결과 및 다운로드 ---
st.markdown('<div class="stBox">', unsafe_allow_html=True)
st.subheader("📝 상세 분석 결과 및 다운로드")

# NG 포인트 리스트업 (텍스트 리포트 복구)
ng_points = df_edit[df_edit['Status'] == "NG"]['Point'].tolist()
if not ng_points:
    st.markdown(f'<div class="status-ok">✅ 모든 캐비티 ({len(df_edit)}EA) 규격 내 만족</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="status-ng">🚨 부적합 포인트 발견: {ng_points} 확인 요망</div>', unsafe_allow_html=True)

# 상세 데이터 테이블
st.dataframe(df_edit[['Point', 'Actual_Position', 'Final_Tolerance', 'Status', 'Usage_Rate']]
             .style.format({
                 'Actual_Position': '{:.4f}',
                 'Final_Tolerance': '{:.4f}',
                 'Usage_Rate': '{:.1f}%'
             }).apply(lambda x: ['background-color: #ffcccc' if v == "NG" else '' for v in x], subset=['Status']))

# [신규] 결과 엑셀 다운로드 버튼
output_result = BytesIO()
with pd.ExcelWriter(output_result, engine='xlsxwriter') as writer:
    df_edit.to_excel(writer, index=False, sheet_name='Analysis_Result')
st.download_button(
    label="📂 위치도 분석 결과 엑셀 파일 다운로드",
    data=output_res.getvalue(),
    file_name="Quality_Report_Position.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
st.markdown('</div>', unsafe_allow_html=True)
