import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from io import BytesIO

# ==========================================
# 1. 스타일 및 초기화
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
# 2. 통합 파싱 엔진
# ==========================================
def parse_dukin_v24(text, sample_count):
    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', text)]
    processed = []
    step = 1 + sample_count 
    set_len = step * 3 
    total_items = len(nums) // set_len
    for i in range(total_items):
        base = i * set_len
        label = chr(65 + i) if i < 26 else f"P{i+1}"
        try:
            p_row = nums[base : base + step]
            x_row = nums[base + step : base + (step * 2)]
            y_row = nums[base + (step * 2) : base + (step * 3)]
            for s in range(sample_count):
                processed.append({
                    "항목": f"{label}_S{s+1}",
                    "도면_X": x_row[0], "도면_Y": y_row[0],
                    "실측_X": x_row[s+1], "실측_Y": y_row[s+1],
                    "실측지름": p_row[s+1]
                })
        except: continue
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
            up_file = st.file_uploader("CSV/Excel 업로드", type=['csv', 'xlsx'])
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
                st.success("✅ 데이터 변환 성공!")
                st.dataframe(st.session_state.data, use_container_width=True)
            else:
                st.error("데이터를 파싱하지 못했습니다. 형식을 확인해주세요.")

    # --- Tab 2: 위치도 및 MMC 분석 ---
    with tab2:
        if 'data' not in st.session_state:
            st.warning("⚠️ 데이터를 먼저 로드해 주세요.")
        else:
            st.markdown('<div class="stBox">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            mmc_val = col1.number_input("📏 MMC 기준값", value=0.350, format="%.3f")
            base_tol = col2.number_input("📐 기본 공차", value=0.350, format="%.3f")

            if st.button("🔍 상세 분석 및 과녁 생성"):
                df = st.session_state.data.copy()
                df['위치도'] = (np.sqrt((df['실측_X'] - df['도면_X'])**2 + (df['실측_Y'] - df['도면_Y'])**2) * 2).round(4)
                df['보너스'] = (df['실측지름'] - mmc_val).clip(lower=0).round(4)
                df['최종공차'] = (base_tol + df['보너스']).round(4)
                df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")
                st.session_state.analysed_data = df
                st.dataframe(df.style.apply(lambda x: ["background-color: #ffbaba" if "NG" in str(v) else "" for v in x], axis=1), use_container_width=True)

            if 'analysed_data' in st.session_state:
                st.subheader("🎯 위치도 산포도 (Target Map)")
                ad = st.session_state.analysed_data
                base_r = base_tol / 2  # 기본 공차 반지름
                
                fig = go.Figure()

                # --- 1. 과녁 배경 (원형 허용 구역 채우기) ---
                # 이 부분이 빠지면 과녁이 보이지 않습니다.
                fig.add_shape(
                    type="circle",
                    xref="x", yref="y",
                    x0=-base_r, y0=-base_r, x1=base_r, y1=base_r,
                    fillcolor="rgba(52, 152, 219, 0.3)", # 더 선명한 파란색 채우기
                    line=dict(color="RoyalBlue", width=3), # 테두리 강조
                    layer="below" # 점보다 아래에 그려지게 설정
                )

                # --- 2. 데이터 포인트 (OK/NG 분리) ---
                for p_label, p_color, p_status in [("✅ OK", "#2ecc71", "✅ OK"), ("❌ NG", "#e74c3c", "❌ NG")]:
                    subset = ad[ad['판정'] == p_status]
                    if not subset.empty:
                        fig.add_trace(go.Scatter(
                            x=subset['실측_X'] - subset['도면_X'],
                            y=subset['실측_Y'] - subset['도면_Y'],
                            mode='markers',
                            name=p_label,
                            marker=dict(color=p_color, size=12, line=dict(color='white', width=1)),
                            text=subset['항목'],
                            hovertemplate="<b>%{text}</b><br>X편차: %{x:.4f}<br>Y편차: %{y:.4f}<extra></extra>"
                        ))

                # --- 3. 축 및 레이아웃 설정 (과녁이 잘 보이게 범위 조정) ---
                dev_x = ad['실측_X'] - ad['도면_X']
                dev_y = ad['실측_Y'] - ad['도면_Y']
                # 데이터가 너무 멀리 있으면 과녁이 작게 보이므로 범위를 적절히 제한
                max_dev = max(dev_x.abs().max(), dev_y.abs().max(), base_r * 2)
                lim = max_dev * 1.2

                fig.update_layout(
                    xaxis=dict(range=[-lim, lim], zeroline=True, zerolinewidth=2, zerolinecolor='black', gridcolor='#eee', title="X 편차"),
                    yaxis=dict(range=[-lim, lim], zeroline=True, zerolinewidth=2, zerolinecolor='black', gridcolor='#eee', title="Y 편차"),
                    width=800, height=800,
                    plot_bgcolor='white',
                    showlegend=True,
                    title_text=f"🎯 위치도 분석 과녁 (공차 범위: Ø{base_tol})",
                    title_x=0.5
                )

                st.plotly_chart(fig, use_container_width=True)

    # --- Tab 3: 통계 리포트 ---
    with tab3:
        if 'analysed_data' in st.session_state:
            ad = st.session_state.analysed_data
            ok_cnt = (ad['판정'] == "✅ OK").sum()
            st.markdown(f'<div class="report-card">📊 합격률: **{(ok_cnt/len(ad))*100:.1f}%** ({ok_cnt}/{len(ad)})</div>', unsafe_allow_html=True)
            csv = ad.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 결과 다운로드", csv, "Quality_Report.csv", "text/csv")

if __name__ == "__main__":
    main()
