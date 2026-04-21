import streamlit as st
import pandas as pd
import numpy as np
import re

# 1. 페이지 설정
st.set_page_config(page_title="덕인 성적서 분석기", layout="wide")

# 2. 데이터 분석 함수
def parse_dukin_final(text, sample_count):
    # 숫자만 추출
    nums = re.findall(r'[-+]?\d*\.\d+|\d+', text)
    nums = [float(n) for n in nums]
    
    processed = []
    line_len = 1 + sample_count 
    set_len = line_len * 3 
    
    total_points = len(nums) // set_len
    
    for i in range(total_points):
        base = i * set_len
        label = chr(65 + i) if i < 26 else f"P{i+1}"
        
        try:
            p_row = nums[base : base + line_len]
            x_row = nums[base + line_len : base + (line_len * 2)]
            y_row = nums[base + (line_len * 2) : base + (line_len * 3)]
            
            for s in range(sample_count):
                processed.append({
                    "항목": f"{label}_S{s+1}",
                    "도면_X": x_row[0],
                    "도면_Y": y_row[0],
                    "실측_X": x_row[s+1],
                    "실측_Y": y_row[s+1],
                    "실측지름": p_row[s+1]
                })
        except:
            continue
    return processed

# 3. UI 구성
st.title("🎯 덕인 위치도 분석 시스템 (v20.0)")
st.markdown("---")

# 입력 섹션
with st.sidebar:
    st.header("⚙️ 설정")
    sc = st.number_input("샘플 수 (S1~S4면 4)", min_value=1, value=4)
    mmc_ref = st.number_input("MMC 기준", value=0.350, format="%.3f")
    tol_ref = st.number_input("기본 공차", value=0.350, format="%.3f")

raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=300)

if st.button("🚀 데이터 분석 및 결과 확인"):
    if raw_input:
        res = parse_dukin_final(raw_input, sc)
        if res:
            df = pd.DataFrame(res)
            # 계산 로직
            df['위치도'] = (2 * np.sqrt((df['실측_X'] - df['도면_X'])**2 + (df['실측_Y'] - df['도면_Y'])**2)).round(4)
            df['보너스'] = (df['실측지름'] - mmc_ref).clip(lower=0).round(4)
            df['최종공차'] = (tol_ref + df['보너스']).round(4)
            df['판정'] = np.where(df['위치도'] <= df['최종공차'], "OK", "NG")
            
            # 결과 표시
            st.success(f"✅ 분석 완료: {len(res)}개 포인트")
            st.dataframe(df.style.apply(lambda x: ["background-color: #ffcccc" if v == "NG" else "" for v in x], axis=1), use_container_width=True)
            
            # 다운로드 버튼
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 분석 결과 다운로드 (CSV)", csv, "result.csv", "text/csv")
        else:
            st.error("데이터를 분석할 수 없습니다. 형식을 확인해주세요.")
    else:
        st.warning("데이터를 먼저 입력해주세요.")
