import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="위치도 분석 시스템 v3.1", layout="wide")

st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .summary-box { background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; margin-top: 30px; }
    .status-ok { color: #16a34a; font-weight: bold; font-size: 1.1rem; }
    .status-ng { color: #dc2626; font-weight: bold; font-size: 1.1rem; }
    /* 표 헤더 강조 */
    thead tr th { background-color: #f1f5f9 !important; color: #1e293b !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 위치도 정밀 분석 시스템")

# --- 2. 초기화 로직 (Session State) ---
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

def reset_app():
    st.session_state.reset_key += 1
    st.rerun()

# --- 3. 함수 정의 ---
def get_template():
    df_temp = pd.DataFrame({
        "측정포인트": ["E", "F", "G", "H", "I", "J", "K", "L"],
        "기본공차": [0.30] * 8,
        "도면치수_X": [-55.70, -35.80, -14.80, 5.10, -45.50, -5.10, -55.70, 5.10],
        "도면치수_Y": [-38.80, -38.80, -38.80, -38.80, -54.70, -54.70, -70.30, -70.30],
        "측정치_X": [0.0] * 8,
        "측정치_Y": [0.0] * 8,
        "실측지름_MMC용": [0.50] * 8
    })
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df_temp.to_excel(writer, index=False, sheet_name='위치도양식')
    return out.getvalue()

def create_excel_report(dataframe, plotly_fig):
    output_excel = BytesIO()
    try:
        img_bytes = plotly_fig.to_image(format="png", width=800, height=800)
    except:
        img_bytes = None
    
    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
        dataframe.to_excel(writer, sheet_name='분석결과', index=False)
        worksheet = writer.sheets['분석결과']
        if img_bytes:
            worksheet.insert_image('I2', 'graph.png', {'image_data': BytesIO(img_bytes), 'x_scale': 0.6, 'y_scale': 0.6})
    return output_excel.getvalue()

# --- 4. 데이터 입력 섹션 ---
with st.expander("📂 데이터 입력 및 설정", expanded=True):
    c_header1, c_header2 = st.columns([5, 1])
    with c_header2:
        if st.button("🔄 데이터 리셋", use_container_width=True):
            reset_app()

    c1, c2 = st.columns([1, 2])
    with c1:
        st.download_button("📥 한글 양식 다운로드", data=get_template(), file_name="위치도_양식.xlsx", use_container_width=True)
        mmc_val = st.number_input("MMC 기준값(최소지름)", value=0.500, format="%.3f")
    with c2:
        file = st.file_uploader("측정 데이터 업로드 (XLSX)", type=["xlsx"], key=f"uploader_{st.session_state.reset_key}")

# 데이터 로딩 로직
if file:
    df = pd.read_excel(file)
else:
    # 성적서 기반 기본 샘플
    df = pd.DataFrame({
        "측정포인트": ["E", "F", "G", "H", "I", "J", "K", "L"],
        "기본공차": [0.30] * 8, "도면치수_X": [-55.7, -35.8, -14.8, 5.1, -45.5, -5.1, -55.7, 5.1],
        "도면치수_Y": [-38.8, -38.8, -38.8, -38.8, -54.7, -54.7, -70.3, -70.3],
        "측정치_X": [-55.715, -35.790, -14.810, 5.105, -45.525, -5.090, -55.740, 5.115],
        "측정치_Y": [-38.820, -38.805, -38.790, -38.815, -54.720, -54.685, -70.320, -70.310],
        "실측지름_MMC용": [0.556, 0.524, 0.532, 0.550, 0.510, 0.505, 0.560, 0.545]
    })

# --- 5. 위치도 계산 ---
df['X편차'] = df['측정치_X'] - df['도면치수_X']
df['Y편차'] = df['측정치_Y'] - df['도면치수_Y']
df['위치도결과'] = 2 * np.sqrt(df['X편차']**2 + df['Y편차']**2)
df['보너스'] = (df['실측지름_MMC용'] - mmc_val).clip(lower=0)
df['최종공차'] = df['기본공차'] + df['보너스']
df['판정'] = np.where(df['위치도결과'] <= df['최종공차'], "OK", "NG")
df['소진율(%)'] = (df['위치도결과'] / df['최종공차']) * 100

# --- 6. 시각화 (강조된 X, Y축 및 시인성 개선) ---
fig = go.Figure()

# [중요] X, Y축 진하게 표시 (0선 강조)
fig.update_xaxes(zeroline=True, zerolinewidth=2.5, zerolinecolor='black', showgrid=True, gridwidth=1, gridcolor='#e2e8f0')
fig.update_yaxes(zeroline=True, zerolinewidth=2.5, zerolinecolor='black', showgrid=True, gridwidth=1, gridcolor='#e2e8f0')

# 공차 영역 그리기
fig.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, 
             line=dict(color="RoyalBlue", width=2, dash="dash"), name="기본공차(ø0.3)")
max_t = df['최종공차'].max()
fig.add_shape(type="circle", x0=-max_t/2, y0=-max_t/2, x1=max_t/2, y1=max_t/2, 
             line=dict(color="MediumPurple", width=3), fillcolor="rgba(147, 112, 219, 0.15)", name="최대공차(MMC)")

# 데이터 포인트 플로팅 (시인성 강화)
for _, row in df.iterrows():
    p_color = '#00c853' if row['판정'] == "OK" else '#ff1744' # 선명한 녹색/빨간색
    fig.add_trace(go.Scatter(
        x=[row['X편차']], y=[row['Y편차']], name=row['측정포인트'],
        mode='markers+text',
        text=[f"<b>{row['측정포인트']}</b>"], # 글자 굵게
        textposition="top center",
        marker=dict(size=14, color=p_color, line=dict(width=2, color='white'), symbol='circle'),
        hovertemplate=f"포인트: {row['측정포인트']}<br>X편차: {row['X편차']:.4f}<br>Y편차: {row['Y편차']:.4f}<br>판정: {row['판정']}<extra></extra>"
    ))

fig.update_layout(
    xaxis=dict(range=[-0.35, 0.35], title="<b>X 편차 (mm)</b>"),
    yaxis=dict(range=[-0.35, 0.35], scaleanchor="x", scaleratio=1, title="<b>Y 편차 (mm)</b>"),
    height=700, margin=dict(l=20, r=20, t=40, b=20),
    template="plotly_white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# --- 7. 화면 메인 출력 ---
st.markdown('<div class="stBox">', unsafe_allow_html=True)
st.subheader("🌐 편차 분포 과녁 차트 (X-Y 강조)")
st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="stBox">', unsafe_allow_html=True)
st.subheader("📋 분석 데이터 상세 정보")
# 데이터 시인성 강화 (NG 강조)
styled_df = df.style.map(lambda x: 'color: #ff1744; font-weight: bold; background-color: #fff1f2' if x == 'NG' else '', subset=['판정'])
st.dataframe(styled_df, use_container_width=True, height=300)
st.markdown('</div>', unsafe_allow_html=True)

# --- 8. 하단 요약 ---
st.markdown('<div class="summary-box">', unsafe_allow_html=True)
st.subheader("📊 품질 분석 요약")
c_res1, c_res2, c_res3 = st.columns(3)
with c_res1:
    st.write(f"**총 검사:** {len(df)} 포인트")
    st.write(f"**합격/불합격:** {len(df[df['판정']=='OK'])} / {len(df[df['판정']=='NG'])}")
with c_res2:
    if len(df[df['판정']=="NG"]) == 0:
        st.markdown('<p class="status-ok">✅ 모든 데이터가 규격 이내입니다.</p>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p class="status-ng">🚨 {len(df[df['판정']=="NG"])}개의 규격 이탈이 있습니다.</p>', unsafe_allow_html=True)
with c_res3:
    report = create_excel_report(df, fig)
    st.download_button("🚀 이미지 포함 엑셀 보고서 저장", data=report, file_name="위치도_종합분석.xlsx", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)
