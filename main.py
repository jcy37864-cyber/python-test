import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from io import BytesIO

# 1. 화면 스타일링
def init_app():
    st.set_page_config(page_title="덕인 성적서 마스터 v15.0", layout="wide")
    st.markdown("""
        <style>
        .main { background-color: #f1f5f9; }
        .stButton > button { 
            background-color: #dc2626 !important; 
            color: white !important; 
            font-weight: bold; 
            height: 4em; 
            border-radius: 10px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        }
        </style>
    """, unsafe_allow_html=True)

# 2. 초유연 파싱 엔진 (패턴 전면 재수정)
def parse_dukin_v15(raw_text, sample_count):
    processed = []
    
    # 1. 텍스트 청소: 따옴표 제거 및 불필요한 공백 정리
    clean_text = raw_text.replace('"', '').replace("'", "")
    
    # 2. 항목명(A~L)을 기준으로 쪼개기 (탭이나 공백에 둘러싸인 한 글자 대문자 찾기)
    # 덕인 데이터 특성상 항목명 앞뒤로 탭(\t)이 많으므로 이를 포함하여 쪼갭니다.
    parts = re.split(r'[\s\t]+([A-L])[\s\t]+', " " + clean_text + " ")
    
    # split 결과 예시: ['', 'A', '숫자데이터들...', 'B', '숫자데이터들...']
    for i in range(1, len(parts), 2):
        name = parts[i].strip()
        content = parts[i+1]
        
        # 해당 항목 구역에서 숫자(소수점, 마이너스 포함)만 순서대로 추출
        nums = re.findall(r'[-+]?\d*\.\d+|\d+', content)
        nums = [float(n) for n in nums]
        
        # 덕인 구조: 보통 한 줄에 [도면값 1개 + 샘플값 n개]
        # X행, Y행이 필수이므로 한 세트(step)는 1 + sample_count 개
        step = 1 + sample_count
        
        if len(nums) >= step * 2: # 최소 X, Y 두 줄 분량의 숫자는 있어야 함
            try:
                # 숫자가 엄청 많으면(3세트 이상) 첫 세트는 지름(P)으로 간주
                if len(nums) >= step * 3:
                    p_off, x_off, y_off = 0, step, step * 2
                else:
                    p_off, x_off, y_off = -1, 0, step # 지름 정보가 없을 때
                
                for s in range(sample_count):
                    processed.append({
                        "항목": f"{name}_S{s+1}",
                        "도면_X": nums[x_offset if (x_offset:=x_off) else 0],
                        "도면_Y": nums[y_offset if (y_offset:=y_off) else 0],
                        "측정_X": nums[x_off + 1 + s],
                        "측정_Y": nums[y_off + 1 + s],
                        "실측지름": nums[p_off + 1 + s] if p_off != -1 else 0.0
                    })
            except Exception:
                continue
                
    return processed

# 3. 메인 앱 레이아웃
def main():
    init_app()
    st.title("🎯 덕인 위치도 분석 솔루션 v15.0")
    
    t1, t2, t3 = st.tabs(["📥 1. 데이터 로드", "📊 2. 결과 분석", "📈 3. 통계 리포트"])

    with t1:
        st.info("성적서 텍스트를 아래 칸에 붙여넣고 [분석 시작]을 눌러주세요.")
        sc = st.number_input("🔢 샘플(캐비티) 수", min_value=1, value=4)
        raw_input = st.text_area("데이터 붙여넣기", height=350, placeholder="여기에 성적서를 복사하세요...")
        
        if st.button("🚀 데이터 분석 및 변환 시작") and raw_input:
            res_list = parse_dukin_v15(raw_input, sc)
            if res_list:
                st.session_state.df_v15 = pd.DataFrame(res_list)
                st.success(f"✅ {len(res_list)}개 포인트를 성공적으로 분석했습니다!")
                st.dataframe(st.session_state.df_v15, use_container_width=True)
            else:
                st.error("❌ 분석할 수 없는 형식입니다. 항목명(A, B, C...)이 포함되어 있는지 확인해주세요.")

    with t2:
        if 'df_v15' in st.session_state:
            df = st.session_state.df_v15.copy()
            st.markdown("### ⚙️ 위치도 계산 설정")
            c1, c2 = st.columns(2)
            mmc_val = c1.number_input("📏 MMC 기준", value=0.350, format="%.3f")
            tol_val = c2.number_input("📐 기본 공차", value=0.350, format="%.3f")

            if st.button("🔍 위치도 산출 및 판정"):
                # 위치도 공식
                df['위치도'] = (2 * np.sqrt((df['측정_X'] - df['도면_X'])**2 + (df['측정_Y'] - df['도면_Y'])**2)).round(4)
                df['보너스'] = (df['실측지름'] - mmc_val).clip(lower=0).round(4)
                df['최종공차'] = (tol_val + df['보너스']).round(4)
                df['판정'] = np.where(df['위치도'] <= df['최종공차'], "OK", "NG")
                st.session_state.final_v15 = df
                st.dataframe(df.style.apply(lambda x: ["background-color: #fee2e2" if v == "NG" else "" for v in x], axis=1), use_container_width=True)
        else:
            st.warning("데이터 로드 탭을 먼저 완료해주세요.")

    with t3:
        if 'final_v15' in st.session_state:
            res = st.session_state.final_v15
            ok_n = (res['판정'] == "OK").sum()
            st.metric("최종 합격률", f"{(ok_n/len(res))*100:.1f}%", f"{ok_n}/{len(res)} 포인트 합격")
            
            # 엑셀 다운로드
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
                res.to_excel(wr, index=False)
            st.download_button("📥 결과 엑셀 저장", out.getvalue(), "Quality_Report_v15.xlsx")

if __name__ == "__main__":
    main()
