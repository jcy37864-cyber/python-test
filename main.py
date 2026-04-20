import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="위치도 분석 & 엑셀 보고서", layout="wide")

st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .summary-box { background-color: #f8fafc; padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; margin-top: 30px; }
    .status-ok { color: #16a34a; font-weight: bold; font-size: 1.2rem; }
    .status-ng { color: #dc2626; font-weight: bold; font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 위치도 정밀 분석 및 엑셀 보고서 시스템")

# --- 2. 함수 정의 영역 (에러 방지를 위해 상단 배치) ---
def get_korean_template():
    template_df = pd.DataFrame({
        "측정포인트": ["E", "F", "G", "H", "I", "J", "K", "L"],
        "기본공차": [0.30] * 8,
        "도면치수_X": [-55.70, -35.80, -14.80, 5.10, -45.50, -5.10, -55.70, 5.10],
        "도면치수_Y": [-38.80, -38.80, -38.80, -38.80, -54.70, -54.70, -70.30, -70.30],
        "측정치_X": [0.0] * 8,
        "측정치_Y": [0.0] * 8,
        "실측지름_MMC용": [0.50] * 8
    })
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        template_df.to_excel(writer, index=False, sheet_name='위치도데이터')
    return output.getvalue()

def create_excel_report(dataframe, plotly_fig):
    output = BytesIO()
    try:
        # kaleido가 설치되어 있어야 동작함
        img_bytes = plotly_fig.to_image(format="png", width=600, height=600)
    except Exception as e:
        st.error("그래프 이미지 변환 중 오류가 발생했습니다. (kaleido 라이브러리 확인 필요)")
        return None
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        dataframe.to_excel(writer, sheet_name='분석데이터', index=False)
        workbook = writer.book
        worksheet = writer.sheets['분석데이터']
        
        # 헤더 및 NG 스타일
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
        ng_fmt = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        
        for col_num, value in enumerate(dataframe.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, 15)
            
        # 그래프 이미지 삽입 (I2 셀 위치)
        image_data = BytesIO(img_bytes)
        worksheet.insert_image('I2', 'graph.png', {'image_data': image_data, 'x_scale': 0.7, 'y_scale': 0.7})
        
    return output.getvalue()

# --- 3. 데이터 입력 및 처리 ---
with st.expander("📂 엑셀 템플릿 및 업로드", expanded=True):
    col_dl, col_ul = st.columns([1, 2])
    with col_dl:
        st.download_button("📥 한글 양식 다운로드", data=get_korean_template(), file_name="위치도_양식.xlsx", use_container_width=True)
        mmc_min = st.number_input("MMC 기준값", value=0.500, format="%.3f")

    with col_ul:
        uploaded_file = st.file_uploader("측정값을 입력한 엑셀 업로드", type=["xlsx"])

# 데이터 로딩 (샘플 또는 업로드)
if uploaded_file:
    df = pd.read_excel(uploaded_file)
else:
    df = pd.DataFrame({
        "측정포인트": ["E", "F", "G", "H", "I", "J", "K", "L"],
        "기본공차": [0.30] * 8,
        "도면치수_X": [-55.70, -35.80, -14.80, 5.10, -45.50, -5.10, -55.70, 5.10],
        "도면치수_Y": [-38.80, -38.80, -38.80, -38.80, -54.70, -54.70, -70.30, -70.30],
        "측정치_X": [-55.712, -35.795, -14.805, 5.102, -45.520, -5.095, -55.731, 5.115],
        "측정치_Y": [-38.815, -38.802, -38.795, -38.810, -54.712, -54.690, -70.315, -70.305],
        "실측지름_MMC용": [0.556, 0.524, 0.532, 0.550, 0.510, 0.505, 0.560, 0.545]
    })

# 계산 수행
df['X편차'] = df['측정치_X'] - df['도면치수_X']
df['Y편차'] = df['측정치_Y'] - df['도면치수_Y']
df['위치도결과'] = 2 * np.sqrt(df['X편차']**2 + df['Y편차']**2)
df['보너스공차'] = (df['실측지름_MMC용'] - mmc_min).clip(lower=0)
df['최종허용공차'] = df['기본공차'] + df['보너스공차']
df['판정'] = np.where(df['위치도결과'] <= df['최종허용공차'], "OK", "NG")
df['소진율'] = (df['위치도결과'] / df['최종허용공차']) * 100

# --- 4. 그래프 생성 (fig 변수 확실히 생성) ---
fig = go.Figure()
fig.add_vline(x=0, line_width=1, line_color="black")
fig.add_hline(y=0, line_width=1, line_color="black")
fig.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, line=dict(color="blue", width=2))
max_tol
