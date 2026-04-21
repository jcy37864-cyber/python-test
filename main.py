import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO

# 1. 초기 설정
st.set_page_config(page_title="덕인 성적서 v17.0", layout="wide")
st.markdown("<style>.stButton>button{background-color:#ef4444!important;color:white!important;font-weight:bold;height:3.5em;width:100%}</style>", unsafe_allow_html=True)

def parse_dukin_v17(text, sample_count):
    # 모든 숫자(소수점, 음수 포함)를 추출하여 1차원 리스트로 만듭니다.
    # 이 방식은 텍스트에 어떤 글자가 섞여있든 숫자의 '순서'에만 집중합니다.
    all_nums = re.findall(r'[-+]?\d*\.\d+|\d+', text)
    all_nums = [float(n) for n in all_nums]
    
    processed = []
    step = 1 + sample_count  # 도면1 + 샘플수 (예: 4개면 5)
    
    # 데이터가 3줄(P, X, Y) 단위로 구성되므로, 전체 숫자 개수를 한 세트(3*step)로 나눕니다.
    # 예: 항목 A에 숫자가 15개(5*3) 있다면 정확히 한 항목입니다.
    total_sets = len(all_nums) // (step * 3)
    
    for i in range(total_sets):
        start_idx = i * (step * 3)
        # 항목명은 데이터가 규칙적이라면 A, B, C... 순서로 부여
        label = chr(65 + i) if i < 26 else f"P{i+1}"
        
        # 데이터 분리
        p_row = all_nums[start_idx : start_idx + step]
        x_row = all_nums[start_idx + step : start_idx + (step * 2)]
        y_row = all_nums[start_idx + (step * 2) : start_idx + (step * 3)]
        
        for s in range(sample_count):
            try:
                processed.append({
                    "항목": f"{label}_S{s+1}",
                    "도면_X": x_row[0],
                    "도면_Y": y_row[0],
                    "측정_X": x_row[s+1],
                    "측정_Y": y_row[s+1],
                    "실측지름": p_row[s+1]
                })
            except IndexError:
                continue
    return processed

# 2. 메인 화면
st.title("🎯 덕인 성적서 최종 분석 v17.0")
st.info("항목명 인식 대신 '숫자 나열 패턴'을 분석하는 최신 로직이 적용되었습니다.")

sc = st.number_input("🔢 샘플(캐비티) 수 설정", min_value=1, value=4)
raw_input = st.text_area("성적서 전체를 여기에 붙여넣으세요", height=350)

if st.button("🚀 데이터 분석 및 표 생성") and raw_input:
    res = parse_dukin_v17(raw_input, sc)
    if res:
        df = pd.DataFrame(res)
        # 위치도 계산 공식: 2 * sqrt(dx^2 + dy^2)
        df['위치도'] = (2 * np.sqrt((df['측정_X'] - df['도면_X'])**2 + (df['측정_Y'] - df['도면_Y'])**2)).round(4)
        st.session_state.df_v17 = df
        st.success(f"✅ 분석 완료! {len(res)}개의 샘플 데이터를 찾았습니다.")
        st.dataframe(df, use_container_width=True)
    else:
        st.error("데이터에서 숫자 패턴을 찾지 못했습니다. 샘플 수 설정을 확인해 주세요.")

# 3. 공차 판정 섹션
if 'df_v17' in st.session_state:
    st.divider()
    df = st.session_state.df_v17
    col1, col2 = st.columns(2)
    mmc_ref = col1.number_input("📏 MMC 기준", value=0.350, format="%.3f")
    tol_ref = col2.number_input("📐 기본 공차", value=0.350, format="%.3f")
    
    if st.button("🔍 최종 판정 및 엑셀 준비"):
        df['보너스'] = (df['실측지름'] - mmc_ref).clip(lower=0).round(4)
        df['최종공차'] = (tol_ref + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")
        
        st.dataframe(df.style.apply(lambda x: ["background-color: #ffcccc" if v == "❌ NG" else "" for v in x], axis=1), use_container_width=True)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 분석 결과 엑셀 저장", output.getvalue(), "Dukin_Final_Report.xlsx")
