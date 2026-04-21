import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from io import BytesIO

# ==========================================
# 1. 스타일 및 초기화
# ==========================================
def init_app():
    st.set_page_config(page_title="덕인 성적서 마스터 v12.0", layout="wide")
    st.markdown("""
        <style>
        .main { background-color: #f8fafc; }
        .stBox { background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px; }
        .report-card { background-color: #f1f5f9; padding: 20px; border-left: 10px solid #3b82f6; border-radius: 8px; line-height: 2.0; font-size: 1.1em; }
        .stButton > button { background-color: #ef4444 !important; color: white !important; font-weight: bold; border-radius: 8px; width: 100%; height: 3em; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 초정밀 파싱 엔진 (패턴 인식 강화)
# ==========================================
def parse_dukin_v12(raw_text, sample_count):
    processed = []
    # 1. 항목 단위로 데이터 쪼개기 (A, B, C... 대문자 기준)
    # 텍스트 내에서 '알파벳 한글자'를 기준으로 데이터를 나눕니다.
    parts = re.split(r'\s([A-L])\s|\s([A-L])\t|^([A-L])\t', raw_text)
    
    # split 결과에서 None 제거 및 정리
    cleaned_parts = [p.strip() for p in parts if p and p.strip()]
    
    # 구조: ['위치도정보', 'A', 'A의데이터들', 'B', 'B의데이터들'...]
    # 실제 데이터는 index 1부터 (항목명, 데이터) 쌍으로 존재
    for i in range(0, len(cleaned_parts)-1):
        name = cleaned_parts[i]
        if len(name) == 1 and name.isalpha(): # 항목명(A, B...) 확인
            content = cleaned_parts[i+1]
            
            # 해당 항목에서 모든 숫자 추출
            nums = re.findall(r'[-+]?\d*\.\d+|\d+', content)
            nums = [float(n) for n in nums]
            
            per_line = 1 + sample_count # 도면치수 1개 + 샘플들 n개
            
            # 덕인 성적서 3행 구조: [P행] [X행] [Y행]
            if len(nums) >= per_line * 2:
                try:
                    # 데이터가 3세트(P, X, Y)인 경우와 2세트(X, Y)인 경우 대응
                    if len(nums) >= per_line * 3:
                        p_idx, x_idx, y_idx = 0, per_line, per_line * 2
                    else:
                        p_idx, x_idx, y_idx = -1, 0, per_line # P행이 없는 경우

                    for s in range(sample_count):
                        processed.append({
                            "항목": f"{name}_S{s+1}",
                            "도면_X": nums[x_idx],
                            "도면_Y": nums[y_idx],
                            "측정_X": nums[x_idx + 1 + s],
                            "측정_Y": nums[y_idx + 1 + s],
                            "실측지름": nums[p_idx + 1 + s] if p_idx != -1 else 0.0
                        })
                except: continue
    return processed

# ==========================================
# 3. 메인 화면 구성
# ==========================================
def main():
    init_app()
    st.title("🚀 덕인 위치도 통합 분석 솔루션 v12.0")
    
    tab1, tab2, tab3 = st.tabs(["📥 데이터 로드", "📊 위치도 분석", "📈 통계 리포트"])

    with tab1:
        st.info("성적서 전체를 복사해서 아래 칸에 붙여넣으세요.")
        col_set1, col_set2 = st.columns([1, 2])
        sample_count = col_set1.number_input("🔢 샘플(캐비티) 수", min_value=1, value=4)
        
        raw_data = st.text_area("성적서 텍스트 붙여넣기", height=300, placeholder="여기에 붙여넣으세요...")
        
        if st.button("🚀 분석 데이터 변환 시작") and raw_data:
            res = parse_dukin_v12(raw_data, sample_count)
            if res:
                st.session_state.data = pd.DataFrame(res)
                st.success(f"✅ {len(res)}개의 데이터 포인트를 찾았습니다!")
                st.dataframe(st.session_state.data, use_container_width=True)
            else:
                st.error("❌ 데이터를 분석할 수 없습니다. 항목명(A, B...)이 포함되어 있는지 확인해주세요.")

    with tab2:
        if 'data' not in st.session_state:
            st.warning("⚠️ 먼저 데이터를 로드해 주세요.")
        else:
            df = st.session_state.data.copy()
            st.markdown('<div class="stBox">', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            mmc_base = c1.number_input("📏 MMC 기준값", value=0.350, format="%.3f")
            tol_base = c2.number_input("📐 기본 공차", value=0.350, format="%.3f")

            if st.button("🔍 위치도 계산 및 판정 실행"):
                # 위치도 공식: 2 * sqrt(dx^2 + dy^2)
                df['위치도'] = (2 * np.sqrt((df['측정_X'] - df['도면_X'])**2 + (df['측정_Y'] - df['도면_Y'])**2)).round(4)
                df['보너스'] = (df['실측지름'] - mmc_base).clip(lower=0).round(4)
                df['최종공차'] = (tol_base + df['보너스']).round(4)
                df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")
                st.session_state.analysed = df
                
                st.dataframe(df.style.apply(lambda x: ["background-color: #ffbaba" if v == "❌ NG" else "" for v in x], axis=1), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if 'analysed' in st.session_state:
                st.subheader("🎯 위치도 산포도")
                ad = st.session_state.analysed
                fig, ax = plt.subplots(figsize=(6,6))
                dx, dy = ad['측정_X'] - ad['도면_X'], ad['측정_Y'] - ad['도면_Y']
                ax.add_patch(plt.Circle((0,0), tol_base/2, color='#3498db', fill=False, lw=2, linestyle='--'))
                colors = ad['판정'].apply(lambda x: '#2ecc71' if 'OK' in x else '#e74c3c')
                ax.scatter(dx, dy, c=colors, s=50, edgecolors='white')
                limit = max(dx.abs().max(), dy.abs().max(), tol_base/2) * 1.5
                ax.set_xlim(-limit, limit); ax.set_ylim(-limit, limit)
                ax.axhline(0, color='gray', lw=1); ax.axvline(0, color='gray', lw=1)
                ax.set_aspect('equal')
                st.pyplot(fig)

    with tab3:
        if 'analysed' in st.session_state:
            ad = st.session_state.analysed
            ok_n = (ad['판정'] == "✅ OK").sum()
            st.markdown(f'<div class="report-card"><b>합격률: {(ok_n/len(ad))*100:.1f}%</b> ({ok_n}/{len(ad)})</div>', unsafe_allow_html=True)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                ad.to_excel(writer, index=False)
            st.download_button("📥 엑셀 저장", output.getvalue(), "Result.xlsx")

if __name__ == "__main__":
    main()
