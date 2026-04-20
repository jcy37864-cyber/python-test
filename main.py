import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램 v3.8", layout="wide")

# 2. 커스텀 CSS (UI 개선)
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
        font-size: 0.95rem;
        line-height: 1.6;
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
            result_df.index = result_df.index + 1
            st.dataframe(result_df, use_container_width=True, height=400)
            st.download_button("📂 CSV 다운로드", result_df.to_csv(index=True).encode("utf-8-sig"), "zxy_result.csv")
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 📈 2. 그래프 분석 (엑셀 내 멀티 그래프 첨부)
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
        avg_v = df['VALUE'].mean()
        std_v = df['VALUE'].std()

        # [화면 그래프 1] 점 그래프
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📈 측정 추세 분석 (Line)")
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='측정값'))
        fig_p.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_p.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        if not ng_df.empty:
            fig_p.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='NG', marker=dict(color='red', size=10)))
        if df.loc[worst_idx, "편차"] > 0:
            fig_p.add_trace(go.Scatter(x=[worst_idx], y=[worst_val], mode='markers', name='Worst', marker=dict(color='rgba(0,0,0,0)', size=20, line=dict(color='red', width=3))))
        st.plotly_chart(fig_p, use_container_width=True)

        # [화면 그래프 2] 정밀 막대 그래프
        st.subheader("📊 샘플별 수치 비교 (Bar - 정밀 보기)")
        y_min = min(df["VALUE"].min(), df["MIN"].min()) * 0.999
        y_max = max(df["VALUE"].max(), df["MAX"].max()) * 1.001
        colors = ['#FF4B4B' if p == "NG" else '#00B4D8' for p in df["판정"]]
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(x=df.index, y=df["VALUE"], marker_color=colors, text=df["VALUE"], textposition='outside'))
        fig_b.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green")
        fig_b.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange")
        fig_b.update_layout(yaxis_range=[y_min, y_max], yaxis=dict(tickformat=".3f"), showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [데이터 분석 및 다운로드 섹션]
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("💾 데이터 저장 및 정밀 분석")
        
        # 엑셀/이미지용 1번 그래프 (점) 생성
        fig_mpl1, ax1 = plt.subplots(figsize=(10, 4))
        ax1.plot(df.index, df["VALUE"], marker='o', color='#1f77b4', alpha=0.7)
        ax1.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--')
        ax1.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--')
        if not ng_df.empty: ax1.scatter(ng_df.index, ng_df["VALUE"], color='red', s=40, zorder=5)
        if df.loc[worst_idx, "편차"] > 0: ax1.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=300, linewidths=2, zorder=6)
        ax1.set_title("Trend Analysis (Line)")
        img_line = BytesIO(); fig_mpl1.savefig(img_line, format='png', bbox_inches='tight'); plt.close(fig_mpl1)

        # 엑셀용 2번 그래프 (막대) 생성
        fig_mpl2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.bar(df.index, df["VALUE"], color=['red' if p == "NG" else '#1f77b4' for p in df["판정"]], alpha=0.8)
        ax2.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--')
        ax2.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--')
        ax2.set_ylim(y_min, y_max) # 정밀 보기 적용
        ax2.set_title("Sample Comparison (Bar)")
        img_bar = BytesIO(); fig_mpl2.savefig(img_bar, format='png', bbox_inches='tight'); plt.close(fig_mpl2)

        cd1, cd2 = st.columns(2)
        with cd1:
            excel_buf = BytesIO()
            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Quality_Report')
                workbook, worksheet = writer.book, writer.sheets['Quality_Report']
                red_f = workbook.add_format({'bg_color': '#FFCCCC', 'font_color': '#9C0006', 'num_format': '0.0000'})
                num_f = workbook.add_format({'num_format': '0.0000'})
                for i in range(len(df)):
                    fmt = red_f if df.iloc[i]["판정"] == "NG" else num_f
                    worksheet.set_row(i + 1, None, fmt)
                # 두 개의 그래프 삽입
                worksheet.insert_image('H2', 'line_graph.png', {'image_data': img_line, 'x_scale': 0.5, 'y_scale': 0.5})
                worksheet.insert_image('H22', 'bar_graph.png', {'image_data': img_bar, 'x_scale': 0.5, 'y_scale': 0.5})
            st.download_button("📂 결과 엑셀 다운로드 (그래프 2종 포함)", excel_buf.getvalue(), "Total_Quality_Report.xlsx", use_container_width=True)
        with cd2:
            st.download_button("🖼️ 메인 그래프 이미지 다운로드", img_line.getvalue(), "Trend_Graph.png", use_container_width=True)
        
        st.markdown("---")
        # 분석 리포트 섹션
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.info("📊 **데이터 상세 요약**")
            total_n, ng_n = len(df), len(ng_df)
            m1, m2 = st.columns(2)
            m1.metric("총 샘플", f"{total_n}개")
            m2.metric("불량률", f"{(ng_n/total_n)*100:.1f}%", f"-{ng_n} NG", delta_color="inverse")
            
            if ng_n == 0:
                msg = f"✅ **공정 안정:** 모든 샘플이 규격 내에 있습니다. 평균 {avg_v:.4f}, 산포 {std_v:.4f}로 관리가 우수합니다."
            else:
                msg = f"🚨 **품질 주의:** {ng_n}개의 불량이 발생했습니다. **최대 이탈 No.{worst_idx}({worst_val:.4f})**에 대한 공정 확인이 필요합니다."
            st.markdown(f'<div class="summary-box">{msg}</div>', unsafe_allow_html=True)
        with c2: st.metric("평균값 (Mean)", f"{avg_v:.4f}", f"σ: {std_v:.4f}")
        with c3: st.metric("Worst Point", f"{worst_val:.4f}" if ng_n > 0 else "N/A", f"Idx: {worst_idx}")
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 🧮 3. 계산기 (MMC 포함 최종)
# =========================
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 보조 및 MMC 계산기")
    tabs = st.tabs(["🎯 MMC 보너스", "⚖️ 공차 판정", "🔧 토크 변환", "📏 단위 변환", "📊 데이터 산포"])
    
    with tabs[0]: # MMC
        mc1, mc2 = st.columns(2)
        m_type = mc1.radio("종류", ["구멍 (Hole)", "축 (Shaft)"], horizontal=True, key="m_t_f")
        m_geo = mc2.number_input("도면 기하공차", value=0.05, format="%.4f", key="m_g_f")
        mc3, mc4, mc5 = st.columns(3)
        m_mmc = mc3.number_input("MMC 규격치", value=10.00, format="%.4f", key="m_m_f")
        m_act = mc4.number_input("실측치", value=10.02 if "구멍" in m_type else 9.98, format="%.4f", key="m_a_f")
        bonus = max(0.0, m_act - m_mmc if "구멍" in m_type else m_mmc - m_act)
        mc5.metric("최종 허용치", f"{m_geo + bonus:.4f}", f"+{bonus:.4f}")
        st.info("실제 가공 치수가 MMC에서 벗어난 만큼 기하 공차가 보너스로 부여됩니다.")

    with tabs[1]: # 공차
        p1, p2, p3, p4 = st.columns(4)
        base, u_t, l_t, ms = p1.number_input("기준", key="cb_f"), p2.number_input("상한", key="cu_f"), p3.number_input("하한", key="cl_f"), p4.number_input("측정", key="cm_f")
        lo, up = base - abs(l_t), base + abs(u_t)
        if lo <= ms <= up: st.success(f"✅ OK ({lo:.4f} ~ {up:.4f})")
        else: st.error(f"🚨 NG (이탈: {ms-up if ms>up else ms-lo:+.4f})")

    with tabs[2]: # 토크
        v, m = st.number_input("수치", key="tv_f"), st.selectbox("방향", ["N·m → kgf·m", "kgf·m → N·m"], key="tm_f")
        st.success(f"결과: {v * 0.101972 if 'kgf' in m else v * 9.80665:.4f}")

    with tabs[3]: # 단위
        u_i = st.selectbox("항목", ["mm/inch", "mm/μm", "kg/lb"], key="ui_f")
        u_v = st.number_input("수치", key="uv_f")
        if "inch" in u_i: res, lab = u_v/25.4, "inch"
        elif "μm" in u_i: res, lab = u_v*1000, "μm"
        else: res, lab = u_v*2.20462, "lb"
        st.info(f"결과: {res:.4f} {lab}")

    with tabs[4]: # 산포
        s_t = st.text_area("쉼표 구분 입력", key="st_f")
        try:
            l = [float(x.strip()) for x in s_t.split(",") if x.strip()]
            if l: st.write(f"평균: {sum(l)/len(l):.4f} | R: {max(l)-min(l):.4f}")
        except: pass
    st.markdown('</div>', unsafe_allow_html=True)
