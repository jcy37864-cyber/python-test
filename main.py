import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램 v2.3", layout="wide")

# 2. 그래프 설정
plt.rcParams['axes.unicode_minus'] = False
plt.rc('font', family='sans-serif') 

# 3. 사이드바 스타일
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0E1117; }
[data-testid="stSidebar"] * { color: white; }
</style>
""", unsafe_allow_html=True)

st.title("📊 품질 측정 통합 프로그램")

menu = st.sidebar.radio("메뉴 선택", ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"])

# =========================
# 🔄 ZXY 변환 (기능 유지)
# =========================
if menu == "🔄 ZXY 변환":
    st.subheader("🔄 ZXY 데이터 변환")
    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({"X": [""] * 100, "Y": [""] * 100, "Z": [""] * 100})
    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic")
    if st.button("ZXY 결과 생성"):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row["X"]).strip(), str(row["Y"]).strip(), str(row["Z"]).strip()
            if x and y and z: results.extend([z, x, y])
        if results:
            result_df = pd.DataFrame(results, columns=["변환 결과"])
            st.dataframe(result_df, use_container_width=True)
            st.download_button("📂 CSV 다운로드", result_df.to_csv(index=False).encode("utf-8-sig"), "zxy_result.csv")

# =========================
# 📈 그래프 분석 (이미지 다운로드 추가)
# =========================
elif menu == "📈 그래프 분석":
    st.subheader("📈 품질 그래프 분석")
    uploaded_file = st.file_uploader("파일 업로드", type=["xlsx", "csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df = df.round(4)
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1).round(4)
        
        worst_idx = df["편차"].idxmax()
        worst_val = df.loc[worst_idx, "VALUE"]

        # --- 1. 화면용 Plotly 그래프 (Worst 원 강조 포함) ---
        st.markdown("#### 🔍 대화형 추이 분석")
        fig_plotly = go.Figure()
        fig_plotly.add_trace(go.Scatter(
            x=df.index, y=df["VALUE"], mode='lines+markers', name='측정값',
            text=[f"샘플: {i}<br>판정: {p}" for i, p in zip(df.index, df["판정"])],
            hovertemplate="<b>%{text}</b><br>수치: %{y:.4f}<extra></extra>",
            line=dict(color='#1f77b4', width=2)
        ))
        fig_plotly.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_plotly.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        
        ng_df = df[df["판정"] == "NG"]
        if not ng_df.empty:
            fig_plotly.add_trace(go.Scatter(
                x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='불량(NG)',
                marker=dict(color='red', size=10)
            ))
        if df.loc[worst_idx, "편차"] > 0:
            fig_plotly.add_trace(go.Scatter(
                x=[worst_idx], y=[worst_val], mode='markers', name='Worst Point',
                marker=dict(color='rgba(0,0,0,0)', size=25, line=dict(color='red', width=3)),
                showlegend=True
            ))
        fig_plotly.update_layout(hovermode="closest", template="plotly_white", margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_plotly, use_container_width=True)

        # --- 2. 다운로드용 고해상도 Matplotlib 그래프 생성 ---
        fig_mpl, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df.index, df["VALUE"], marker='o', markersize=5, color='#1f77b4', label="Value", alpha=0.8)
        ax.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--', label="MAX")
        ax.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--', label="MIN")
        
        if not ng_df.empty:
            ax.scatter(ng_df.index, ng_df["VALUE"], color='red', s=40, zorder=5, label="NG")
        
        if df.loc[worst_idx, "편차"] > 0:
            ax.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=400, linewidths=2.5, zorder=6, label="Worst")
        
        ax.set_title("Quality Analysis Report Image")
        ax.set_xlabel("Sample Index")
        ax.set_ylabel("Value")
        ax.legend(loc='upper right')
        ax.grid(True, linestyle=':', alpha=0.5)
        
        # 이미지 버퍼 저장 (PNG)
        img_buffer = BytesIO()
        fig_mpl.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig_mpl)

        # --- 3. 다운로드 버튼 섹션 (엑셀 & 이미지) ---
        col_down1, col_down2 = st.columns(2)
        
        # 엑셀 다운로드 (NG 색상 및 이미지 포함)
        with col_down1:
            excel_out = BytesIO()
            with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Result')
                workbook, worksheet = writer.book, writer.sheets['Result']
                num_fmt = workbook.add_format({'num_format': '0.0000'})
                red_fmt = workbook.add_format({'bg_color': '#FFCCCC', 'font_color': '#9C0006', 'num_format': '0.0000'})
                for row_num in range(1, len(df) + 1):
                    fmt = red_fmt if df.iloc[row_num-1]["판정"] == "NG" else num_fmt
                    worksheet.set_row(row_num, None, fmt)
                worksheet.set_column('A:E', 12, num_fmt)
                worksheet.insert_image('H2', 'graph.png', {'image_data': img_buffer, 'x_scale': 0.65, 'y_scale': 0.65})
            st.download_button("📂 결과 엑셀 다운로드", excel_out.getvalue(), "quality_report.xlsx", use_container_width=True)

        # 이미지 개별 다운로드 (새로 추가)
        with col_down2:
            st.download_button("🖼️ 그래프 이미지 다운로드 (PNG)", img_buffer.getvalue(), "quality_graph.png", use_container_width=True)

        # --- 4. 데이터 테이블 & 요약 ---
        st.markdown("---")
        st.dataframe(df.style.format(subset=["MIN", "MAX", "VALUE", "편차"], formatter="{:.4f}").apply(
            lambda row: ['background-color: #ffcccc' if row["판정"] == "NG" else '' for _ in row], axis=1), use_container_width=True)

        col_sum1, col_sum2 = st.columns(2)
        with col_sum1:
            st.markdown("### 📋 검사 요약")
            avg_v = df["VALUE"].mean()
            st.write(f"• 전체: {len(df)} / 불량: {len(ng_df)}")
            if len(ng_df) == 0: st.success(f"✅ 모든 데이터 합격 (평균: {avg_v:.4f})")
            else: st.error(f"🚨 규격 이탈 발생 (평균: {avg_v:.4f})")
        with col_sum2:
            st.markdown("### 📍 Worst 상세")
            if df.loc[worst_idx, "편차"] > 0:
                st.error(f"**최대 편차: {worst_val:.4f}** (샘플 {worst_idx})")
                st.write(f"규격 대비 이탈량: {df.loc[worst_idx, '편차']:.4f}")
            else: st.info("✅ 특이사항 없음")

# =========================
# 🧮 계산기 (기능 유지)
# =========================
elif menu == "🧮 계산기":
    st.subheader("🧮 품질 보조 계산기")
    calc = st.selectbox("기능 선택", ["토크 변환", "합계/평균", "공차 판정"])
    if calc == "공차 판정":
        c1, c2, c3, c4 = st.columns(4)
        target = c1.number_input("기준값", 0.0, format="%.4f")
        u_tol = c2.number_input("상한(+)", 0.0, format="%.4f")
        l_tol = c3.number_input("하한(-)", 0.0, format="%.4f")
        meas = c4.number_input("측정값", 0.0, format="%.4f")
        mi, ma = target - abs(l_tol), target + abs(u_tol)
        if mi <= meas <= ma: st.success(f"### OK ✅ ({mi:.4f} ~ {ma:.4f})")
        else: 
            diff = meas - ma if meas > ma else meas - mi
            st.error(f"### NG 🚨 (이탈: {diff:.4f})")
