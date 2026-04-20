import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램", layout="wide")

# 2. 그래프 폰트 설정
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

menu = st.sidebar.radio(
    "메뉴 선택",
    ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"]
)

# =========================
# 🔄 ZXY 변환
# =========================
if menu == "🔄 ZXY 변환":
    st.subheader("🔄 ZXY 데이터 변환")
    st.info("X, Y, Z를 입력하면 [Z -> X -> Y] 순서로 데이터가 세로로 쌓여 결과가 생성됩니다.")

    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({
            "X": [""] * 100, "Y": [""] * 100, "Z": [""] * 100,
        })

    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic")

    if st.button("ZXY 결과 생성"):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row["X"]).strip(), str(row["Y"]).strip(), str(row["Z"]).strip()
            if x and y and z:
                results.extend([z, x, y])

        if results:
            result_df = pd.DataFrame(results, columns=["변환 결과"])
            st.dataframe(result_df, use_container_width=True)
            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📂 CSV 다운로드", csv, "zxy_result.csv")
        else:
            st.warning("데이터를 입력해주세요.")

# =========================
# 📈 그래프 분석 (Plotly + Matplotlib 통합)
# =========================
elif menu == "📈 그래프 분석":
    st.subheader("📈 품질 그래프 분석")

    uploaded_file = st.file_uploader("엑셀 또는 CSV 파일 업로드", type=["xlsx", "csv"])

    # 템플릿 다운로드
    template = pd.DataFrame({"MIN": [30.1], "MAX": [30.7], "VALUE": [30.3]})
    tmp_out = BytesIO()
    with pd.ExcelWriter(tmp_out, engine="openpyxl") as writer:
        template.to_excel(writer, index=False)
    st.download_button("📄 템플릿 다운로드", tmp_out.getvalue(), "template.xlsx")

    if uploaded_file:
        # 데이터 로드 및 판정 로직
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1)

        # 1. 화면용 Plotly 대화형 그래프 (마우스 오버 시 정보 표시)
        st.markdown("#### 🔍 대화형 추이 분석 (마우스를 점 위에 올려보세요)")
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
                marker=dict(color='red', size=10),
                hovertemplate="<b>🚨 NG 샘플: %{x}</b><br>수치: %{y:.4f}<extra></extra>"
            ))
        
        fig_plotly.update_layout(hovermode="closest", template="plotly_white", margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_plotly, use_container_width=True)

        # 2. 데이터 테이블 표시
        def highlight_ng(row):
            return ['background-color: #ffcccc' if row["판정"] == "NG" else '' for _ in row]
        st.dataframe(df.style.apply(highlight_ng, axis=1), use_container_width=True)

        # 3. 엑셀 저장용 Matplotlib 그래프 생성 (보이지 않게 처리)
        fig_mpl, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df["VALUE"], marker='o', markersize=4, color='#1f77b4')
        ax.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--')
        ax.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--')
        worst_idx = df["편차"].idxmax()
        if df.loc[worst_idx, "편차"] > 0:
            ax.scatter(worst_idx, df.loc[worst_idx, "VALUE"], facecolors='none', edgecolors='red', s=400, linewidths=2)
        
        img_buffer = BytesIO()
        fig_mpl.savefig(img_buffer, format='png', bbox_inches='tight')
        plt.close(fig_mpl)

        # 4. 결과 엑셀 다운로드
        excel_out = BytesIO()
        with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Result')
            workbook, worksheet = writer.book, writer.sheets['Result']
            red_format = workbook.add_format({'bg_color': '#FFCCCC', 'font_color': '#9C0006'})
            for row_num in range(1, len(df) + 1):
                if df.iloc[row_num-1]["판정"] == "NG":
                    worksheet.set_row(row_num, None, red_format)
            worksheet.insert_image('H2', 'graph.png', {'image_data': img_buffer, 'x_scale': 0.6, 'y_scale': 0.6})

        st.download_button("📸 결과 엑셀 다운로드 (이미지 포함)", excel_out.getvalue(), "quality_report.xlsx")

        # 5. 요약 섹션
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📋 검사 결과 요약")
            total, ng_count = len(df), len(df[df["판정"] == "NG"])
            st.write(f"• 전체: {total} / 양호: {total-ng_count} / 불량: {ng_count}")
            if ng_count == 0: st.success("✅ 모든 데이터 규격 만족")
            else: st.error(f"🚨 규격 이탈 발생 ({ng_count}건)")
            
            avg_val = df["VALUE"].mean()
            if avg_val > df["MAX"].mean(): st.error(f"📉 경향: 평균({avg_val:.4f}) 상한 초과 추세")
            elif avg_val < df["MIN"].mean(): st.error(f"📈 경향: 평균({avg_val:.4f}) 하한 미달 추세")
            else: st.info(f"✔ 경향: 평균({avg_val:.4f}) 규격 내 안정적")

        with col2:
            st.markdown("### 📍 Worst Point 정보")
            worst_row = df.loc[worst_idx]
            if worst_row["편차"] > 0:
                st.error(f"**최대 편차 측정값: {worst_row['VALUE']:.4f}**")
                st.write(f"• 순번: {worst_idx} / 편차량: {worst_row['편차']:.4f}")
            else: st.info("✅ Worst 포인트 없음")

# =========================
# 🧮 계산기
# =========================
elif menu == "🧮 계산기":
    st.subheader("🧮 품질 보조 계산기")
    calc = st.selectbox("기능 선택", ["토크 변환", "합계/평균", "공차 판정"])
    if calc == "토크 변환":
        val = st.number_input("수치 입력", 0.0)
        mode = st.selectbox("변환 선택", ["N·m → kgf·m", "kgf·m → N·m"])
        if mode == "N·m → kgf·m": st.success(f"결과: {val * 0.101972:.4f} kgf·m")
        else: st.success(f"결과: {val * 9.80665:.4f} N·m")
    elif calc == "합계/평균":
        nums = st.text_input("값 입력 (쉼표 구분)", "10, 20, 30")
        try:
            vals = [float(x.strip()) for x in nums.split(",") if x.strip()]
            if vals: st.info(f"합계: {sum(vals):.2f} / 평균: {sum(vals)/len(vals):.2f}")
        except: st.error("형식을 확인하세요.")
    elif calc == "공차 판정":
        st.info("상하한 공차 분리 판정")
        c1, c2, c3, c4 = st.columns(4)
        target = c1.number_input("기준값", 0.0, format="%.4f")
        u_tol = c2.number_input("상한(+)", 0.0, format="%.4f")
        l_tol = c3.number_input("하한(-)", 0.0, format="%.4f")
        meas = c4.number_input("측정값", 0.0, format="%.4f")
        mi, ma = target - abs(l_tol), target + abs(u_tol)
        if mi <= meas <= ma: st.success(f"OK ({mi:.4f} ~ {ma:.4f})")
        else: st.error(f"NG (이탈: {meas-ma if meas>ma else meas-mi:.4f})")
