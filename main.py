import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정실 통합 시스템 v4.1", layout="wide")

# 2. 커스텀 CSS (버튼 가시성 보강 및 UI 디자인)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #0E1117 !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    
    /* 사이드바 내의 모든 버튼 글자색 강제 지정 */
    [data-testid="stSidebar"] button p {
        color: #FFFFFF !important;
        font-weight: bold;
    }
    
    /* 초기화 버튼 전용 스타일 (빨간색 계열로 강조) */
    div.stButton > button {
        border-radius: 8px;
    }
    
    /* 사이드바 리셋 버튼 전용 스타일 */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
    }

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

st.title("📊 품질 측정실 통합 시스템")

# =========================
# 🛠️ 사이드바 메뉴 및 가이드
# =========================
st.sidebar.title("🚀 정밀측정")
menu = st.sidebar.radio("📋 메뉴 선택", ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"])

st.sidebar.markdown("---")

if menu == "🔄 ZXY 변환":
    st.sidebar.info("**🔄 ZXY 변환**\n\n측정 좌표를 표준 순서(Z→X→Y)로 자동 재배열합니다. 결과 No.는 1번부터 시작됩니다.")
elif menu == "📈 그래프 분석":
    st.sidebar.info("**📈 그래프 분석**\n\n추세 점그래프와 정밀 막대그래프를 제공하며, 엑셀 보고서 추출이 가능합니다.")
elif menu == "🧮 계산기":
    st.sidebar.info("**🧮 품질 계산기**\n\nMMC 보너스 공차 계산, 정밀 공차 판정, 단위 변환 등 실무 수식을 제공합니다.")

st.sidebar.markdown("---")
# [개선] 글자가 항상 잘 보이는 초기화 버튼
if st.sidebar.button("🧹 데이터 초기화 (Reset)", use_container_width=True):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

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
            result_df.index = result_df.index + 1
            st.dataframe(result_df, use_container_width=True, height=400)
            
            st.markdown("### 📋 간편 복사 영역")
            copy_text = "\n".join(map(str, results))
            st.text_area("드래그하여 전체 복사가 가능합니다.", copy_text, height=150)
            
            st.download_button("📂 CSV 다운로드", result_df.to_csv(index=True).encode("utf-8-sig"), "zxy_result.csv")
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
        avg_v, std_v = df['VALUE'].mean(), df['VALUE'].std()

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        
        # 1. 추세 점 그래프 (호버 라벨 확대 적용)
        st.subheader("📈 측정 추세 분석 (Line)")
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='측정값',
                                   hovertemplate='샘플 No: %{x}<br>측정값: %{y:.4f}<extra></extra>'))
        fig_p.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_p.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        
        if not ng_df.empty:
            fig_p.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='NG', marker=dict(color='red', size=10)))
        if df.loc[worst_idx, "편차"] > 0:
            fig_p.add_trace(go.Scatter(x=[worst_idx], y=[worst_val], mode='markers', name='Worst', 
                                        marker=dict(color='rgba(0,0,0,0)', size=20, line=dict(color='red', width=3))))
        
        # [핵심] 호버 라벨 디자인 및 크기 확대
        fig_p.update_layout(
            hoverlabel=dict(bgcolor="black", font_size=20, font_color="white", font_family="Malgun Gothic"),
            hovermode="closest",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_p, use_container_width=True)

        # 2. 정밀 막대 그래프 (호버 라벨 확대 적용)
        st.subheader("📊 샘플별 수치 비교 (Bar - 정밀 보기)")
        y_min, y_max = min(df["VALUE"].min(), df["MIN"].min()) * 0.999, max(df["VALUE"].max(), df["MAX"].max()) * 1.001
        colors = ['#FF4B4B' if p == "NG" else '#00B4D8' for p in df["판정"]]
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(x=df.index, y=df["VALUE"], marker_color=colors, text=df["VALUE"], textposition='outside',
                               hovertemplate='샘플 No: %{x}<br>측정값: %{y:.4f}<extra></extra>'))
        fig_b.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green")
        fig_b.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange")
        
        fig_b.update_layout(
            yaxis_range=[y_min, y_max], 
            yaxis=dict(tickformat=".3f"),
            hoverlabel=dict(bgcolor="darkblue", font_size=20, font_color="white", font_family="Malgun Gothic"),
            showlegend=False
        )
        st.plotly_chart(fig_b, use_container_width=True)

        # 3. 데이터 분포 히스토그램
        st.subheader("🎯 데이터 분포 분석 (Histogram)")
        fig_h = go.Figure()
        fig_h.add_trace(go.Histogram(x=df["VALUE"], nbinsx=15, marker_color='#1f77b4', opacity=0.7,
                                     hovertemplate='범위: %{x}<br>개수: %{y}<extra></extra>'))
        fig_h.add_vline(x=df["MAX"].iloc[0], line_color="green", line_dash="dash")
        fig_h.add_vline(x=df["MIN"].iloc[0], line_color="orange", line_dash="dash")
        fig_h.update_layout(
            xaxis_title="측정값", yaxis_title="빈도수",
            hoverlabel=dict(bgcolor="gray", font_size=18, font_color="white")
        )
        st.plotly_chart(fig_h, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [리포트 및 다운로드 섹션]
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("💾 데이터 저장 및 정밀 분석")
        
        # 엑셀용 이미지 생성 (Matplotlib)
        fig_mpl1, ax1 = plt.subplots(figsize=(10, 4))
        ax1.plot(df.index, df["VALUE"], marker='o', color='#1f77b4', alpha=0.7)
        ax1.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--')
        ax1.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--')
        if not ng_df.empty: ax1.scatter(ng_df.index, ng_df["VALUE"], color='red', s=40, zorder=5)
        if df.loc[worst_idx, "편차"] > 0: ax1.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=300, linewidths=2, zorder=6)
        img_line = BytesIO(); fig_mpl1.savefig(img_line, format='png', bbox_inches='tight'); plt.close(fig_mpl1)

        fig_mpl2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.bar(df.index, df["VALUE"], color=['red' if p == "NG" else '#1f77b4' for p in df["판정"]], alpha=0.8)
        ax2.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--')
        ax2.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--')
        ax2.set_ylim(y_min, y_max); img_bar = BytesIO(); fig_mpl2.savefig(img_bar, format='png', bbox_inches='tight'); plt.close(fig_mpl2)

        cd1, cd2 = st.columns(2)
        with cd1:
            excel_buf = BytesIO()
            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Report')
                workbook, worksheet = writer.book, writer.sheets['Report']
                red_f = workbook.add_format({'bg_color': '#FFCCCC', 'font_color': '#9C0006', 'num_format': '0.0000'})
                num_f = workbook.add_format({'num_format': '0.0000'})
                for i in range(len(df)):
                    fmt = red_f if df.iloc[i]["판정"] == "NG" else num_f
                    worksheet.set_row(i + 1, None, fmt)
                worksheet.insert_image('H2', 'line.png', {'image_data': img_line, 'x_scale': 0.5, 'y_scale': 0.5})
                worksheet.insert_image('H22', 'bar.png', {'image_data': img_bar, 'x_scale': 0.5, 'y_scale': 0.5})
            st.download_button("📂 결과 엑셀 다운로드 (그래프 2종 포함)", excel_buf.getvalue(), "Quality_Report_v4_2.xlsx", use_container_width=True)
        with cd2:
            st.download_button("🖼️ 메인 그래프 이미지 다운로드", img_line.getvalue(), "Trend_Graph.png", use_container_width=True)
        
        st.markdown("---")
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.info("📊 **데이터 상세 요약**")
            total_n, ng_n = len(df), len(ng_df)
            m1, m2 = st.columns(2); m1.metric("총 샘플", f"{total_n}개"); m2.metric("불량률", f"{(ng_n/total_n)*100:.1f}%", f"-{ng_n} NG", delta_color="inverse")
            if ng_n == 0: msg = f"✅ **공정 안정:** 모든 샘플 규격 내 존재. 평균 {avg_v:.4f}, 산포 {std_v:.4f}로 우수합니다."
            else: msg = f"🚨 **품질 주의:** {ng_n}개 불량 발생. **No.{worst_idx}({worst_val:.4f})** 점검이 필요합니다."
            st.markdown(f'<div class="summary-box">{msg}</div>', unsafe_allow_html=True)
        with c2: st.metric("평균 (Mean)", f"{avg_v:.4f}", f"σ: {std_v:.4f}")
        with c3: st.metric("Worst Point", f"{worst_val:.4f}" if ng_n > 0 else "N/A", f"Idx: {worst_idx}")
        st.markdown('</div>', unsafe_allow_html=True)
        
