import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="위치도 분석 시스템 v3.4", layout="wide")
st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
    .guide-blue { color: #2563eb; font-weight: bold; } 
    .guide-purple { color: #9333ea; font-weight: bold; }
    .guide-red { color: #ef4444; font-weight: bold; }
    .summary-box { background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 위치도 정밀 분석 시스템")

# --- 2. 초기화 로직 (Session State) ---
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0
def reset_app():
    st.session_state.reset_key += 1
    st.rerun()

# --- 3. 함수 정의 ---
def get_template():
    # 1번부터 시작하도록 템플릿 생성
    template_df = pd.DataFrame({
        "측정포인트": [i for i in range(1, 9)],
        "기본공차": [0.30] * 8, 
        "도면치수_X": [-55.7, -35.8, -14.8, 5.1, -45.5, -5.1, -55.7, 5.1],
        "도면치수_Y": [-38.8, -38.8, -38.8, -38.8, -54.7, -54.7, -70.3, -70.3],
        "측정치_X": [0.0]*8, "측정치_Y": [0.0]*8, "실측지름_MMC용": [0.50]*8
    })
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        template_df.to_excel(writer, index=False, sheet_name='위치도양식')
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

# --- 4. 데이터 입력 및 설정 ---
with st.expander("📂 데이터 입력 및 설정", expanded=True):
    header_col1, header_col2 = st.columns([5, 1])
    with header_col2:
        if st.button("🔄 데이터 리셋", use_container_width=True): reset_app()
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.download_button("📥 한글 양식 다운로드", data=get_template(), file_name="위치도_양식.xlsx", use_container_width=True)
        mmc_val = st.number_input("MMC 기준값(최소지름)", value=0.500, format="%.3f")
    with c2:
        file = st.file_uploader("데이터 업로드", type=["xlsx"], key=f"up_{st.session_state.reset_key}")

# 데이터 로딩 및 계산
if file:
    df = pd.read_excel(file)
else:
    # 샘플 데이터 (1번부터 시작)
    df = pd.DataFrame({
        "측정포인트": [1, 2, 3, 4, 5, 6, 7, 8],
        "기본공차": [0.30] * 8, 
        "도면치수_X": [-55.7, -35.8, -14.8, 5.1, -45.5, -5.1, -55.7, 5.1],
        "도면치수_Y": [-38.8, -38.8, -38.8, -38.8, -54.7, -54.7, -70.3, -70.3],
        "측정치_X": [-55.715, -35.790, -14.810, 5.105, -45.525, -5.090, -55.740, 5.115],
        "측정치_Y": [-38.820, -38.805, -38.790, -38.815, -54.720, -54.685, -70.320, -70.310],
        "실측지름_MMC용": [0.556, 0.524, 0.532, 0.550, 0.510, 0.505, 0.560, 0.545]
    })

# 계산 로직
df['X편차'] = df['측정치_X'] - df['도면치수_X']
df['Y편차'] = df['측정치_Y'] - df['도면치수_Y']
df['위치도결과'] = 2 * np.sqrt(df['X편차']**2 + df['Y편차']**2)
df['보너스'] = (df['실측지름_MMC용'] - mmc_val).clip(lower=0)
df['최종공차'] = df['기본공차'] + df['보너스']
df['판정'] = np.where(df['위치도결과'] <= df['최종공차'], "OK", "NG")
df['소진율(%)'] = (df['위치도결과'] / df['최종공차']) * 100

# 인덱스를 1부터 표시하기 위해 조정
df.index = np.arange(1, len(df) + 1)

# --- 5. 시각화 가이드 및 그래프 (NG 경계선 추가) ---
st.markdown("""
    <div class="stBox">
        <h4>💡 과녁 범위 읽는 법 (v3.4)</h4>
        <ul>
            <li><span class="guide-blue">🔵 파란 점선 원:</span> <b>기본 공차 영역 (ø0.3)</b> - 보너스 없는 순수 규격 범위</li>
            <li><span class="guide-purple">🟣 보라색 실선 영역:</span> <b>최종 합격선 (MMC)</b> - 보너스가 포함되어 확장된 실제 합격 범위</li>
            <li><span class="guide-red">🔴 빨간 점선 원:</span> <b>규격 이탈 경계선 (NG)</b> - 이 선을 넘으면 불합격입니다.</li>
            <li><span style="color:#ef4444; font-weight:bold;">🔴 빨간색 점:</span> NG 포인트 | <span style="color:#10b981; font-weight:bold;">🟢 녹색 점:</span> OK 포인트</li>
        </ul>
    </div>
""", unsafe_allow_html=True)

fig = go.Figure()
# 축 강조
fig.update_xaxes(zeroline=True, zerolinewidth=2.5, zerolinecolor='black', showgrid=True, gridcolor='#eee')
fig.update_yaxes(zeroline=True, zerolinewidth=2.5, zerolinecolor='black', showgrid=True, gridcolor='#eee')

# 원 그리기
# 1. 기본공차 영역 (파란색 점선)
fig.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, line=dict(color="Blue", width=2, dash="dot"))

# 2. 최종 합격 영역 (보라색 채우기)
max_t = df['최종공차'].max()
fig.add_shape(type="circle", x0=-max_t/2, y0=-max_t/2, x1=max_t/2, y1=max_t/2, 
             line=dict(color="Purple", width=2.5), fillcolor="rgba(147, 112, 219, 0.1)")

# [신규] 3. NG 경계선 영역 (빨간색 점선)
# 최종 합격선(보라색)보다 약간 더 넓게 그려서 "여길 넘으면 불량"임을 시각화
fig.add_shape(type="circle", x0=-(max_t/2 + 0.02), y0=-(max_t/2 + 0.02), x1=(max_t/2 + 0.02), y1=(max_t/2 + 0.02), 
             line=dict(color="Red", width=1.5, dash="dashdot"))

# 포인트 찍기
for _, row in df.iterrows():
    p_color = '#10b981' if row['판정'] == "OK" else '#ef4444'
    fig.add_trace(go.Scatter(
        x=[row['X편차']], y=[row['Y편차']], name=str(row['측정포인트']),
        mode='markers+text', text=[f"<b>{row['측정포인트']}</b>"], textposition="top center",
        marker=dict(size=13, color=p_color, line=dict(width=1.5, color='white'))
    ))

fig.update_layout(xaxis=dict(range=[-0.35, 0.35], title="X 편차"), 
                  yaxis=dict(range=[-0.35, 0.35], scaleanchor="x", scaleratio=1, title="Y 편차"),
                  height=650, template="plotly_white", showlegend=False)

st.plotly_chart(fig, use_container_width=True)

# --- 6. 상세 데이터 표 ---
st.markdown('<div class="stBox">', unsafe_allow_html=True)
st.subheader("📋 분석 상세 데이터 (1번부터 시작)")
styled_df = df.style.map(lambda x: 'color:red; font-weight:bold' if x == 'NG' else '', subset=['판정'])
st.dataframe(styled_df, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 하단 요약 및 보고서 ---
st.markdown('<div class="summary-box">', unsafe_allow_html=True)
st.subheader("📊 품질 분석 요약")
res_c1, res_c2, res_c3 = st.columns(3)
with res_c1:
    st.write(f"**총 검사:** {len(df)} 포인트")
    st.write(f"**합격/불합격:** {len(df[df['판정']=='OK'])} / {len(df[df['판정']=='NG'])}")
with res_c2:
    if len(df[df['판정']=="NG"]) == 0: st.success("✅ 모든 포인트 규격 합격")
    else: st.error(f"🚨 {len(df[df['판정']=='NG'])}개 포인트 불합격 발생")
with res_c3:
    report = create_excel_report(df, fig)
    st.download_button("🚀 이미지 포함 엑셀 보고서 저장", data=report, file_name="위치도_보고서.xlsx", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)
