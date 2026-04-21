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

    with tab1:
        st.header("데이터 변환 엔진")
        col_opt1, col_opt2 = st.columns([1, 2])
        with col_opt1:
            input_method = st.radio("입력 방식", ["텍스트 붙여넣기", "파일 업로드"])
            sample_count = st.number_input("🔢 샘플(캐비티) 수", min_value=1, value=4)
        
        raw_text = st.text_area("데이터 입력", height=250) if input_method == "텍스트 붙여넣기" else ""
        if input_method == "파일 업로드":
            up_file = st.file_uploader("CSV/Excel 업로드", type=['csv', 'xlsx'])
            if up_file: raw_text = pd.read_excel(up_file).to_string() if up_file.name.endswith('xlsx') else pd.read_csv(up_file).to_string()

        if st.button("🚀 데이터 분석 실행") and raw_text:
            res = parse_dukin_v24(raw_text, sample_count)
            if res:
                st.session_state.data = pd.DataFrame(res)
                st.success("✅ 데이터 변환 성공!")
                st.dataframe(st.session_state.data, use_container_width=True)

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
                base_r = base_tol / 2 # 반경 계산
                
                fig = go.Figure()

                # --- 1. 과녁 배경 (허용부 색상 채우기) ---
                fig.add_shape(type="circle", xref="x", yref="y",
                              x0=-base_r, y0=-base_r, x1=base_r, y1=base_r, 
                              fillcolor="rgba(52, 152, 219, 0.2)", # 연한 파란색 채우기
                              line=dict(color="RoyalBlue", width=2))

                # --- 2. 데이터 포인트 (OK/NG 색상 분리) ---
                # OK 데이터
                ok_df = ad[ad['판정'] == "✅ OK"]
                fig.add_trace(go.Scatter(
                    x=ok_df['실측_X'] - ok_df['도면_X'],
                    y=ok_df['실측_Y'] - ok_df['도면_Y'],
                    mode='markers',
                    name='✅ OK',
                    marker=dict(color='#2ecc71', size=11, line=dict(color='white', width=1)),
                    text=ok_df['항목'],
                    hovertemplate="<b>%{text}</b><br>X 편차: %{x:.4f}<br>Y 편차: %{y:.4f}<extra></extra>"
                ))

                # NG 데이터
                ng_df = ad[ad['판정'] == "❌ NG"]
                fig.add_trace(go.Scatter(
                    x=ng_df['실측_X'] - ng_df['도면_X'],
                    y=ng_df['실측_Y'] - ng_df['도면_Y'],
                    mode='markers',
                    name='❌ NG',
                    marker=dict(color='#e74c3c', size=11, line=dict(color='white', width=1)),
                    text=ng_df['항목'],
                    hovertemplate="<b>%{text}</b><br>X 편차: %{x:.4f}<br>Y 편차: %{y:.4f}<extra></extra>"
                ))

                # --- 3. 레이아웃 설정 ---
                dev_x = ad['실측_X'] - ad['도면_X']
                dev_y = ad['실측_Y'] - ad['도면_Y']
                lim = max(dev_x.abs().max(), dev_y.abs().max(), base_r) * 1.4
                
                fig.update_layout(
                    xaxis=dict(range=[-lim, lim], zeroline=True, zerolinewidth=2, zerolinecolor='black', gridcolor='#f0f0f0'),
                    yaxis=dict(range=[-lim, lim], zeroline=True, zerolinewidth=2, zerolinecolor='black', gridcolor='#f0f0f0'),
                    width=700, height=700,
                    plot_bgcolor='white',
                    showlegend=True,
                    title_text=f"X-Y Deviation (Tolerance: Ø{base_tol})",
                    title_x=0.5,
                    aspectratio=dict(x=1, y=1)
                )
                
                st.plotly_chart(fig, use_container_width=True)