# =========================
# 🧮 3. 계산기
# =========================
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 보조 및 MMC 계산기")
    tabs = st.tabs(["🔧 토크 변환","🎯 MMC 보너스", "⚖️ 공차 판정", "📏 단위 변환", "📊 데이터 산포"])
    
    with tabs[0]:
        v, m = st.number_input("수치", key="tv_v41"), st.selectbox("방향", ["N·m → kgf·m", "kgf·m → N·m"], key="tm_v41")
        st.success(f"결과: {v * 0.101972 if 'kgf' in m else v * 9.80665:.4f}")
         
    with tabs[1]:
        mc1, mc2 = st.columns(2)
        m_type = mc1.radio("종류", ["구멍 (Hole)", "축 (Shaft)"], horizontal=True, key="m_t_v41")
        m_geo = mc2.number_input("도면 기하공차", value=0.05, format="%.4f", key="m_g_v41")
        mc3, mc4, mc5 = st.columns(3)
        m_mmc = mc3.number_input("MMC 규격치", value=10.00, format="%.4f", key="m_m_v41")
        m_act = mc4.number_input("실측치", value=10.02 if "구멍" in m_type else 9.98, format="%.4f", key="m_a_v41")
        bonus = max(0.0, m_act - m_mmc if "구멍" in m_type else m_mmc - m_act)
        mc5.metric("최종 허용치", f"{m_geo + bonus:.4f}", f"+{bonus:.4f}")

    with tabs[2]:
        p1, p2, p3, p4 = st.columns(4)
        base, u_t, l_t, ms = p1.number_input("기준", key="cb_v41"), p2.number_input("상한", key="cu_v41"), p3.number_input("하한", key="cl_v41"), p4.number_input("측정", key="cm_v41")
        lo, up = base - abs(l_t), base + abs(u_t)
        if lo <= ms <= up: st.success(f"✅ OK ({lo:.4f} ~ {up:.4f})")
        else: st.error(f"🚨 NG (이탈: {ms-up if ms>up else ms-lo:+.4f})")

   

    with tabs[3]:
        u_i = st.selectbox("항목", ["mm -> inch", "mm -> μm", "kg -> lb"], key="ui_v41")
        u_v = st.number_input("수치", key="uv_v41")
        if "inch" in u_i: res, lab = u_v/25.4, "inch"
        elif "μm" in u_i: res, lab = u_v*1000, "μm"
        else: res, lab = u_v*2.20462, "lb"
        st.info(f"결과: {res:.4f} {lab}")

    with tabs[4]:
        s_t = st.text_area("쉼표 구분 입력", key="st_v41")
        try:
            l = [float(x.strip()) for x in s_t.split(",") if x.strip()]
            if l: st.write(f"평균: {sum(l)/len(l):.4f} | R: {max(l)-min(l):.4f}")
        except: pass
    st.markdown('</div>', unsafe_allow_html=True)
