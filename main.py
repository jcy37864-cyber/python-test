import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
import PIL.Image as Image # 이미지 처리를 위해 필요

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="위치도 통합 분석 & 보고서 생성", layout="wide")

# (기존 CSS 설정 생략 - v2.5와 동일)

st.title("🎯 위치도 정밀 분석 및 엑셀 보고서 시스템")

# --- 2. 엑셀 보고서 생성 함수 (이미지 포함) ---
def create_excel_report(dataframe, fig):
    output = BytesIO()
    # 그래프를 이미지로 변환
    img_bytes = fig.to_image(format="png", width=600, height=600)
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # 데이터 시트 작성
        dataframe.to_excel(writer, sheet_name='분석데이터', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['분석데이터']
        
        # 스타일 설정 (헤더/판정)
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
        ng_fmt = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        
        # 엑셀 시트 정돈
        for col_num, value in enumerate(dataframe.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, 15)
            
        # [핵심] 그래프 이미지 삽입
        image_data = BytesIO(img_bytes)
        worksheet.insert_image('I2', 'graph.png', {'image_data': image_data, 'x_scale': 0.8, 'y_scale': 0.8})
        
        # 판정 결과 조건부 서식
        worksheet.conditional_format(1, 10, len(dataframe), 10, {
            'type': 'cell', 'criteria': '==', 'value': '"NG"', 'format': ng_fmt
        })
        
    return output.getvalue()

# --- 3. 데이터 로딩 및 계산 ---
# (v2.5의 데이터 로딩 및 위치도 계산 로직 동일 적용)
# ... [중략: df 계산 로직] ...

# --- 4. 시각화 (그래프 생성) ---
# (v2.5의 Plotly 그래프 생성 로직 동일 적용)
fig = go.Figure()
# ... [중략: fig 설정 로직] ...

# 화면에 그래프 표시
st.plotly_chart(fig, use_container_width=True)

# --- 5. 최종 다운로드 섹션 ---
st.markdown('<div class="summary-box">', unsafe_allow_html=True)
st.subheader("📁 분석 결과 내보내기")
col1, col2 = st.columns(2)

with col1:
    st.write("모든 데이터와 과녁 차트 이미지가 포함된 엑셀 보고서를 생성합니다.")
    report_data = create_excel_report(df, fig)
    st.download_button(
        label="🚀 이미지 포함 엑셀 보고서 다운로드",
        data=report_data,
        file_name="위치도_종합분석_보고서.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col2:
    st.write("차트 이미지만 따로 저장하고 싶을 때 사용하세요.")
    img_download = fig.to_image(format="png")
    st.download_button(
        label="🖼️ 과녁 차트(PNG)만 저장",
        data=img_download,
        file_name="위치도_차트.png",
        mime="image/png",
        use_container_width=True
    )
st.markdown('</div>', unsafe_allow_html=True)
