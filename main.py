import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from io import BytesIO

def init_app():
    st.set_page_config(page_title="덕인 성적서 마스터 v16.0", layout="wide")
    st.markdown("<style>.stButton>button{background-color:#ef4444!important;color:white!important;font-weight:bold;height:3em;width:100%}</style>", unsafe_allow_html=True)

# [V16 핵심 로직] 줄바꿈/탭 무관, 항목명-숫자 추출기
def parse_dukin_v16(text, sample_count):
    processed = []
    # 1. 항목명(A~L)이 나타나는 위치를 모두 찾음
    # 뒤에 탭이나 공백이 오는 한 글자 대문자 탐색
    item_indices = [(m.start(), m.group().strip()) for m in re.finditer(r'(?:\s|^|\t)([A-L])(?:\s|\t|$)', text)]
    
    for idx in range(len(item_indices)):
        start_pos, name = item_indices[idx]
        # 현재 항목부터 다음 항목 전까지의 텍스트 추출
        end_pos = item_indices[idx+1][0] if idx + 1 < len(item_indices) else len(text)
        chunk = text[start_pos:end_pos]
        
        # 해당 구역에서 모든 숫자 추출
        nums = re.findall(r'[-+]?\d*\.\d+|\d+', chunk)
        nums = [float(n) for n in nums]
        
        step = 1 + sample_count # 도면치수 1개 + 샘플들
        
        # 숫자가 부족하면 무시, 충분하면 데이터 생성
        if len(nums) >= step * 2:
            try:
                # 3행 구조(P, X, Y)인지 2행 구조(X, Y)인지 판단
                if len(nums) >= step * 3:
                    p_off, x_off, y_off = 0, step, step * 2
                else:
                    p_off, x_off, y_off = -1, 0, step
                
                for s in range(sample_count):
                    processed.append({
                        "항목": f"{name}_S{s+1}",
                        "도면_X": nums[x_off], "도면_Y": nums[y_off],
                        "측정_X": nums[x_off + 1 + s], "측정_Y": nums[y_off + 1 + s],
                        "실측지름": nums[p_off + 1 + s] if p_off != -1 else 0.0
                    })
            except: continue
    return processed

def main():
    init_app()
    st.title("🚀 덕인 위치도 통합 분석 v16.0")
    
    sc = st.number_input("🔢 샘플(캐비티) 수", min_value=1, value=4)
    raw_input = st.text_area("성적서 텍스트를 여기에 붙여넣으세요", height=300)
    
    if st.button("🚀 데이터 분석 및 표 생성"):
        if raw_input:
            res = parse_dukin_v16(raw_input, sc)
            if res:
                df = pd.DataFrame(res)
                # 위치도 계산
                df['위치도'] = (2 * np.sqrt((df['측정_X'] - df['도면_X'])**2 + (df['측정_Y'] - df['도면_Y'])**2)).round(4)
                st.session_state.df_v16 = df
                st.success(f"✅ {len(res)}개 데이터 분석 성공!")
                st.dataframe(df, use_container_width=True)
            else:
                st.error("❌ 데이터를 읽지 못했습니다. 항목명(A, B...)이 있는지 확인해주세요.")

    if 'df_v16' in st.session_state:
        st.divider()
        df = st.session_state.df_v16
        c1, c2 = st.columns(2)
        mmc = c1.number_input("📏 MMC 기준", value=0.350)
        tol = c2.number_input("📐 기본 공차", value=0.350)
        
        if st.button("🔍 최종 판정 실행"):
            df['보너스'] = (df['실측지름'] - mmc).clip(lower=0).round(4)
            df['최종공차'] = (tol + df['보너스']).round(4)
            df['판정'] = np.where(df['위치도'] <= df['최종공차'], "OK", "NG")
            st.dataframe(df.style.apply(lambda x: ["background-color:#ffcccc" if v=="NG" else "" for v in x], axis=1), use_container_width=True)

if __name__ == "__main__":
    main()
