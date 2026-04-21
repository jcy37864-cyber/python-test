import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import re
from io import BytesIO

# ==========================================
# 1. 스타일 및 초기화 (삭제되었던 스타일 복구)
# ==========================================
def init_app():
    st.set_page_config(page_title="품질 통합 분석 시스템 v10.5", layout="wide")
    st.markdown("""
        <style>
        .main { background-color: #f8fafc; }
        .stBox { background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px; }
        .report-card { background-color: #f1f5f9; padding: 20px; border-left: 10px solid #3b82f6; border-radius: 8px; line-height: 2.0; font-size: 1.1em; }
        .stButton > button { background-color: #ef4444 !important; color: white !important; font-weight: bold; border-radius: 8px; }
        </style>
    """, unsafe_allow_html=True)

def clean_float(value):
    try:
        cleaned = re.sub(r'[^0-9\.\-]', '', str(value))
        return float(cleaned) if cleaned else 0.0
    except: return 0.0

# ==========================================
# 2. 통합 파싱 엔진 (중복 제거하되 기능은 유지)
# ==========================================
def parse_dukin_engine(lines, sample_count):
    processed = []
    # 1. 텍스트 라인을 데이터 리스트로 정밀 변환
    data_grid = []
    for line in lines:
        if isinstance(line, list):
            row = [str(x).strip() for x in line if str(x).strip()]
        else:
            row = re.split(r'\t|\s{2,}', str(line).strip())
            row = [x for x in row if x]
        if row: data_grid.append(row)

    # 2. 3행 유효성 검사 및 추출
    i = 0
    while i < len(data_grid) - 2:
        row1, row2, row3 = data_grid[i], data_grid[i+1], data_grid[i+2]
        
        # 첫 번째 행에 영문자(항목명)가 있는지 확인
        item_match = next((x for x in row1 if x.isalpha() and len(x) == 1), None)
        
        if item_match:
            def extract_numbers(row):
                # 숫자, 소수점, 마이너스 기호만 추출
                nums = []
                for val in row:
                    found = re.findall(r'[-+]?\d*\.\d+|\d+', val)
                    nums.extend([float(f) for f in found])
                return nums

            nums_p = extract_numbers(row1) # 지름/MMC용
            nums_x = extract_numbers(row2) # X 좌표
            nums_y = extract_numbers(row3) # Y 좌표

            # 최소 도면치수 1개 + 측정치 1개는 있어야 계산 가능
            if len(nums_x) >= 2 and len(nums_y) >= 2:
                for s in range(sample_count):
                    try:
                        processed.append({
                            "측정포인트": f"{item_match}_S{s+1}",
                            "도면치수_X": nums_x[0],
                            "도면치수_Y": nums_y[0],
                            "측정치_X": nums_x[s+1] if len(nums_x) > s+1 else nums_x[-1],
                            "측정치_Y": nums_y[s+1] if len(nums_y) > s+1 else nums_y[-1],
                            "실측지름_MMC용": nums_p[s+1] if len(nums_p) > s+1 else nums_p[-1]
                        })
                    except Exception: continue
            i += 3 # 성공 시 3행 건너뜀
        else:
            i += 1 # 실패 시 한 행씩 내려가며 탐색
            
    return processed
