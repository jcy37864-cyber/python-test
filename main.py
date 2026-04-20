import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램 v3.5", layout="wide")

# 2. 커스텀 CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #0E1117 !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    .stBox {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #e1e4e8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        margin-bottom: 25px;
    }
    .summary-box {
        background-color: #f1f3f5;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #1f77b4;
        color: #333 !important;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

plt.rcParams['axes.unicode_minus'] = False
plt.rc('font', family='sans-serif') 

st.title("📊 품질 측정 통합 시스템")
menu = st.sidebar.radio("📋 메뉴 선택", ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"])

# =========================
# 🔄 1. ZXY 변환 (No. 1부터 시작)
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
            result_df.index = result_df.index + 1  # No. 1부터 시작
            st.dataframe(result_df, use_container_width=True, height=400)
            st.download_button("📂 CSV 다운로드", result_df.to_csv(index=True).encode("utf-8-sig"), "zxy_result.csv")
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 📈 2. 그래프 분석 (점+막대 통합 및 다운로드 복구)
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

        # [그래프 영역]
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        
        # 메인 점 그래프
        st.subheader("📈 측정 추세 분석 (Line)")
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='측정값'))
        fig_p.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_p.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        if not ng_df.empty:
            fig_p.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='NG', marker=dict(color='red', size=10)))
        if df.loc[worst_idx, "편차"] > 0: # 워스트 포인트 강조
            fig_p.add_trace(go.Scatter(x=[worst_idx], y=[worst_val], mode='markers', name='Worst', marker=dict(color='rgba(0,0,0,0)', size=20, line=dict(color='red', width=3))))
        st.plotly_chart(fig_p, use_container_width=True)

        # 보조 막대 그래프
      # 보조 막대 그래프 (Y축 범위 최적화 버전)
        st.subheader("📊 샘플별 수치 비교 (Bar - 정밀 보기)")
        colors = ['#FF4B4B' if p == "NG" else '#00B4D8' for p in df["판정"]]
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(
            x=df.index, 
            y=df["VALUE"], 
            marker_color=colors, 
            name='측정치',
            text=df["VALUE"],           # 막대 위에 수치 표시
            textposition='outside'      # 수치 위치
        ))
        
        # 규격선 표시
        fig_b.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_b.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")

        # [핵심] Y축 범위 자동 설정: 측정값의 최소값보다 조금 낮게, 최대값보다 조금 높게
        y_min = min(df["VALUE"].min(), df["MIN"].min()) * 0.999  # 하한값이나 측정값 중 작은 쪽 기준
        y_max = max(df["VALUE"].max(), df["MAX"].max()) * 1.001  # 상한값이나 측정값 중 큰 쪽 기준
        
        fig_b.update_layout(
            yaxis_range=[y_min, y_max], 
            yaxis=dict(tickformat=".3f"), # 소수점 3자리까지 표시
            showlegend=False
        )
        st.plotly_chart(fig_b, use_container_width=True)

        # [다운로드 및 리포트]
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("💾 데이터 저장 및 분석")
        
        # 다운로드용 이미지 생성 (Matplotlib)
        fig_mpl, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df.index, df["VALUE"], marker='o', color='#1f77b4', alpha=0.7)
        ax.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--')
        ax.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--')
        if not ng_df.empty: ax.scatter(ng_df.index, ng_df["VALUE"], color='red', s=40, zorder=5)
        if df.loc[worst_idx, "편차"] > 0: ax.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=300, linewidths=2, zorder=6)
        img_buf = BytesIO(); fig_mpl.savefig(img_buf, format='png', bbox_inches='tight'); plt.close(fig_mpl)

        cd1, cd2 = st.columns(2)
        with cd1:
            excel_buf = BytesIO()
            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Result')
                workbook, worksheet = writer.book, writer.sheets['Result']
                red_f = workbook.add_format({'bg_color': '#FFCCCC', 'font_color': '#9C0006', 'num_format': '0.0000'})
                num_f = workbook.add_format({'num_format': '0.0000'})
                for i in range(len(df)):
                    fmt = red_f if df.iloc[i]["판정"] == "NG" else num_f
                    worksheet.set_row(i + 1, None, fmt)
                worksheet.insert_image('H2', 'graph.png', {'image_data': img_buf, 'x_scale': 0.6, 'y_scale': 0.6})
            st.download_button("📂 결과 엑셀 다운로드", excel_buf.getvalue(), "Quality_Report.xlsx", use_container_width=True)
        with cd2:
            st.download_button("🖼️ 그래프 이미지 다운로드", img_buf.getvalue(), "Quality_Graph.png", use_container_width=True)
        
        st.markdown("---")
        st.dataframe(df.style.format(subset=["MIN", "MAX", "VALUE", "편차"], formatter="{:.4f}").apply(
            lambda r: ['background-color: #FFCCCC; color: #9C0006' if r["판정"] == "NG" else '' for _ in r], axis=1), use_container_width=True)
        
        c1, c2, c3 = st.columns(3)
        avg_v = df['VALUE'].mean()
        with c1:
            st.info("📊 **데이터 정보**")
            msg = f"✅ 모든 샘플 정상." if not len(ng_df) else f"🚨 {len(ng_df)}개의 불량 발견 (No.{worst_idx} 주의)"
            st.markdown(f'<div class="summary-box">{msg}</div>', unsafe_allow_html=True)
        with c2: st.metric("평균값", f"{avg_v:.4f}")
        with c3: st.metric("최대 이탈", f"{worst_val:.4f}" if df.loc[worst_idx, "편차"] > 0 else "N/A")
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 🧮 3. 계산기 (MMC 및 정밀 측정)
# =========================
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 보조 및 MMC 계산기")
    tabs = st.tabs(["🎯 MMC 보너스", "⚖️ 공차 판정", "🔧 토크 변환", "📏 단위 변환", "📊 데이터 산포"])
    
    with tabs[0]: # MMC 계산기
        mc1, mc2 = st.columns(2)
        m_type = mc1.radio("종류", ["구멍 (Hole)", "축 (Shaft)"], horizontal=True, key="m_t")
        m_geo = mc2.number_input("도면 기하공차", value=0.05, format="%.4f", key="m_g")
        mc3, mc4, mc5 = st.columns(3)
        m_mmc = mc3.number_input("MMC 치수 (규격값)", value=10.00, format="%.4f", key="m_m")
        m_act = mc4.number_input("실측 치수", value=10.02 if "구멍" in m_type else 9.98, format="%.4f", key="m_a")
        bonus = max(0.0, m_act - m_mmc if "구멍" in m_type else m_mmc - m_act)
        mc5.metric("최종 허용 공차", f"{m_geo + bonus:.4f}", f"Bonus: +{bonus:.4f}")
        st.info(f"**해설:** 보너스 공차가 가산되어 총 {m_geo + bonus:.4f}까지 허용됩니다.")

    with tabs[1]: # 공차 판정
        p1, p2, p3, p4 = st.columns(4)
        base, u_t, l_t, ms = p1.number_input("기준", key="c_b"), p2.number_input("상한(+)", key="c_u"), p3.number_input("하한(-)", key="c_l"), p4.number_input("측정", key="c_m")
        lo, up = base - abs(l_t), base + abs(u_t)
        if lo <= ms <= up: st.success(f"✅ OK ({lo:.4f} ~ {up:.4f})")
        else: st.error(f"🚨 NG (이탈: {ms-up if ms>up else ms-lo:+.4f})")

    with tabs[2]: # 토크
        v, m = st.number_input("수치", key="t_v"), st.selectbox("방향", ["N·m → kgf·m", "kgf·m → N·m"], key="t_m")
        st.success(f"결과: {v * 0.101972 if 'kgf' in m else v * 9.80665:.4f}")

    with tabs[3]: # 단위
        u_i = st.selectbox("항목", ["mm/inch", "mm/μm", "kg/lb"], key="u_i")
        u_v = st.number_input("수치", key="u_v")
        if "inch" in u_i: res = u_v/25.4; lab = "inch"
        elif "μm" in u_i: res = u_v*1000; lab = "μm"
        else: res = u_v*2.20462; lab = "lb"
        st.info(f"결과: {res:.4f} {lab}")

    with tabs[4]: # 산포
        s_t = st.text_area("쉼표 구분 입력", key="s_t")
        try:
            l = [float(x.strip()) for x in s_t.split(",") if x.strip()]
            if l: st.write(f"평균: {sum(l)/len(l):.4f} | 범위(R): {max(l)-min(l):.4f}")
        except: pass
    st.markdown('</div>', unsafe_allow_html=True)
