import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램 v2.9", layout="wide")

# 2. 커스텀 CSS (사이드바 흰색 글자 및 카드 디자인)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #0E1117 !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] .st-emotion-cache-17l6i46 { font-weight: bold; border-right: 3px solid #1f77b4; }
    .stBox {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #e1e4e8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        margin-bottom: 25px;
    }
    h2 { color: #1f77b4; border-bottom: 2.5px solid #1f77b4; padding-bottom: 12px; }
    .stDataEditor { border: 1px solid #ced4da !important; }
    /* 요약 텍스트 박스 스타일 */
    .summary-box {
        background-color: #f1f3f5;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #1f77b4;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

plt.rcParams['axes.unicode_minus'] = False
plt.rc('font', family='sans-serif') 

st.title("📊 품질 측정 통합 프로그램")
menu = st.sidebar.radio("📋 메뉴 선택", ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"])

# =========================
# 🔄 ZXY 변환
# =========================
if menu == "🔄 ZXY 변환":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🔄 ZXY 데이터 입력 및 변환")
    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({"X": [""] * 100, "Y": [""] * 100, "Z": [""] * 100})
    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic")
    if st.button("🚀 ZXY 결과 생성", use_container_width=True):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row["X"]).strip(), str(row["Y"]).strip(), str(row["Z"]).strip()
            if x and y and z: results.extend([z, x, y])
        if results:
            result_df = pd.DataFrame(results, columns=["변환 결과"])
            st.dataframe(result_df, use_container_width=True, height=400)
            st.download_button("📂 CSV 다운로드", result_df.to_csv(index=False).encode("utf-8-sig"), "zxy_result.csv")
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 📈 그래프 분석 (한글 요약 추가)
# =========================
elif menu == "📈 그래프 분석":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📁 분석 준비")
    template_df = pd.DataFrame({"MIN": [10.0], "MAX": [10.5], "VALUE": [10.25]})
    template_out = BytesIO()
    with pd.ExcelWriter(template_out, engine='xlsxwriter') as writer:
        template_df.to_excel(writer, index=False)
    st.download_button("📥 분석용 엑셀 양식 다운로드", template_out.getvalue(), "품질분석_양식.xlsx")
    
    st.markdown("---")
    uploaded_file = st.file_uploader("양식에 맞춰 작성된 파일을 업로드하세요", type=["xlsx", "csv"])
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df = df.round(4)
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1).round(4)
        worst_idx = df["편차"].idxmax()
        worst_val = df.loc[worst_idx, "VALUE"]
        ng_df = df[df["판정"] == "NG"]

        # 그래프 및 다운로드 (기존 로직 동일)
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        fig_plotly = go.Figure()
        fig_plotly.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='측정값'))
        fig_plotly.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_plotly.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        if not ng_df.empty:
            fig_plotly.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='NG', marker=dict(color='red', size=10)))
        st.plotly_chart(fig_plotly, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 리포트 및 요약
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📋 종합 분석 리포트")
        def highlight_ng(row):
            return ['background-color: #FFCCCC' if row["판정"] == "NG" else '' for _ in row]
        st.dataframe(df.style.format(subset=["MIN", "MAX", "VALUE", "편차"], formatter="{:.4f}").apply(highlight_ng, axis=1), use_container_width=True)
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        avg_v = df['VALUE'].mean()
        ng_count = len(ng_df)
        
        with c1:
            st.info("📊 **데이터 정보**")
            st.metric("샘플수 / NG수", f"{len(df)}개", f"{ng_count}개", delta_color="inverse")
            
            # --- [핵심 추가] 한글 데이터 요약 ---
            st.markdown("**📝 데이터 요약 분석**")
            if ng_count == 0:
                summary_text = f"✅ 모든 샘플이 규격 내에 존재합니다. 평균값({avg_v:.4f})은 안정적이며 공정이 양호하게 관리되고 있습니다."
            else:
                worst_info = f"{worst_val:.4f} (Index {worst_idx})"
                summary_text = f"🚨 총 {ng_count}개의 불량이 발견되었습니다. 특히 {worst_info}에서 최대 편차가 발생했으니 해당 구간의 설비/공정 점검이 필요합니다."
            
            st.markdown(f'<div class="summary-box">{summary_text}</div>', unsafe_allow_html=True)

        with c2:
            st.info("📏 **통계 분석**")
            st.metric("측정 평균값", f"{avg_v:.4f}", f"σ: {df['VALUE'].std():.4f}")
        with c3:
            st.info("📍 **Worst Point**")
            st.metric("최대 이탈값", f"{worst_val:.4f}" if df.loc[worst_idx, "편차"] > 0 else "N/A", f"Idx: {worst_idx}")
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 🧮 계산기
# =========================
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 보조 계산기")
    tabs = st.tabs(["🔧 토크 변환", "📏 기초 단위 변환", "📊 합계/평균", "⚖️ 공차 판정"])
    with tabs[0]: # 토크 로직
        c_t1, c_t2 = st.columns(2)
        val_t = c_t1.number_input("수치", 0.0, format="%.4f")
        mode_t = c_t2.selectbox("방향", ["N·m → kgf·m", "kgf·m → N·m"])
        st.success(f"**결과: {val_t * 0.101972 if 'kgf' in mode_t else val_t * 9.80665:.4f}**")
    # ... (기타 탭 로직 생략, 이전과 동일)
    st.markdown('</div>', unsafe_allow_html=True)
