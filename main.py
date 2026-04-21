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
                base_r = base_tol / 2  # 반지름
                
                fig = go.Figure()

                # 1. 중앙 십자선 (검은색)
                fig.update_layout(
                    xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black'),
                    yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black')
                )

                # 2. 과녁 원 (이게 안 보이면 반지름이 너무 작은 것임)
                # 원이 너무 작아서 안 보일 수 있으니 테두리를 아주 두껍게 설정
                fig.add_shape(
                    type="circle",
                    xref="x", yref="y",
                    x0=-base_r, y0=-base_r, x1=base_r, y1=base_r,
                    fillcolor="rgba(52, 152, 219, 0.4)", # 내부 색상
                    line=dict(color="RoyalBlue", width=4), # 테두리 두껍게!
                    layer="above" # 점보다 위에 그려서 확실히 보이게 함
                )

                # 3. 데이터 포인트
                for p_label, p_color, p_status in [("✅ OK", "#2ecc71", "✅ OK"), ("❌ NG", "#e74c3c", "❌ NG")]:
                    subset = ad[ad['판정'] == p_status]
                    if not subset.empty:
                        fig.add_trace(go.Scatter(
                            x=subset['실측_X'] - subset['도면_X'],
                            y=subset['실측_Y'] - subset['도면_Y'],
                            mode='markers',
                            name=p_label,
                            marker=dict(color=p_color, size=12, line=dict(color='white', width=1)),
                            text=subset['항목']
                        ))

                # 4. 축 범위 강제 조정 (데이터가 너무 멀면 과녁이 안 보임)
                # 만약 점들이 100씩 떨어져 있다면, 과녁(0.35)을 보기 위해 범위를 제한해야 함
                dev_x = ad['실측_X'] - ad['도면_X']
                dev_y = ad['실측_Y'] - ad['도면_Y']
                
                # 데이터가 있더라도 최소한 공차의 5배 정도는 보이게 설정
                view_range = max(base_r * 5, 0.5) 
                
                fig.update_layout(
                    # 주석: 아래 범위를 주석 처리하면 점들이 다 보이지만 과녁은 작아집니다.
                    # 일단 과녁 확인을 위해 범위를 좁게 잡아보겠습니다.
                    xaxis=dict(range=[-view_range, view_range], gridcolor='#eee'),
                    yaxis=dict(range=[-view_range, view_range], gridcolor='#eee'),
                    width=800, height=800,
                    plot_bgcolor='white',
                    title_text=f"🎯 과녁 중심부 확대 (공차: Ø{base_tol})"
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
