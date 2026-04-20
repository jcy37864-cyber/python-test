import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 시스템 v4.3", layout="wide")

# 2. 커스텀 CSS (기업용 프리미엄 디자인 강화)
st.markdown("""
    <style>
    /* 메인 배경 및 폰트 */
    .main { background-color: #f4f7f9; }
    
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] { 
        background-color: #1e293b !important; 
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    
    /* 사이드바 버튼 글자색 강제 지정 */
    [data-testid="stSidebar"] button p {
        color: #FFFFFF !important;
        font-weight: bold;
    }
    
    /* 사이드바 리셋 버튼 전용 스타일 */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #ef4444 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
    }

    /* 카드형 박스 디자인 (Shadow & Radius) */
    .stBox {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        margin-bottom: 24px;
    }
    
    /* 상단 요약 카드 (Metric Card) 커스텀 */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* 하단 요약 알림창 */
    .summary-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #3b82f6;
        color: #1e293b !important;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* 탭 메뉴 스타일 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #f1f5f9;
        border-radius: 8px 8px 0 0;
        padding: 0 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

plt.rcParams['axes.unicode_minus'] = False
plt.rc('font', family='sans-serif') 

st.title("📊 품질 측정 통합 시스템")

# =========================
# 🛠️ 사이드바 메뉴 및 가이드
# =========================
st.sidebar.title("🚀 주요 기능")
menu = st.sidebar.radio("📋 메뉴 선택", ["🔄 데이터 변환기", "📈 그래프 분석", "🧮 계산기"])

st.sidebar.markdown("---")

if menu == "🔄 데이터 변환기":
    st.sidebar.info("**🔄 데이터 변환기**\n\nZXY 등 다양한 측정 좌표를 표준 순서로 재배열합니다. 결과 No.는 1번부터 시작됩니다.")
elif menu == "📈 그래프 분석":
    st.sidebar.info("**📈 그래프 분석**\n\n추세 점그래프와 정밀 막대그래프를 제공하며, 엑셀 보고서 추출이 가능합니다.")
elif menu == "🧮 계산기":
    st.sidebar.info("**🧮 품질 계산기**\n\nMMC 보너스 공차 계산, 정밀 공차 판정, 단위 변환 등 실무 수식을 제공합니다.")

st.sidebar.markdown("---")
if st.sidebar.button("🧹 데이터 초기화 (Reset)", use_container_width=True):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# =========================
# 🔄 1. 데이터 변환 코너 (확장형)
# =========================
if menu == "🔄 데이터 변환기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🔄 데이터 형식 변환기")
    
    convert_mode = st.selectbox(
        "📝 변환 방식을 선택하세요", 
        ["ZXY 변환 (표준)", "XYZ 변환 (추가 예정)", "사용자 정의 (추가 예정)"],
        index=0
    )
    
    st.markdown("---")

    if convert_mode == "ZXY 변환 (표준)":
        st.write("📌 **Z → X → Y** 순서로 데이터를 재배열합니다.")
        if "df_zxy" not in st.session_state:
            st.session_state.df_zxy = pd.DataFrame({"X": [""] * 100, "Y": [""] * 100, "Z": [""] * 100})
        
        edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic", key="editor_zxy_v43")
        
        if st.button("🚀 ZXY 결과 생성", use_container_width=True):
            results = []
            for _, row in edited_df.iterrows():
                x, y, z = str(row["X"]).strip(), str(row["Y"]).strip(), str(row["Z"]).strip()
                if x and y and z: results.extend([z, x, y])
            
            if results:
                result_df = pd.DataFrame(results, columns=["변환 결과"])
                result_df.index = result_df.index + 1
                st.success(f"✅ 총 {len(results)}개의 데이터가 변환되었습니다.")
                st.dataframe(result_df, use_container_width=True, height=300)
                
                st.markdown("### 📋 간편 복사 영역")
                st.text_area("드래그하여 전체 복사가 가능합니다.", "\n".join(map(str, results)), height=150)
                st.download_button("📂 CSV 다운로드", result_df.to_csv(index=True).encode("utf-8-sig"), "zxy_result.csv")
    else:
        st.info("💡 선택하신 변환 로직을 준비 중입니다.")
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 📈 2. 그래프 분석 (디자인 강화 버전)
# =========================
elif menu == "📈 그래프 분석":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📁 분석 파일 업로드")
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

        # [그래프 시각화 박스]
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📈 측정 추세 분석 (Line)")
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='측정값',
                                   hovertemplate='No: %{x}<br>Value: %{y:.4f}<extra></extra>'))
        fig_p.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_p.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        if not ng_df.empty:
            fig_p.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='NG', marker=dict(color='red', size=10)))
        if df.loc[worst_idx, "편차"] > 0:
            fig_p.add_trace(go.Scatter(x=[worst_idx], y=[worst_val], mode='markers', name='Worst', 
                                        marker=dict(color='rgba(0,0,0,0)', size=20, line=dict(color='red', width=3))))
        fig_p.update_layout(hoverlabel=dict(bgcolor="black", font_size=20, font_color="white"))
        st.plotly_chart(fig_p, use_container_width=True)

        st.subheader("📊 샘플별 수치 비교 (Bar)")
        y_min, y_max = min(df["VALUE"].min(), df["MIN"].min()) * 0.999, max(df["VALUE"].max(), df["MAX"].max()) * 1.001
        colors = ['#FF4B4B' if p == "NG" else '#3b82f6' for p in df["판정"]]
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(x=df.index, y=df["VALUE"], marker_color=colors, text=df["VALUE"], textposition='outside',
                               hovertemplate='No: %{x}<br>Value: %{y:.4f}<extra></extra>'))
        fig_b.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green")
        fig_b.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange")
        fig_b.update_layout(yaxis_range=[y_min, y_max], hoverlabel=dict(bgcolor="darkblue", font_size=20), showlegend=False)
        st.plotly_chart(fig_b, use_container_width=True)

        st.subheader("🎯 데이터 분포 (Histogram)")
        fig_h = go.Figure()
        fig_h.add_trace(go.Histogram(x=df["VALUE"], nbinsx=15, marker_color='#64748b', opacity=0.7))
        fig_h.update_layout(xaxis_title="측정값", yaxis_title="빈도수", hoverlabel=dict(font_size=18))
        st.plotly_chart(fig_h, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [전문 대시보드 요약 박스]
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📊 품질 분석 대시보드")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 전체 샘플", f"{len(df)} EA")
        c2.metric("✅ 합격 (OK)", f"{len(df)-len(ng_df)} EA", delta=f"{((len(df)-len(ng_df))/len(df))*100:.1,f}%")
        c3.metric("🚨 불량 (NG)", f"{len(ng_df)} EA", delta=f"-{len(ng_df)}", delta_color="inverse")
        c4.metric("🎯 Worst Point", f"{worst_val:.3f}", f"Idx: {worst_idx}")

        st.markdown("---")
        if len(ng_df) == 0:
            st.markdown(f'<div class="summary-box" style="border-left-color: #10b981;"><h4 style="color:#065f46;">✅ 공정 상태 양호</h4>모든 데이터가 규격 내에 있습니다. 평균 <b>{avg_v:.4f}</b>로 안정적입니다.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="summary-box" style="border-left-color: #ef4444;"><h4 style="color:#991b1b;">🚨 품질 경보</h4>{len(ng_df)}개의 불량 확인. <b>No.{worst_idx}({worst_val:.4f})</b>를 집중 점검하세요.</div>', unsafe_allow_html=True)

        # 엑셀 보고서 생성 로직 (이미지 삽입 포함)
        fig_mpl1, ax1 = plt.subplots(figsize=(10, 4))
        ax1.plot(df.index, df["VALUE"], marker='o', color='#3b82f6'); ax1.axhline(y=df["MAX"].iloc[0], color='g', ls='--'); ax1.axhline(y=df["MIN"].iloc[0], color='orange', ls='--')
        if not ng_df.empty: ax1.scatter(ng_df.index, ng_df["VALUE"], color='red', s=40)
        if df.loc[worst_idx, "편차"] > 0: ax1.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=300, lw=2)
        img_line = BytesIO(); fig_mpl1.savefig(img_line, format='png'); plt.close(fig_mpl1)

        fig_mpl2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.bar(df.index, df["VALUE"], color=['red' if p == "NG" else '#3b82f6' for p in df["판정"]]); ax2.set_ylim(y_min, y_max)
        img_bar = BytesIO(); fig_mpl2.savefig(img_bar, format='png'); plt.close(fig_mpl2)

        excel_buf = BytesIO()
        with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
            workbook, worksheet = writer.book, writer.sheets['Report']
            worksheet.insert_image('H2', 'line.png', {'image_data': img_line, 'x_scale': 0.5, 'y_scale': 0.5})
            worksheet.insert_image('H22', 'bar.png', {'image_data': img_bar, 'x_scale': 0.5, 'y_scale': 0.5})
        
        st.markdown("<br>", unsafe_allow_html=True)
        dc1, dc2 = st.columns(2)
        dc1.download_button("📂 정밀 분석 엑셀 보고서 출력", excel_buf.getvalue(), "Quality_Report.xlsx", use_container_width=True)
        dc2.download_button("🖼️ 메인 그래프 이미지 저장", img_line.getvalue(), "Trend_Graph.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 🧮 3. 계산기
# =========================
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 보조 및 MMC 계산기")
    tabs = st.tabs(["🎯 MMC 보너스", "⚖️ 공차 판정", "🔧 토크 변환", "📏 단위 변환", "📊 데이터 산포"])
    
    with tabs[0]:
        mc1, mc2 = st.columns(2)
        m_type = mc1.radio("종류", ["구멍 (Hole)", "축 (Shaft)"], horizontal=True, key="m_t_v43")
        m_geo = mc2.number_input("도면 기하공차", value=0.05, format="%.4f", key="m_g_v43")
        mc3, mc4, mc5 = st.columns(3)
        m_mmc = mc3.number_input("MMC 규격치", value=10.00, format="%.4f", key="m_m_v43")
        m_act = mc4.number_input("실측치", value=10.02 if "구멍" in m_type else 9.98, format="%.4f", key="m_a_v43")
        bonus = max(0.0, m_act - m_mmc if "구멍" in m_type else m_mmc - m_act)
        mc5.metric("최종 허용치", f"{m_geo + bonus:.4f}", f"+{bonus:.4f}")

    with tabs[1]:
        p1, p2, p3, p4 = st.columns(4)
        base, u_t, l_t, ms = p1.number_input("기준", key="cb_v43"), p2.number_input("상한", key="cu_v43"), p3.number_input("하한", key="cl_v43"), p4.number_input("측정", key="cm_v43")
        lo, up = base - abs(l_t), base + abs(u_t)
        if lo <= ms <= up: st.success(f"✅ OK ({lo:.4f} ~ {up:.4f})")
        else: st.error(f"🚨 NG (이탈: {ms-up if ms>up else ms-lo:+.4f})")

    with tabs[2]:
        v, m = st.number_input("수치", key="tv_v43"), st.selectbox("방향", ["N·m → kgf·m", "kgf·m → N·m"], key="tm_v43")
        st.success(f"결과: {v * 0.101972 if 'kgf' in m else v * 9.80665:.4f}")

    with tabs[3]:
        u_i = st.selectbox("항목", ["mm/inch", "mm/μm", "kg/lb"], key="ui_v43")
        u_v = st.number_input("수치", key="uv_v43")
        if "inch" in u_i: res, lab = u_v/25.4, "inch"
        elif "μm" in u_i: res, lab = u_v*1000, "μm"
        else: res, lab = u_v*2.20462, "lb"
        st.info(f"결과: {res:.4f} {lab}")

    with tabs[4]:
        s_t = st.text_area("쉼표 구분 입력", key="st_v43")
        try:
            l = [float(x.strip()) for x in s_t.split(",") if x.strip()]
            if l: st.write(f"평균: {sum(l)/len(l):.4f} | R: {max(l)-min(l):.4f}")
        except: pass
    st.markdown('</div>', unsafe_allow_html=True)
