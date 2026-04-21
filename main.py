import streamlit as st
import pandas as pd
import numpy as np
import re

# 1. 기본 설정 및 에러 방지
st.set_page_config(page_title="덕인 성적서 v19.0", layout="wide")

# 2. 파싱 엔진 (가장 안전한 방식)
def parse_dukin_v19(text, sample_count):
    # 모든 숫자 추출
    nums = re.findall(r'[-+]?\d*\.\d+|\d+', text)
    nums = [float(n) for n in nums]
    
    processed = []
    line_len = 1 + sample_count 
    set_len = line_len * 3 
    
    total_points = len(nums) // set_len
    
    for i in range(total_points):
        base = i * set_len
        label = chr(65 + i) if i < 26 else f"P{i+1}"
        
        # P, X, Y 데이터 슬라이싱
        try:
            p_row = nums[base : base + line_len]
            x_row = nums[base + line_len : base + (line_len * 2)]
            y_row = nums[base + (line_len * 2) : base + (line_len * 3)]
            
            for s in range(sample_count):
                processed.append({
                    "항목": f"{label}_S{s+1}",
                    "도면_X": x_row[0],
                    "도면_Y": y_row[0],
                    "측정_X": x_row[s+1],
                    "측정_Y": y_row[s+1],
                    "실측지름": p_row[s+1]
                })
        except:
            continue
    return processed

# 3. 메인 화면
st.title("🎯 덕인 위치도 분석 (복구 완료 v19.0)")

sc = st.number_input("🔢 샘플 수 (S1~S4면 4 입력)", min_value=1, value=4)
raw_input = st.text_area("성적서를 여기에 붙여넣으세요", height=300)

if st.button("🚀 분석 시작"):
    if raw_input:
        res = parse_dukin_v19(raw_input, sc)
        if res:
            df = pd.DataFrame(res)
            # 위치도 계산
            df['위치도'] = (2 * np.sqrt((df['측정_X'] - df['도면_X'])**2 + (df['측정_Y'] - df['도면_Y'])**2)).round(4)
            st.session_state.final_df = df
            st.success("✅ 데이터 분석 성공!")
            st.dataframe(df, use_container_width=True)
        else:
            st.error("데이터를 읽을 수 없습니다. 샘플 수와 입력 내용을 확인하세요.")

# 4. 결과 출력
if 'final_df' in st.session_state:
    st.divider()
    df = st.session_state.final_df
    c1, c2 = st.columns(2)
    mmc = c1.number_input("📏 MMC 기준", value=0.350)
    tol = c2.number_input("📐 기본 공차", value=0.350)
    
    if st.button("🔍 최종 판정"):
        df['보너스'] = (df['실측지름'] - mmc).clip(lower=0).round(4)
        df['최종공차'] = (tol + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "OK", "NG")
        
        # 판정 결과 출력
        st.dataframe(df, use_container_width=True)
        
        # CSV로 저장 (엑셀보다 에러가 안 남)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 결과 다운로드 (CSV)", csv, "result.csv", "text/csv")
