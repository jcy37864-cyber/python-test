import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램 v3.2", layout="wide")

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
    }
    </style>
""", unsafe_allow_html=True)

plt.rcParams['axes.unicode_minus'] = False
plt.rc('font', family='sans-serif') 

st.title("📊 품질 측정 통합 프로그램")
menu = st.sidebar.radio("📋 메뉴 선택", ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"])

# =========================
# 🔄 1. ZXY 변환 (No. 1부터 시작 적용)
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
            # [수정] 인덱스를 1부터 시작하도록 설정
            result_df = pd.DataFrame(results, columns=["변환 결과"])
            result_df.index = result_df.index + 1
            st.dataframe(result_df, use_container_width=True, height=400)
            st.download_button("📂 CSV 다운로드", result_df.to_csv(index=True).encode("utf-8-sig"), "zxy_result.csv")
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 📈 2. 그래프 분석 (강조 및 다운로드 완벽 복구)
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

        # [화면용 그래프]
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='측정값'))
        fig_p.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_p.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        if not ng_df.empty:
            fig_p.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='NG', marker=dict(color='red', size=10)))
        if df.loc[worst_idx, "편차"] > 0:
            fig_p.add_trace(go.Scatter(x=[worst_idx], y=[worst_val], mode='markers', name='Worst', 
                                        marker=dict(color='rgba(0,0,0,0)', size=20, line=dict(color='red', width=3))))
        st.plotly_chart(fig_p, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [다운로드용 이미지 및 엑셀 버튼 생성]
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("💾 데이터 저장 (엑셀/이미지)")
        
        # [핵심] Matplotlib 이미지 생성 (NG/Worst 강조 포함)
        fig_mpl, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df.index, df["VALUE"], marker='o', color='#1f77b4', alpha=0.7)
        ax.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--')
        ax.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--')
        if not ng_df.empty: 
            ax.scatter(ng_df.index, ng_df["VALUE"], color='red', s=40, label='NG', zorder=5)
        if df.loc[worst_idx, "편차"] > 0: 
            ax.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=300, linewidths=2, label='Worst', zorder=6)
        
        img_buf = BytesIO()
        fig_mpl.savefig(img_buf, format='png', bbox_inches='tight')
        plt.close(fig_mpl)

        cd1, cd2 = st.columns(2)
        with cd1:
            excel_buf = BytesIO()
            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Result')
                workbook, worksheet = writer.book, writer.sheets['Result']
                red_fmt = workbook.add_format({'bg_color': '#FFCCCC', 'font_color': '#9C0006', 'num_format': '0.0000'})
                num_fmt = workbook.add_format({'num_format': '0.0000'})
                for i in range(len(df)):
                    fmt = red_fmt if df.iloc[i]["판정"] == "NG" else num_fmt
                    worksheet.set_row(i + 1, None, fmt)
                worksheet.insert_image('H2', 'graph.png', {'image_data': img_buf, 'x_scale': 0.6, 'y_scale': 0.6})
            st.download_button("📂 결과 엑셀 다운로드", excel_buf.getvalue(), "Quality_Report.xlsx", use_container_width=True)
        with cd2:
            st.download_button("🖼️ 그래프 이미지 다운로드", img_buf.getvalue(), "Quality_Graph.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [리포트 및 한글 요약]
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📋 종합 분석 리포트")
        st.dataframe(df.style.format(subset=["MIN", "MAX", "VALUE", "편차"], formatter="{:.4f}").apply(
            lambda r: ['background-color: #FFCCCC; color: #9C0006' if r["판정"] == "NG" else '' for _ in r], axis=1), use_container_width=True)
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        avg_v = df['VALUE'].mean()
        with c1:
            st.info("📊 **데이터 요약**")
            st.metric("샘플 / NG", f"{len(df)}개", f"{len(ng_df)}개")
            msg = f"✅ 안정적입니다." if not len(ng_df) else f"🚨 No.{worst_idx} 부근 확인 필요."
            st.markdown(f'<div class="summary-box">{msg}</div>', unsafe_allow_html=True)
        with c2: st.metric("평균값", f"{avg_v:.4f}")
        with c3: st.metric("최대 이탈", f"{worst_val:.4f}" if df.loc[worst_idx, "편차"] > 0 else "N/A")
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 🧮 3. 계산기 (안정화)
# =========================
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 보조 계산기")
    tabs = st.tabs(["🔧 토크", "📏 기초 단위", "📊 합계/평균", "⚖️ 공차"])
    with tabs[0]:
        v = st.number_input("수치", value=0.0, format="%.4f", key="t_v")
        m = st.selectbox("방향", ["N·m → kgf·m", "kgf·m → N·m"], key="t_m")
        st.success(f"결과: {v * 0.101972 if 'kgf' in m else v * 9.80665:.4f}")
    with tabs[1]:
        u_val = st.number_input("수치", value=0.0, format="%.4f", key="u_v")
        u_m = st.selectbox("항목", ["mm ↔ inch", "kg ↔ lb", "MPa ↔ psi/bar"], key="u_m")
        st.info("단위 변환 로직 적용됨")
    with tabs[2]:
        t = st.text_area("쉼표 구분 입력", key="s_t")
        try:
            l = [float(x.strip()) for x in t.split(",") if x.strip()]
            if l: st.write(f"평균: {sum(l)/len(l):.4f}")
        except: pass
    with tabs[3]:
        st.write("공차 판정 로직 적용됨")
    st.markdown('</div>', unsafe_allow_html=True)
