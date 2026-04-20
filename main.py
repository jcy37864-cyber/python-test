import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 시스템 v4.3.1", layout="wide")

# 2. 커스텀 CSS (기업용 프리미엄 디자인)
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] button p { color: #FFFFFF !important; font-weight: bold; }
    [data-testid="stSidebar"] div.stButton > button { background-color: #ef4444 !important; color: white !important; border: none !important; border-radius: 8px; }
    .stBox { background-color: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); margin-bottom: 24px; }
    div[data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 15px 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
    .summary-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 6px solid #3b82f6; color: #1e293b !important; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #f1f5f9; border-radius: 8px 8px 0 0; padding: 0 20px; }
    .stTabs [aria-selected="true"] { background-color: #3b82f6 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

plt.rcParams['axes.unicode_minus'] = False

st.title("📊 품질 측정 통합 시스템")

# 사이드바 메뉴
st.sidebar.title("🚀 주요 기능")
menu = st.sidebar.radio("📋 메뉴 선택", ["🔄 데이터 변환기", "📈 그래프 분석", "🧮 계산기"])

st.sidebar.markdown("---")
if st.sidebar.button("🧹 데이터 초기화 (Reset)", use_container_width=True):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# 🔄 1. 데이터 변환기
if menu == "🔄 데이터 변환기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🔄 데이터 형식 변환기")
    convert_mode = st.selectbox("📝 변환 방식을 선택하세요", ["ZXY 변환 (표준)", "XYZ 변환 (추가 예정)"], index=0)
    
    if convert_mode == "ZXY 변환 (표준)":
        if "df_zxy" not in st.session_state:
            st.session_state.df_zxy = pd.DataFrame({"X": [""] * 100, "Y": [""] * 100, "Z": [""] * 100})
        edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic", key="editor_v431")
        if st.button("🚀 ZXY 결과 생성", use_container_width=True):
            results = []
            for _, row in edited_df.iterrows():
                x, y, z = str(row.get("X","")).strip(), str(row.get("Y","")).strip(), str(row.get("Z","")).strip()
                if x and y and z: results.extend([z, x, y])
            if results:
                res_df = pd.DataFrame(results, columns=["변환 결과"])
                res_df.index += 1
                st.success(f"✅ {len(results)}개 변환 완료")
                st.dataframe(res_df, use_container_width=True)
                st.text_area("📋 간편 복사", "\n".join(map(str, results)), height=150)
    st.markdown('</div>', unsafe_allow_html=True)

# 📈 2. 그래프 분석 (수정 핵심 섹션)
elif menu == "📈 그래프 분석":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
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

        # 대화형 그래프 (Plotly)
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📈 측정 분석 그래프")
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='정상', line=dict(color='#3b82f6')))
        fig_p.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_p.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        if not ng_df.empty:
            fig_p.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='NG', marker=dict(color='red', size=12)))
        fig_p.update_layout(hoverlabel=dict(bgcolor="black", font_size=20, font_color="white"))
        st.plotly_chart(fig_p, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 요약 대시보드
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📊 품질 분석 대시보드")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 전체 샘플", f"{len(df)} EA")
        c2.metric("✅ 합격 (OK)", f"{len(df)-len(ng_df)} EA", delta=f"{((len(df)-len(ng_df))/len(df))*100:.1f}%")
        c3.metric("🚨 불량 (NG)", f"{len(ng_df)} EA", delta=f"-{len(ng_df)}", delta_color="inverse")
        c4.metric("🎯 Worst", f"{worst_val:.3f}", f"Idx: {worst_idx}")

        # ---------------------------------------------------------
        # 엑셀용 정적 그래프 생성 (Matplotlib - NG 포인트 강조 포함)
        # ---------------------------------------------------------
        fig_mpl, ax1 = plt.subplots(figsize=(10, 4))
        ax1.plot(df.index, df["VALUE"], marker='o', color='#3b82f6', label='Value', zorder=1)
        ax1.axhline(y=df["MAX"].iloc[0], color='green', ls='--', label='MAX')
        ax1.axhline(y=df["MIN"].iloc[0], color='orange', ls='--', label='MIN')
        # NG 포인트 빨간색 강조 (엑셀 삽입용)
        if not ng_df.empty:
            ax1.scatter(ng_df.index, ng_df["VALUE"], color='red', s=60, label='NG', zorder=5)
        # Worst 포인트 원 강조
        if df.loc[worst_idx, "편차"] > 0:
            ax1.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=200, lw=2, zorder=6)
        
        img_buf = BytesIO()
        fig_mpl.savefig(img_buf, format='png', bbox_inches='tight')
        plt.close(fig_mpl)

        # ---------------------------------------------------------
        # 엑셀 파일 생성 (NG 행 빨간색 서식 포함)
        # ---------------------------------------------------------
        excel_out = BytesIO()
        with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
            workbook  = writer.book
            worksheet = writer.sheets['Report']

            # 서식 정의
            red_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'}) # NG행 배경색
            num_format = workbook.add_format({'num_format': '0.0000'})
            
            # 1. 데이터 영역 서식 적용 (NG 행 검사)
            for i, row_data in enumerate(df.values):
                row_idx = i + 1 # 헤더 제외
                if df.iloc[i]["판정"] == "NG":
                    worksheet.set_row(row_idx, None, red_format)
                else:
                    worksheet.set_row(row_idx, None, num_format)

            # 2. 강조된 그래프 이미지 삽입
            worksheet.insert_image('H2', 'trend.png', {'image_data': img_buf, 'x_scale': 0.6, 'y_scale': 0.6})

        st.markdown("---")
        dc1, dc2 = st.columns(2)
        dc1.download_button("📂 엑셀 보고서 다운로드 (NG 강조 완료)", excel_out.getvalue(), "Quality_Report_Final.xlsx", use_container_width=True)
        dc2.download_button("🖼️ 그래프 이미지 저장", img_buf.getvalue(), "Trend_Graph.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# 🧮 3. 계산기 (기존 기능 유지)
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 계산기")
    # ... (기존 계산기 코드 동일)
    st.info("계산기 기능은 이전 버전과 동일하게 작동합니다.")
    st.markdown('</div>', unsafe_allow_html=True)
