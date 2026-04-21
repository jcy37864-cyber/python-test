import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO

# 1. 초기화 및 디자인
st.set_page_config(page_title="덕인 성적서 v18.0", layout="wide")
st.markdown("<style>.stButton>button{background-color:#ef4444!important;color:white!important;font-weight:bold;height:3.5em;width:100%}</style>", unsafe_allow_html=True)

def parse_dukin_v18(text, sample_count):
    # [핵심] 텍스트에서 숫자, 소수점, 마이너스 기호만 남기고 나머지는 공백으로 치환
    # Ø2.3 같은 특수문자나 한글/영문을 모두 제거하여 숫자 리스트만 뽑습니다.
    nums = re.findall(r'[-+]?\d*\.\d+|\d+', text)
    nums = [float(n) for n in nums]
    
    processed = []
    # 한 줄의 데이터 길이 = 도면값(1) + 샘플수(sample_count)
    line_len = 1 + sample_count 
    # 한 세트(P, X, Y)의 전체 숫자 개수
    set_len = line_len * 3 
    
    # 전체 숫자 리스트를 세트 단위로 쪼개기
    total_points = len(nums) // set_len
    
    for i in range(total_points):
        base = i * set_len
        # 항목명은 순서대로 A, B, C... 부여
        label = chr(65 + i) if i < 26 else f"P{i+1}"
        
        # 숫자 리스트에서 P, X, Y 뭉치를 순서대로 잘라냄
        p_row = nums[base : base + line_len]
        x_row = nums[base + line_len : base + (line_len * 2)]
        y_row = nums[base + (line_len * 2) : base + (line_len * 3)]
        
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

# 2. 메인 UI
st.title("🎯 덕인 위치도 무적 엔진 v18.0")
st.warning("항목명 인식 대신 '숫자 나열 순서'를 강제로 매칭하는 로직입니다.")

with st.container():
    sc = st.number_input("🔢 샘플(캐비티) 수 (S1~S4면 '4' 입력)", min_value=1, value=4)
    raw_input = st.text_area("성적서 데이터를 전체 복사해서 붙여넣으세요", height=300)
    
    if st.button("🚀 데이터 분석 및 표 생성") and raw_input:
        res = parse_dukin_v18(raw_input, sc)
        if res:
            df = pd.DataFrame(res)
            # 위치도 수식: 2 * sqrt(dx^2 + dy^2)
            df['위치도'] = (2 * np.sqrt((df['측정_X'] - df['도면_X'])**2 + (df['측정_Y'] - df['도면_Y'])**2)).round(4)
            st.session_state.v18_data = df
            st.success(f"✅ 성공! {len(res)}개의 데이터를 읽어왔습니다.")
            st.dataframe(df, use_container_width=True)
        else:
            st.error("데이터에서 숫자 패턴을 읽지 못했습니다. 샘플 수 설정을 확인해 주세요.")

# 3. 계산 및 판정
if 'v18_data' in st.session_state:
    st.divider()
    df = st.session_state.v18_data
    c1, c2 = st.columns(2)
    mmc_val = c1.number_input("📏 MMC 기준", value=0.350, format="%.3f")
    tol_val = c2.number_input("📐 기본 공차", value=0.350, format="%.3f")
    
    if st.button("🔍 최종 판정 및 저장"):
        df['보너스'] = (df['실측지름'] - mmc_val).clip(lower=0).round(4)
        df['최종공차'] = (tol_val + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")
        st.dataframe(df.style.apply(lambda x: ["background-color: #ffcccc" if v == "❌ NG" else "" for v in x], axis=1), use_container_width=True)
        
        # 엑셀 다운로드
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 분석 결과 엑셀 저장", output.getvalue(), "Result_v18.xlsx")
