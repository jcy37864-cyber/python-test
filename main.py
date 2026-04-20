import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램 v3.0", layout="wide")

# 2. 커스텀 CSS (사이드바 흰색 글자, 카드 디자인, 요약박스)
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
    .summary-box {
        background-color: #f1f3f5;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #1f77b4;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #333 !important;
    }
    </style>
""", unsafe_allow_html=True)

plt.rcParams['axes.unicode_minus'] = False
plt.rc('font', family='sans-serif') 

st.title("📊 품질 측정 통합 프로그램")
menu = st.sidebar.radio("📋 메뉴 선택", ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"])

# =========================
# 🔄 1. ZXY 변환
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
# 📈 2. 그래프 분석
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
    uploaded_file = st.file_uploader("파일 업로드 (XLSX, CSV)", type=["xlsx", "csv"])
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df = df.round(4)
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1).round(4)
        worst_idx = df["편차"].idxmax()
        worst_val = df.loc[worst_idx, "VALUE"]
        ng_df = df[df["판정"] == "NG"]

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        fig_plotly = go.Figure()
        fig_plotly.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='측정값'))
        fig_plotly.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_plotly.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        if not ng_df.empty:
            fig_plotly.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='NG', marker=dict(color='red', size=10)))
        st.plotly_chart(fig_plotly, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📋 종합 분석 리포트")
        st.dataframe(df.style.format(subset=["MIN", "MAX", "VALUE", "편차"], formatter="{:.4f}").apply(
            lambda row: ['background-color: #FFCCCC; color: #9C0006' if row["판정"] == "NG" else '' for _ in row], axis=1), use_container_width=True)
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        avg_v = df['VALUE'].mean()
        with c1:
            st.info("📊 **데이터 요약**")
            st.metric("샘플 / NG", f"{len(df)}개", f"{len(ng_df)}개", delta_color="inverse")
            if len(ng_df) == 0:
                msg = f"✅ 모든 샘플이 정상입니다. 평균 {avg_v:.4f}로 안정적인 품질을 유지 중입니다."
            else:
                msg = f"🚨 {len(ng_df)}개의 불량이 발생했습니다. Index {worst_idx}(값: {worst_val:.4f})에서 최대 편차가 확인됩니다."
            st.markdown(f'<div class="summary-box">{msg}</div>', unsafe_allow_html=True)
        with c2:
            st.info("📏 **통계 분석**")
            st.metric("평균값", f"{avg_v:.4f}", f"σ: {df['VALUE'].std():.4f}")
        with c3:
            st.info("📍 **Worst Point**")
            st.metric("최대 이탈", f"{worst_val:.4f}" if df.loc[worst_idx, "편차"] > 0 else "N/A", f"Idx: {worst_idx}")
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 🧮 3. 계산기 (모든 기능 통합)
# =========================
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 보조 계산기")
    tabs = st.tabs(["🔧 토크 변환", "📏 기초 단위 변환", "📊 합계/평균", "⚖️ 공차 판정"])
    
    with tabs[0]:
        st.write("### 토크 단위 상호 변환")
        c1, c2 = st.columns(2)
        val = c1.number_input("수치 입력", value=0.0, format="%.4f", key="t_val")
        mode = c2.selectbox("방향", ["N·m → kgf·m", "kgf·m → N·m"], key="t_mode")
        res = val * 0.101972 if "kgf" in mode else val * 9.80665
        st.success(f"**결과: {res:.4f}**")

    with tabs[1]:
        st.write("### 실무 기초 단위 변환")
        u1, u2, u3 = st.columns([2, 2, 1])
        u_type = u1.selectbox("항목", ["길이 (mm/inch)", "무게 (kg/lb)", "압력 (MPa/psi/bar)"], key="u_type")
        u_val = u2.number_input("수치", value=0.0, format="%.4f", key="u_val")
        if "길이" in u_type:
            u_dir = u3.selectbox("방향", ["mm → inch", "inch → mm"], key="u_l")
            u_res = u_val / 25.4 if "inch" in u_dir else u_val * 25.4
            u_lab = "inch" if "inch" in u_dir else "mm"
        elif "무게" in u_type:
            u_dir = u3.selectbox("방향", ["kg → lb", "lb → kg"], key="u_w")
            u_res = u_val * 2.20462 if "lb" in u_dir else u_val / 2.20462
            u_lab = "lb" if "lb" in u_dir else "kg"
        else:
            u_dir = u3.selectbox("방향", ["MPa → psi", "psi → MPa", "MPa → bar", "bar → MPa"], key="u_p")
            if "psi" in u_dir: u_res = u_val * 145.038 if "MPa" in u_dir.split('→')[0] else u_val / 145.038
            else: u_res = u_val * 10 if "MPa" in u_dir.split('→')[0] else u_val / 10
            u_lab = u_dir.split('→')[1].strip()
        st.info(f"**결과: {u_res:.4f} {u_lab}**")

    with tabs[2]:
        st.write("### 합계 및 평균")
        txt = st.text_area("쉼표(,) 구분 입력", "10, 15.5", key="s_txt")
        try:
            vals = [float(x.strip()) for x in txt.split(",") if x.strip()]
            if vals: st.info(f"합계: {sum(vals):.4f} | 평균: {sum(vals)/len(vals):.4f}")
        except: st.error("숫자만 입력하세요.")

    with tabs[3]:
        st.write("### 공차 판정")
        cc1, cc2, cc3, cc4 = st.columns(4)
        tar = cc1.number_input("기준", value=0.0, key="c_tar")
        ut = cc2.number_input("상한(+)", value=0.0, key="c_ut")
        lt = cc3.number_input("하한(-)", value=0.0, key="c_lt")
        ms = cc4.number_input("측정", value=0.0, key="c_ms")
        mi, ma = tar - abs(lt), tar + abs(ut)
        if mi <= ms <= ma: st.success(f"**OK** ({mi:.4f} ~ {ma:.4f})")
        else: st.error(f"**NG** (이탈: {ms-ma if ms>ma else ms-mi:.4f})")
    st.markdown('</div>', unsafe_allow_html=True)
