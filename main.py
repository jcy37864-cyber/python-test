import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="위치도 분석 시스템 v2.8", layout="wide")

st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .summary-box { background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; margin-top: 30px; }
    .status-ok { color: #16a34a; font-weight: bold; font-size: 1.2rem; }
    .status-ng { color: #dc2626; font-weight: bold; font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 위치도 정밀 분석 및 보고서 자동화")

# --- 2. 함수 정의 (이미지 포함 엑셀 생성) ---
def get_korean_template():
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
        # Kaleido 패키지가 있어야 이미지 변환 가능
        img_bytes = plotly_fig.to_image(format="png", width=600, height=600)
    except:
        img_bytes = None
    
    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
        dataframe.to_excel(writer, sheet_name='분석결과', index=False)
        workbook = writer.book
        worksheet = writer.sheets['분석결과']
        
        # 스타일 및 이미지 삽입
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
        for col_num, value in enumerate(dataframe.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, 15)
            
        if img_bytes:
            image_data = BytesIO(img_bytes)
            worksheet.insert_image('I2', 'graph.png', {'image_data': image_data, 'x_scale': 0.7, 'y_scale': 0.7})
            
    return output_excel.getvalue()

# --- 3. 데이터 입력부 ---
with st.expander("📂 템플릿 및 파일 업로드", expanded=True):
    c1, c2 = st.columns([1, 2])
    with c1:
        st.download_button("📥 한글 양식 다운로드", data=get_korean_template(), file_name="위치도_양식.xlsx")
        mmc_val = st.number_input("MMC 기준값(최소지름)", value=0.500, format="%.3f")
    with c2:
        file = st.file_uploader("엑셀 파일 업로드", type=["xlsx"])

# 데이터 로딩
if file:
    df = pd.read_excel(file)
else:
    # 샘플 데이터
    df = pd.DataFrame({
        "측정포인트": ["E", "F", "G", "H", "I", "J", "K", "L"],
        "기본공차": [0.30] * 8,
        "도면치수_X": [-55.70, -35.80, -14.80, 5.10, -45.50, -5.10, -55.70, 5.10],
        "도면치수_Y": [-38.80, -38.80, -38.80, -38.80, -54.70, -54.70, -70.30, -70.30],
        "측정치_X": [-55.712, -35.795, -14.805, 5.102, -45.520, -5.095, -55.731, 5.115],
        "측정치_Y": [-38.815, -38.802, -38.795, -38.810, -54.712, -54.690, -70.315, -70.305],
        "실측지름_MMC용": [0.556, 0.524, 0.532, 0.550, 0.510, 0.505, 0.560, 0.545]
    })

# --- 4. 계산 및 그래프 생성 ---
df['X편차'] = df['측정치_X'] - df['도면치수_X']
df['Y편차'] = df['측정치_Y'] - df['도면치수_Y']
df['위치도결과'] = 2 * np.sqrt(df['X편차']**2 + df['Y편차']**2)
df['보너스'] = (df['실측지름_MMC용'] - mmc_val).clip(lower=0)
df['최종공차'] = df['기본공차'] + df['보너스']
df['판정'] = np.where(df['위치도결과'] <= df['최종공차'], "OK", "NG")
df['소진율'] = (df['위치도결과'] / df['최종공차']) * 100

fig = go.Figure()
# 손그림 디자인 (파란색/보라색)
fig.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, line=dict(color="blue", width=2))
max_t = df['최종공차'].max()
fig.add_shape(type="circle", x0=-max_t/2, y0=-max_t/2, x1=max_t/2, y1=max_t/2, 
             line=dict(color="purple", width=2), fillcolor="rgba(148, 103, 189, 0.1)")

for _, row in df.iterrows():
    color = '#10b981' if row['판정'] == "OK" else '#ef4444'
    fig.add_trace(go.Scatter(x=[row['X편차']], y=[row['Y편차']], name=row['측정포인트'],
                             mode='markers+text', text=[row['측정포인트']], textposition="top center",
                             marker=dict(size=12, color=color, line=dict(width=1, color='white'))))

fig.update_layout(xaxis=dict(range=[-0.3, 0.3]), yaxis=dict(range=[-0.3, 0.3], scaleanchor="x", scaleratio=1),
                  height=600, template="plotly_white")

st.plotly_chart(fig, use_container_width=True)

# --- 5. 요약 및 다운로드 ---
st.markdown('<div class="summary-box">', unsafe_allow_html=True)
st.subheader("📊 최종 분석 보고")
c1, c2, c3 = st.columns(3)

with c1:
    st.write(f"**총 검사:** {len(df)} 건")
    st.write(f"**합격/불합격:** {len(df[df['판정']=='OK'])} / {len(df[df['판정']=='NG'])}")

with c2:
    if len(df[df['판정']=="NG"]) == 0:
        st.markdown('<p class="status-ok">✅ 규격 만족</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="status-ng">🚨 불합격 발생</p>', unsafe_allow_html=True)

with c3:
    # 엑셀 다운로드 버튼 (안전하게 호출)
    rpt = create_excel_report(df, fig)
    st.download_button("🚀 이미지 포함 엑셀 보고서 저장", data=rpt, file_name="위치도_보고서.xlsx", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)
