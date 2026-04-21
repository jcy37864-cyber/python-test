import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from io import BytesIO

# 1. 스타일 설정
def init_app():
    st.set_page_config(page_title="덕인 성적서 완벽 분석 v13.0", layout="wide")
    st.markdown("""
        <style>
        .stButton > button { background-color: #ef4444 !important; color: white !important; font-weight: bold; height: 3em; width: 100%; }
        .stDataFrame { border: 1px solid #e2e8f0; }
        </style>
    """, unsafe_allow_html=True)

# 2. 핵심 파싱 엔진 (이 부분이 이번 해결의 열쇠입니다)
def parse_dukin_ultra(raw_text, sample_count):
    processed = []
    
    # 텍스트에서 불필요한 따옴표 제거
    raw_text = raw_text.replace('"', '')
    
    # [핵심] 항목명(A~L)을 기준으로 데이터를 쪼갭니다. 
    # 앞뒤에 뭐가 붙어있든 알파벳 한 글자 단독 존재를 찾아냅니다.
    items = re.split(r'\s+([A-L])\s+', " " + raw_text + " ")
    
    # 쪼개진 데이터가 [빈값, 'A', '데이터', 'B', '데이터'...] 형태가 됩니다.
    for i in range(1, len(items), 2):
        name = items[i].strip()
        content = items[i+1]
        
        # 해당 구역에서 숫자(소수점, 마이너스 포함)만 싹 다 뽑습니다.
        nums = re.findall(r'[-+]?\d*\.\d+|\d+', content)
        nums = [float(n) for n in nums]
        
        # 덕인 구조: [도면치수1개 + 샘플치수 n개] 가 한 세트
        # 보통 3세트(지름, X, Y)가 나옵니다.
        step = 1 + sample_count 
        
        if len(nums) >= step * 2: # 최소 X, Y 데이터는 있어야 함
            try:
                # 데이터가 3세트 이상이면 맨 앞 세트는 지름(P)으로 간주
                if len(nums) >= step * 3:
                    p_offset, x_offset, y_offset = 0, step, step * 2
                else:
                    p_offset, x_offset, y_offset = -1, 0, step
                
                for s in range(sample_count):
                    processed.append({
                        "항목": f"{name}_S{s+1}",
                        "도면_X": nums[x_offset],
                        "도면_Y": nums[y_offset],
                        "측정_X": nums[x_offset + 1 + s],
                        "측정_Y": nums[y_offset + 1 + s],
                        "실측지름": nums[p_offset + 1 + s] if p_offset != -1 else 0.0
                    })
            except Exception:
                continue
    return processed

# 3. 메인 앱 실행
def main():
    init_app()
    st.title("🚀 덕인 위치도 정밀 분석 솔루션 v13.0")
    
    tab1, tab2, tab3 = st.tabs(["📥 1. 데이터 입력", "📊 2. 위치도 분석", "📈 3. 결과 리포트"])

    with tab1:
        st.write("성적서 텍스트를 아래에 붙여넣으세요.")
        sc = st.number_input("🔢 샘플(캐비티) 수", min_value=1, value=4)
        raw_input = st.text_area("텍스트 데이터", height=300, placeholder="A 0.123 0.456...")
        
        if st.button("🚀 데이터 분석 시작") and raw_input:
            data_list = parse_dukin_ultra(raw_input, sc)
            if data_list:
                st.session_state.df = pd.DataFrame(data_list)
                st.success(f"✅ 총 {len(data_list)}개 포인트 인식 성공!")
                st.dataframe(st.session_state.df, use_container_width=True)
            else:
                st.error("❌ 데이터를 인식하지 못했습니다. 항목명(A, B...)이 포함되어 있나요?")

    with tab2:
        if 'df' in st.session_state:
            df = st.session_state.df.copy()
            st.write("### 위치도 계산 및 판정")
            c1, c2 = st.columns(2)
            mmc_val = c1.number_input("📏 MMC 기준", value=0.350, format="%.3f")
            tol_val = c2.number_input("📐 기본 공차", value=0.350, format="%.3f")

            if st.button("🔍 결과 산출"):
                # 위치도 공식
                df['위치도'] = (2 * np.sqrt((df['측정_X'] - df['도면_X'])**2 + (df['측정_Y'] - df['도면_Y'])**2)).round(4)
                df['보너스'] = (df['실측지름'] - mmc_val).clip(lower=0).round(4)
                df['최종공차'] = (tol_val + df['보너스']).round(4)
                df['판정'] = np.where(df['위치도'] <= df['최종공차'], "OK", "NG")
                st.session_state.res = df
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("1단계에서 데이터를 먼저 로드해 주세요.")

    with tab3:
        if 'res' in st.session_state:
            res = st.session_state.res
            ok_n = (res['판정'] == "OK").sum()
            st.metric("합격률", f"{(ok_n/len(res))*100:.1f}%", f"{ok_n}/{len(res)}")
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                res.to_excel(writer, index=False)
            st.download_button("📥 엑셀로 저장", output.getvalue(), "Quality_Analysis.xlsx")

if __name__ == "__main__":
    main()
