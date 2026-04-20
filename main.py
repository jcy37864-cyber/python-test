import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 디자인 및 스타일 ---
st.set_page_config(page_title="위치도 분석 시스템 v3.2", layout="wide")
st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
    .guide-blue { color: #2563eb; font-weight: bold; } /* 기본공차 */
    .guide-purple { color: #9333ea; font-weight: bold; } /* MMC보너스 */
    .summary-box { background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 위치도 정밀 분석 시스템")

# --- 2. 초기화 로직 ---
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0
def reset_app():
    st.session_state.reset_key += 1
    st.rerun()

# --- 3. 데이터 입력부 ---
with st.expander("📂 데이터 입력 및 설정", expanded=True):
    header_col1, header_col2 = st.columns([5, 1])
    with header_col2:
        if st.button("🔄 데이터 리셋", use_container_width=True): reset_app()
    
    c1, c2 = st.columns([1, 2])
    with c1:
        # 템플릿 생성 함수 (간소화)
        template_df = pd.DataFrame({
            "측정포인트": ["E", "F", "G", "H", "I", "J", "K", "L"],
            "기본공차": [0.30] * 8, "도면치수_X": [-55.7, -35.8, -14.8, 5.1, -45.5, -5.1, -55.7, 5.1],
            "도면치수_Y": [-38.8, -38.8, -38.8, -38.8, -54.7, -54.7, -70.3, -70.3],
            "측정치_X": [0.0]*8, "측정치_Y": [0.0]*8, "실측지름_MMC용": [0.50]*8
        })
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer: template_df.to_excel(writer, index=False)
        st.download_button("📥 한글 양식 다운로드", data=out.getvalue(), file_name="위치도_양식.xlsx", use_container_width=True)
        mmc_val = st.number_input("MMC 기준값(최소지름)", value=0.500, format="%.3f")
    with c2:
        file = st.file_uploader("데이터 업로드", type=["xlsx"], key=f"up_{st.session_state.reset_key}")

# 데이터 계산
if file: df = pd.read_excel(file)
else:
    df = pd.DataFrame({
        "측정포인트": ["E", "F", "G", "H", "I", "J", "K", "L"],
        "기본공차": [0.30] * 8, "도면치수_X": [-55.7, -35.8, -14.8, 5.1, -45.5, -5.1, -55.7, 5.1],
        "도면치수_Y": [-38.8, -38.8, -38.8, -38.8, -54.7, -54.7, -70.3, -70.3],
        "측정치_X": [-55.715, -35.790, -14.810, 5.105, -45.525, -5.090, -55.740, 5.115],
        "측정치_Y": [-38.820, -38.805, -38.790, -38.815, -54.720, -54.685, -70.320, -70.310],
        "실측지름_MMC용": [0.556, 0.524, 0.532, 0.550, 0.510, 0.505, 0.560, 0.545]
    })

df['X편차'] = df['측정치_X'] - df['도면치수_X']
df['Y편차'] = df['측정치_Y'] - df['도면치수_Y']
df['위치도결과'] = 2 * np.sqrt(df['X편차']**2 + df['Y편차']**2)
df['보너스'] = (df['실측지름_MMC용'] - mmc_val).clip(lower=0)
df['최종공차'] = df['기본공차'] + df['보너스']
df['판정'] = np.where(df['위치도결과'] <= df['최종공차'], "OK", "NG")

# --- 4. 시각화 (범위 의미 명확화) ---
st.markdown("""
    <div class="stBox">
        <h4>💡 과녁 범위 읽는 법</h4>
        <ul>
            <li><span class="guide-blue">🔵 파란 점선 원:</span> <b>기본 공차 영역 (ø0.3)</b> - 보너스 없이 무조건 합격해야 하는 핵심 범위</li>
            <li><span class="guide-purple">🟣 보라색 실선 영역:</span> <b>MMC 보너스 포함 합격선</b> - 구멍이 커짐에 따라 확장된 최종 마지노선</li>
            <li><span style="color:#ef4444; font-weight:bold;">🔴 빨간 점:</span> 규격 이탈(NG) | <span style="color:#10b981; font-weight:bold;">🟢 녹색 점:</span> 합격(OK)</li>
        </ul>
    </div>
""", unsafe_allow_html=True)

fig = go.Figure()

# 축 강조
fig.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black', showgrid=True, gridcolor='#eee')
fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black', showgrid=True, gridcolor='#eee')

# 1. 기본공차 영역 (파란색 점선)
fig.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, 
             line=dict(color="Blue", width=2, dash="dot"))

# 2. 최종 합격 영역 (보라색 채우기)
max_t = df['최종공차'].max()
fig.add_shape(type="circle", x0=-max_t/2, y0=-max_t/2, x1=max_t/2, y1=max_t/2, 
             line=dict(color="Purple", width=2), fillcolor="rgba(147, 112, 219, 0.1)")

# 데이터 포인트
for _, row in df.iterrows():
    p_color = '#10b981' if row['판정'] == "OK" else '#ef4444'
    fig.add_trace(go.Scatter(
        x=[row['X편차']], y=[row['Y편차']], name=row['측정포인트'],
        mode='markers+text', text=[f"<b>{row['측정포인트']}</b>"], textposition="top center",
        marker=dict(size=12, color=p_color, line=dict(width=1, color='white'))
    ))

fig.update_layout(
    xaxis=dict(range=[-0.3, 0.3], title="X 편차"),
    yaxis=dict(range=[-0.3, 0.3], scaleanchor="x", scaleratio=1, title="Y 편차"),
    height=600, template="plotly_white", showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# --- 5. 데이터 표 및 요약 ---
st.subheader("📋 분석 상세 데이터")
st.dataframe(df.style.map(lambda x: 'color:red; font-weight:bold' if x == 'NG' else '', subset=['판정']), use_container_width=True)

st.markdown('<div class="summary-box">', unsafe_allow_html=True)
st.subheader("📊 최종 판정 요약")
res_c1, res_c2 = st.columns(2)
with res_c1:
    st.write(f"**총 검사:** {len(df)} 포인트")
    st.write(f"**합격/불합격:** {len(df[df['판정']=='OK'])} / {len(df[df['판정']=='NG'])}")
with res_c2:
    if len(df[df['판정']=="NG"]) == 0: st.success("✅ 모든 포인트 합격 (PASS)")
    else: st.error(f"🚨 {len(df[df['판정']=='NG'])}개 포인트 규격 이탈 (FAIL)")
st.markdown('</div>', unsafe_allow_html=True)
