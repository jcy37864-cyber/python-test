import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from io import BytesIO

# ==========================================
# 1. 스타일 및 초기화 (디자인 복구)
# ==========================================
def init_app():
    st.set_page_config(page_title="덕인 품질 통합 분석 v10.5", layout="wide")
    st.markdown("""
        <style>
        .main { background-color: #f8fafc; }
        .stBox { background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px; }
        .report-card { background-color: #f1f5f9; padding: 20px; border-left: 10px solid #3b82f6; border-radius: 8px; line-height: 2.0; font-size: 1.1em; }
        .stButton > button { background-color: #ef4444 !important; color: white !important; font-weight: bold; border-radius: 8px; height: 3em; width: 100%; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 통합 파싱 엔진 (안정성 강화 버전)
# ==========================================
def parse_dukin_v24(text, sample_count):
    # 모든 숫자 추출 (가장 안정적인 방식)
    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', text)]
    
    processed = []
    step = 1 + sample_count  # 도면1 + 샘플수
    set_len = step * 3       # P, X, Y 세 줄 묶음
    
    total_items = len(nums) // set_len
    
    for i in range(total_items):
        base = i * set_len
        label = chr(65 + i) if i < 26 else f"P{i+1}"
        
        try:
            # 데이터 슬라이싱
            p_row = nums[base : base + step]
            x_row = nums[base + step : base + (step * 2)]
            y_row = nums[base + (step * 2) : base + (step * 3)]
            
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

# ==========================================
# 3. 메인 앱 로직
# ==========================================
def main():
    init_app()
    st.title("🚀 덕인 성적서 통합 분석 솔루션 v10.5")
    
    tab1, tab2, tab3 = st.tabs(["📥 Step 1. 데이터 로드", "📊 Step 2. 위치도 분석", "📈 Step 3. 통계 리포트"])

    # --- Tab 1: 데이터 로드 ---
    with tab1:
        st.header("데이터 변환 엔진")
        col_opt1, col_opt2 = st.columns([1, 2])
        with col_opt1:
            input_method = st.radio("입력 방식", ["텍스트 붙여넣기", "파일 업로드"])
            sample_count = st.number_input("🔢 샘플(캐비티) 수", min_value=1, value=4)
        
        raw_text = ""
        if input_method == "텍스트 붙여넣기":
            raw_text = st.text_area("성적서 텍스트를 붙여넣으세요", height=250)
        else:
            up_file = st.file_uploader("파일 업로드 (CSV/Excel)", type=['csv', 'xlsx'])
            if up_file:
                if up_file.name.endswith('xlsx'):
                    df_raw = pd.read_excel(up_file, header=None)
                else:
                    df_raw = pd.read_csv(up_file, header=None)
                raw_text = df_raw.to_string()

        if st.button("🚀 데이터 분석 실행") and raw_text:
            res = parse_dukin_v24(raw_text, sample_count)
            if res:
                st.session_state.data = pd.DataFrame(res)
                st.success(f"✅ {len(res)}개 데이터 변환 성공!")
                st.dataframe(st.session_state.data, use_container_width=True)
                st.balloons()
            else:
                st.error("데이터를 파싱하지 못했습니다. 형식을 확인해주세요.")

    # --- Tab 2: 위치도 및 MMC 분석 ---
    with tab2:
        if 'data' not in st.session_state:
            st.warning("⚠️ Step 1에서 데이터를 먼저 로드해 주세요.")
        else:
            st.markdown('<div class="stBox">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            mmc_val = col1.number_input("📏 MMC 기준값", value=0.350, format="%.3f")
            base_tol = col2.number_input("📐 기본 공차", value=0.350, format="%.3f")

            if st.button("🔍 상세 분석 및 산포도 생성"):
                df = st.session_state.data.copy()
                # 계산 로직
                df['위치도'] = (np.sqrt((df['실측_X'] - df['도면_X'])**2 + (df['실측_Y'] - df['도면_Y'])**2) * 2).round(4)
                df['보너스'] = (df['실측지름'] - mmc_val).clip(lower=0).round(4)
                df['최종공차'] = (base_tol + df['보너스']).round(4)
                df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")
                st.session_state.analysed_data = df

                st.dataframe(df.style.apply(lambda x: ["background-color: #ffbaba" if "NG" in str(v) else "" for v in x], axis=1), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if 'analysed_data' in st.session_state:
                st.subheader("🎯 위치도 산포도 (Distribution Map)")
                ad = st.session_state.analysed_data
                dx = ad['실측_X'] - ad['도면_X']
                dy = ad['실측_Y'] - ad['도면_Y']

                fig, ax = plt.subplots(figsize=(6, 6))
                # 가이드 원 (기본공차)
                circle = plt.Circle((0,0), base_tol/2, color='#3498db', fill=True, alpha=0.1)
                ax.add_patch(circle)
                ax.add_patch(plt.Circle((0,0), base_tol/2, color='#3498db', fill=False, lw=2, ls='--'))
                
                # 점 찍기
                colors = ad['판정'].apply(lambda x: '#2ecc71' if 'OK' in x else '#e74c3c')
                ax.scatter(dx, dy, c=colors, s=50, edgecolors='white', zorder=5)
                
                # 축 설정
                lim = max(dx.abs().max(), dy.abs().max(), base_tol/2) * 1.5
                ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
                ax.axhline(0, color='black', lw=1); ax.axvline(0, color='black', lw=1)
                ax.grid(True, ls=':', alpha=0.6)
                ax.set_aspect('equal')
                ax.set_title("X-Y Deviation Map", pad=15)
                st.pyplot(fig)

    # --- Tab 3: 통계 리포트 ---
    with tab3:
        if 'analysed_data' in st.session_state:
            ad = st.session_state.analysed_data
            ok_cnt = (ad['판정'] == "✅ OK").sum()
            ng_cnt = len(ad) - ok_cnt
            
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.subheader("📊 최종 품질 분석 요약")
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.metric("전체 샘플 수", len(ad))
            col_s2.metric("OK", ok_cnt)
            col_s3.metric("NG", ng_cnt, delta_color="inverse")
            st.write(f"최종 합격률: **{(ok_cnt/len(ad))*100:.1f}%**")
            st.markdown('</div>', unsafe_allow_html=True)

            # 다운로드 버튼 (CSV가 서버에서 가장 안정적임)
            csv = ad.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 분석 결과 다운로드 (CSV)", csv, "Quality_Report.csv", "text/csv")
        else:
            st.info("분석을 실행하면 통계 리포트가 활성화됩니다.")

if __name__ == "__main__":
    main()
