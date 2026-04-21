import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from io import BytesIO

# 1. 스타일 설정
def init_app():
    st.set_page_config(page_title="덕인 성적서 완벽 분석 v14.0", layout="wide")
    st.markdown("""
        <style>
        .stButton > button { background-color: #ef4444 !important; color: white !important; font-weight: bold; height: 3.5em; width: 100%; }
        .main { background-color: #f8fafc; }
        </style>
    """, unsafe_allow_html=True)

# 2. 최신 파싱 엔진 (행 단위 추적 방식)
def parse_dukin_v14(raw_text, sample_count):
    processed = []
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    i = 0
    while i < len(lines):
        curr_line = lines[i]
        
        # [패턴] 줄 어딘가에 대문자 A-L이 단독으로 있는지 확인
        # "위치도 A 0.069..." 형태나 "A 0.069..." 형태 모두 대응
        match = re.search(r'(?:\s|^)([A-L])(?:\s|$|\t)', curr_line)
        
        if match and i + 2 < len(lines):
            try:
                name = match.group(1) # 찾은 항목명 (A, B, C...)
                
                # 숫자만 추출하는 도우미 함수
                def extract_nums(text):
                    return [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', text)]

                nums_p = extract_nums(lines[i])   # 현재 줄 (P 또는 위치도)
                nums_x = extract_nums(lines[i+1]) # 다음 줄 (X)
                nums_y = extract_nums(lines[i+2]) # 다다음 줄 (Y)

                # 한 행에 [도면값 + 샘플값들] 구조인지 확인
                # 최소 2개(도면1, 샘플1)는 있어야 함
                if len(nums_x) >= 2 and len(nums_y) >= 2:
                    for s in range(sample_count):
                        processed.append({
                            "항목": f"{name}_S{s+1}",
                            "도면_X": nums_x[0],
                            "도면_Y": nums_y[0],
                            "실측_X": nums_x[s+1] if len(nums_x) > s+1 else nums_x[-1],
                            "실측_Y": nums_y[s+1] if len(nums_y) > s+1 else nums_y[-1],
                            "실측지름": nums_p[s+1] if len(nums_p) > s+1 else 0.0
                        })
                    i += 3 # 3행 세트 처리 완료했으니 점프
                else:
                    i += 1
            except:
                i += 1
        else:
            i += 1
    return processed

# 3. 메인 앱 실행
def main():
    init_app()
    st.title("🚀 덕인 위치도 마스터 v14.0")
    
    t1, t2, t3 = st.tabs(["📥 1. 데이터 입력", "📊 2. 위치도 분석", "📈 3. 리포트"])

    with t1:
        st.info("성적서를 전체 복사해서 아래에 붙여넣으세요. (v14.0은 항목명을 기준으로 3행씩 자동 분석합니다)")
        sc = st.number_input("🔢 샘플(캐비티) 수 설정", min_value=1, value=4)
        raw_input = st.text_area("텍스트 데이터 붙여넣기", height=350)
        
        if st.button("🚀 데이터 분석 및 표 생성") and raw_input:
            data = parse_dukin_v14(raw_input, sc)
            if data:
                st.session_state.master_df = pd.DataFrame(data)
                st.success(f"✅ {len(data)}개의 포인트를 정상적으로 읽었습니다!")
                st.dataframe(st.session_state.master_df, use_container_width=True)
            else:
                st.error("❌ 데이터를 인식하지 못했습니다. 항목명(A, B...) 형식을 확인해 주세요.")

    with t2:
        if 'master_df' in st.session_state:
            df = st.session_state.master_df.copy()
            st.write("### ⚙️ 공차 설정 및 계산")
            c1, c2 = st.columns(2)
            base_mmc = c1.number_input("📏 MMC 기준값", value=0.350, format="%.3f")
            base_tol = c2.number_input("📐 기본 공차값", value=0.350, format="%.3f")

            if st.button("🔍 위치도 계산 실행"):
                # 위치도 공식: 2 * sqrt( (실측X-도면X)^2 + (실측Y-도면Y)^2 )
                df['위치도'] = (2 * np.sqrt((df['실측_X'] - df['도면_X'])**2 + (df['실측_Y'] - df['도면_Y'])**2)).round(4)
                df['보너스'] = (df['실측지름'] - base_mmc).clip(lower=0).round(4)
                df['최종공차'] = (base_tol + df['보너스']).round(4)
                df['판정'] = np.where(df['위치도'] <= df['최종공차'], "OK", "NG")
                st.session_state.final_res = df
                
                # 결과 테이블 출력 (NG는 빨간색)
                st.dataframe(df.style.apply(lambda x: ["background-color: #ffcccc" if v == "NG" else "" for v in x], axis=1), use_container_width=True)
        else:
            st.warning("데이터 로드 탭에서 먼저 분석을 진행해 주세요.")

    with t3:
        if 'final_res' in st.session_state:
            res = st.session_state.final_res
            ok_cnt = (res['판정'] == "OK").sum()
            st.metric("최종 합격률", f"{(ok_cnt/len(res))*100:.1f}%", f"{ok_cnt}/{len(res)} 개 합격")
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                res.to_excel(writer, index=False)
            st.download_button("📥 엑셀 파일 다운로드", output.getvalue(), "Dukin_Result.xlsx")

if __name__ == "__main__":
    main()