# ==========================================
# 3. 메인 앱 레이아웃
# ==========================================
def main():
    init_app()
    st.title("🚀 덕인 성적서 통합 분석 솔루션 v10.5")
    
    tab1, tab2, tab3 = st.tabs(["📥 Step 1. 데이터 로드", "📊 Step 2. 위치도 분석", "📈 Step 3. 통계 리포트"])

    # --- Tab 1: 데이터 로드 (텍스트/파일 모두 지원) ---
    with tab1:
        st.header("데이터 변환 엔진")
        col_opt1, col_opt2 = st.columns([1, 2])
        with col_opt1:
            input_method = st.radio("입력 방식", ["텍스트 붙여넣기", "CSV/Excel 업로드"])
            sample_count = st.number_input("🔢 샘플(캐비티) 수", min_value=1, value=4)
        
        raw_lines = None
        if input_method == "텍스트 붙여넣기":
            raw_data = st.text_area("성적서 텍스트를 붙여넣으세요", height=250)
            if st.button("🚀 데이터 변환 실행") and raw_data:
                raw_lines = [re.split(r'\t|\s{2,}', l.strip()) for l in raw_data.split('\n') if l.strip()]
        else:
            up_file = st.file_uploader("파일 업로드", type=['csv', 'xlsx'])
            if up_file and st.button("🚀 파일 변환 실행"):
                df_raw = pd.read_excel(up_file, header=None) if up_file.name.endswith('xlsx') else pd.read_csv(up_file, header=None)
                raw_lines = df_raw.fillna("").values.tolist()

        if raw_lines:
            res = parse_dukin_engine(raw_lines, sample_count)
            if res:
                st.session_state.data = pd.DataFrame(res)
                st.success(f"✅ {len(res)}개 데이터 변환 성공!")
                st.dataframe(st.session_state.data, use_container_width=True)
                st.balloons()

    # --- Tab 2: 위치도 및 MMC 분석 ---
    with tab2:
        if 'data' not in st.session_state:
            st.warning("⚠️ Step 1에서 데이터를 먼저 로드해 주세요.")
        else:
            df = st.session_state.data.copy()
            st.markdown('<div class="stBox">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            mmc_val = col1.number_input("📏 MMC 기준값", value=0.350, format="%.3f")
            base_tol = col2.number_input("📐 기본 공차", value=0.350, format="%.3f")

            if st.button("🔍 상세 분석 실행"):
                df['위치도결과'] = (np.sqrt((df['측정치_X'] - df['도면치수_X'])**2 + (df['측정치_Y'] - df['도면치수_Y'])**2) * 2).round(4)
                df['보너스공차'] = (df['실측지름_MMC용'] - mmc_val).clip(lower=0).round(4)
                df['최종공차'] = (base_tol + df['보너스공차']).round(4)
                df['판정'] = np.where(df['위치도결과'] <= df['최종공차'], "✅ OK", "❌ NG")
                st.session_state.analysed_data = df # 분석 완료 데이터 저장

                st.dataframe(df.style.apply(lambda x: ["background-color: #ffbaba" if v == "❌ NG" else "" for v in x], axis=1), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if 'analysed_data' in st.session_state:
                st.subheader("🎯 위치도 산포도 (Distribution Map)")
                fig, ax = plt.subplots(figsize=(7, 7))
                ad = st.session_state.analysed_data
                dx, dy = ad['측정치_X'] - ad['도면치수_X'], ad['측정치_Y'] - ad['도면치수_Y']
                
                # 가이드 원 (기본공차 반경)
                ax.add_patch(plt.Circle((0,0), base_tol/2, color='#3498db', fill=True, alpha=0.1, linestyle='--'))
                ax.add_patch(plt.Circle((0,0), base_tol/2, color='#3498db', fill=False, lw=2, label=f'Base Tol (Ø{base_tol})'))
                
                # 데이터 포인트
                colors = ad['판정'].apply(lambda x: '#2ecc71' if 'OK' in x else '#e74c3c')
                ax.scatter(dx, dy, c=colors, s=60, edgecolors='white', zorder=5)
                
                limit = max(dx.abs().max(), dy.abs().max(), base_tol/2) * 1.3
                ax.set_xlim(-limit, limit); ax.set_ylim(-limit, limit)
                ax.axhline(0, color='black', lw=1); ax.axvline(0, color='black', lw=1)
                ax.grid(True, ls=':', alpha=0.5); ax.set_aspect('equal')
                st.pyplot(fig)

    # --- Tab 3: 통계 리포트 및 다운로드 ---
    with tab3:
        if 'analysed_data' in st.session_state:
            ad = st.session_state.analysed_data
            ok_cnt = (ad['판정'] == "✅ OK").sum()
            ng_cnt = len(ad) - ok_cnt
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.subheader("📊 최종 품질 분석 요약")
            st.write(f"Total Samples: {len(ad)} | **OK: {ok_cnt}** | **NG: {ng_cnt}**")
            st.write(f"합격률: **{(ok_cnt/len(ad))*100:.1f}%**")
            st.markdown('</div>', unsafe_allow_html=True)

            # 엑셀 다운로드 기능
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                ad.to_excel(writer, index=False, sheet_name='Analysis_Result')
            st.download_button("📥 분석 결과 엑셀로 저장", output.getvalue(), "Quality_Report.xlsx")
        else:
            st.info("분석을 먼저 실행하면 리포트가 생성됩니다.")

if __name__ == "__main__":
    main()
