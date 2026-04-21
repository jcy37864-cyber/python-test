import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import re
from io import BytesIO

# ==========================================
# 1. 스타일 및 초기화
# ==========================================
def init_app():
    st.set_page_config(page_title="품질 통합 분석 시스템 v11.5", layout="wide")
    st.markdown("""
        <style>
        .main { background-color: #f8fafc; }
        .stBox { background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px; }
        .report-card { background-color: #f1f5f9; padding: 20px; border-left: 10px solid #3b82f6; border-radius: 8px; line-height: 2.0; font-size: 1.1em; }
        .stButton > button { background-color: #ef4444 !important; color: white !important; font-weight: bold; border-radius: 8px; width: 100%; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 최신 파싱 엔진 (보내주신 데이터 맞춤형)
# ==========================================
def parse_dukin_v11_5(raw_data, sample_count):
    processed = []
    # 텍스트 전처리
    if isinstance(raw_data, list):
        full_text = "\n".join([" ".join([str(x) for x in line]) for line in raw_data])
    else:
        full_text = raw_data.replace('"', '').strip()
    
    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
    
    i = 0
    while i < len(lines):
        # 영문자 항목명(A~L) 찾기
        match = re.search(r'([A-L])\t|([A-L])$|([A-L])\s', lines[i])
        
        if match and i + 2 < len(lines):
            try:
                name = match.group().strip()
                
                def get_floats(text):
                    return [float(x) for x in re.findall(r'[-+]?\d*\.\d+|\d+', text)]

                row_p = get_floats(lines[i])   # 위치도/지름 행
                row_x = get_floats(lines[i+1]) # X 좌표 행
                row_y = get_floats(lines[i+2]) # Y 좌표 행

                # 도면치수(첫번째 값)와 샘플들 매칭
                for s in range(sample_count):
                    processed.append({
                        "측정포인트": f"{name}_S{s+1}",
                        "도면치수_X": row_x[0],
                        "도면치수_Y": row_y[0],
                        "측정치_X": row_x[s+1] if len(row_x) > s+1 else row_x[-1],
                        "측정치_Y": row_y[s+1] if len(row_y) > s+1 else row_y[-1],
                        "실측지름_MMC용": row_p[s+1] if len(row_p) > s+1 else 0.0
                    })
                i += 3 # 한 세트(3행) 완료
            except:
                i += 1
        else:
            i += 1
    return processed

# ==========================================
# 3. 메인 앱 레이아웃
# ==========================================
def main():
    init_app()
    st.title("🚀 덕인 성적서 통합 분석 솔루션 v11.5")
    
    tab1, tab2, tab3 = st.tabs(["📥 Step 1. 데이터 로드", "📊 Step 2. 위치도 분석", "📈 Step 3. 통계 리포트"])

    with tab1:
        st.header("데이터 변환 엔진")
        col_opt1, col_opt2 = st.columns([1, 2])
        with col_opt1:
            input_method = st.radio("입력 방식", ["텍스트 붙여넣기", "CSV/Excel 업로드"])
            sample_count = st.number_input("🔢 샘플(캐비티) 수", min_value=1, value=4)
        
        raw_input_data = None
        if input_method == "텍스트 붙여넣기":
            raw_input_data = st.text_area("성적서 텍스트를 붙여넣으세요", height=250)
            btn_label = "🚀 데이터 변환 실행"
        else:
            up_file = st.file_uploader("파일 업로드", type=['csv', 'xlsx'])
            if up_file:
                df_raw = pd.read_excel(up_file, header=None) if up_file.name.endswith('xlsx') else pd.read_csv(up_file, header=None)
                raw_input_data = df_raw.fillna("").values.tolist()
            btn_label = "🚀 파일 변환 실행"

        if st.button(btn_label) and raw_input_data:
            res = parse_dukin_v11_5(raw_input_data, sample_count)
            if res:
                st.session_state.data = pd.DataFrame(res)
                st.success(f"✅ {len(res)}개 데이터 변환 성공!")
                st.dataframe(st.session_state.data, use_container_width=True)
                st.balloons()
            else:
                st.error("❌ 데이터를 분석할 수 없습니다. 형식을 확인해주세요.")

    with tab2:
        if 'data' not in st.session_state:
            st.warning("⚠️ Step 1에서 데이터를 먼저 로드해 주세요.")
        else:
            df = st.session_state.data.copy()
            st.markdown('<div class="stBox">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            mmc_val = col1.number_input("📏 MMC 기준값", value=0.350, format="%.3f")
            base_tol = col2.number_input("📐 기본 공차", value=0.350, format="%.3f")

            if st.button("🔍 상세 분석 및 위치도 계산"):
                df['위치도결과'] = (2 * np.sqrt((df['측정치_X'] - df['도면치수_X'])**2 + (df['측정치_Y'] - df['도면치수_Y'])**2)).round(4)
                df['보너스공차'] = (df['실측지름_MMC용'] - mmc_val).clip(lower=0).round(4)
                df['최종공차'] = (base_tol + df['보너스공차']).round(4)
                df['판정'] = np.where(df['위치도결과'] <= df['최종공차'], "✅ OK", "❌ NG")
                st.session_state.analysed_data = df 

                st.dataframe(df.style.apply(lambda x: ["background-color: #ffbaba" if v == "❌ NG" else "" for v in x], axis=1), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if 'analysed_data' in st.session_state:
                st.subheader("🎯 위치도 산포도 (Distribution Map)")
                fig, ax = plt.subplots(figsize=(7, 7))
                ad = st.session_state.analysed_data
                dx, dy = ad['측정치_X'] - ad['도면치수_X'], ad['측정치_Y'] - ad['도면치수_Y']
                
                ax.add_patch(plt.Circle((0,0), base_tol/2, color='#3498db', fill=True, alpha=0.1, linestyle='--'))
                ax.add_patch(plt.Circle((0,0), base_tol/2, color='#3498db', fill=False, lw=2))
                
                colors = ad['판정'].apply(lambda x: '#2ecc71' if 'OK' in x else '#e74c3c')
                ax.scatter(dx, dy, c=colors, s=60, edgecolors='white', zorder=5)
                
                limit = max(dx.abs().max(), dy.abs().max(), base_tol/2) * 1.5
                ax.set_xlim(-limit, limit); ax.set_ylim(-limit, limit)
                ax.axhline(0, color='black', lw=1); ax.axvline(0, color='black', lw=1)
                ax.grid(True, ls=':', alpha=0.5); ax.set_aspect('equal')
                st.pyplot(fig)

    with tab3:
        if 'analysed_data' in st.session_state:
            ad = st.session_state.analysed_data
            ok_cnt = (ad['판정'] == "✅ OK").sum()
            ng_cnt = len(ad) - ok_cnt
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.subheader("📊 최종 품질 분석 요약")
            st.write(f"Total Points: {len(ad)} | **OK: {ok_cnt}** | **NG: {ng_cnt}**")
            st.write(f"합격률: **{(ok_cnt/len(ad))*100:.1f}%**")
            st.markdown('</div>', unsafe_allow_html=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                ad.to_excel(writer, index=False, sheet_name='Analysis_Result')
            st.download_button("📥 분석 결과 엑셀로 저장", output.getvalue(), "Quality_Report.xlsx")
        else:
            st.info("분석을 먼저 실행하면 리포트가 생성됩니다.")

if __name__ == "__main__":
    main()
