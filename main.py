import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램 v2.8", layout="wide")

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
# 📈 그래프 분석 (수정 완료)
# =========================
elif menu == "📈 그래프 분석":
    # --- [복구] 템플릿 다운로드 섹션 ---
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📁 분석 준비")
    template_df = pd.DataFrame({"MIN": [10.0], "MAX": [10.5], "VALUE": [10.25]})
    template_out = BytesIO()
    with pd.ExcelWriter(template_out, engine='xlsxwriter') as writer:
        template_df.to_excel(writer, index=False)
    st.download_button("📥 분석용 엑셀 양식 다운로드", template_out.getvalue(), "품질분석_양식.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
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

        # 그래프 시각화
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        fig_plotly = go.Figure()
        fig_plotly.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='측정값', line=dict(color='#1f77b4')))
        fig_plotly.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_plotly.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        if not ng_df.empty:
            fig_plotly.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='NG', marker=dict(color='red', size=10)))
        if df.loc[worst_idx, "편차"] > 0:
            fig_plotly.add_trace(go.Scatter(x=[worst_idx], y=[worst_val], mode='markers', name='Worst', marker=dict(color='rgba(0,0,0,0)', size=25, line=dict(color='red', width=3))))
        st.plotly_chart(fig_plotly, use_container_width=True)
        
        # 다운로드 버튼 (엑셀 & 이미지)
        fig_mpl, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df.index, df["VALUE"], marker='o', color='#1f77b4', alpha=0.7)
        ax.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--')
        ax.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--')
        if not ng_df.empty: ax.scatter(ng_df.index, ng_df["VALUE"], color='red', s=30)
        if df.loc[worst_idx, "편차"] > 0: ax.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=300, linewidths=2)
        img_buf = BytesIO(); fig_mpl.savefig(img_buf, format='png', bbox_inches='tight'); plt.close(fig_mpl)

        c_d1, c_d2 = st.columns(2)
        with c_d1:
            excel_out = BytesIO()
            with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Result')
                workbook, worksheet = writer.book, writer.sheets['Result']
                num_fmt = workbook.add_format({'num_format': '0.0000'})
                red_fmt = workbook.add_format({'bg_color': '#FFCCCC', 'font_color': '#9C0006', 'num_format': '0.0000'})
                for r_n in range(1, len(df) + 1):
                    fmt = red_fmt if df.iloc[r_n-1]["판정"] == "NG" else num_fmt
                    worksheet.set_row(r_n, None, fmt)
                worksheet.set_column('A:E', 13, num_fmt)
                worksheet.insert_image('H2', 'graph.png', {'image_data': img_buf, 'x_scale': 0.65, 'y_scale': 0.65})
            st.download_button("📂 결과 엑셀 다운로드", excel_out.getvalue(), "Result_Report.xlsx", use_container_width=True)
        with c_d2:
            st.download_button("🖼️ 그래프 이미지 다운로드", img_buf.getvalue(), "Result_Graph.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- [복구] 종합분석 리포트 및 NG 행 강조 ---
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📋 종합 분석 리포트")
        # Pandas 스타일링을 사용하여 NG인 경우 행 전체 빨간색 배경 적용
        def highlight_ng(row):
            return ['background-color: #FFCCCC; color: #9C0006' if row["판정"] == "NG" else '' for _ in row]
        
        st.dataframe(df.style.format(subset=["MIN", "MAX", "VALUE", "편차"], formatter="{:.4f}").apply(highlight_ng, axis=1), use_container_width=True)
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info("📊 **데이터 정보**")
            st.metric("샘플수 / NG수", f"{len(df)}개", f"{len(ng_df)}개", delta_color="inverse")
        with c2:
            st.info("📏 **통계 분석**")
            st.metric("측정 평균값", f"{df['VALUE'].mean():.4f}", f"σ: {df['VALUE'].std():.4f}")
        with c3:
            st.info("📍 **Worst Point**")
            st.metric("최대 이탈값", f"{worst_val:.4f}" if df.loc[worst_idx, "편차"] > 0 else "N/A", f"Idx: {worst_idx}")
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 🧮 계산기 (보강 완료)
# =========================
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 보조 계산기")
    tabs = st.tabs(["🔧 토크 변환", "📏 기초 단위 변환", "📊 합계/평균", "⚖️ 공차 판정"])
    
    with tabs[0]:
        st.write("### 토크 단위 상호 변환")
        c_t1, c_t2 = st.columns(2)
        val_t = c_t1.number_input("토크 수치", value=0.0, format="%.4f")
        mode_t = c_t2.selectbox("방향", ["N·m → kgf·m", "kgf·m → N·m"])
        res_t = val_t * 0.101972 if "kgf" in mode_t else val_t * 9.80665
        st.success(f"**결과: {res_t:.4f}**")

    with tabs[1]:
        st.write("### 실무 기초 단위 변환")
        c_u1, c_u2, c_u3 = st.columns([2, 2, 1])
        u_type = c_u1.selectbox("항목", ["길이 (mm/inch)", "무게 (kg/lb)", "압력 (MPa/psi/bar)"])
        val_u = c_u2.number_input("수치", value=0.0, format="%.4f", key="unit_val")
        if "길이" in u_type:
            u_mode = c_u3.selectbox("방향", ["mm → inch", "inch → mm"])
            res_u = val_u / 25.4 if "inch" in u_mode else val_u * 25.4
            unit_label = "inch" if "inch" in u_mode else "mm"
        elif "무게" in u_type:
            u_mode = c_u3.selectbox("방향", ["kg → lb", "lb → kg"])
            res_u = val_u * 2.20462 if "lb" in u_mode else val_u / 2.20462
            unit_label = "lb" if "lb" in u_mode else "kg"
        elif "압력" in u_type:
            u_mode = c_u3.selectbox("방향", ["MPa → psi", "psi → MPa", "MPa → bar", "bar → MPa"])
            if "psi" in u_mode: res_u = val_u * 145.038 if "MPa →" in u_mode else val_u / 145.038
            else: res_u = val_u * 10 if "MPa →" in u_mode else val_u / 10
            unit_label = u_mode.split("→")[1].strip()
        st.info(f"**결과: {res_u:.4f} {unit_label}**")

    with tabs[2]:
        txt = st.text_area("숫자 입력 (쉼표 구분)", "10, 20.5")
        try:
            v_list = [float(x.strip()) for x in txt.split(",") if x.strip()]
            if v_list: st.info(f"합계: {sum(v_list):.4f} | 평균: {sum(v_list)/len(v_list):.4f}")
        except: st.error("숫자만 입력하세요.")

    with tabs[3]:
        cc1, cc2, cc3, cc4 = st.columns(4)
        tar, ut, lt, ms = cc1.number_input("기준"), cc2.number_input("상한(+)"), cc3.number_input("하한(-)"), cc4.number_input("측정")
        mi, ma = tar - abs(lt), tar + abs(ut)
        if mi <= ms <= ma: st.success(f"**OK** ({mi:.4f} ~ {ma:.4f})")
        else: st.error(f"**NG** (이탈: {ms-ma if ms>ma else ms-mi:.4f})")
    st.markdown('</div>', unsafe_allow_html=True)
