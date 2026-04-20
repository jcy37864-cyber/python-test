import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import platform

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램", layout="wide")

# 2. 그래프 폰트 설정 (영문 기본 폰트 사용으로 깨짐 방지)
plt.rcParams['axes.unicode_minus'] = False
plt.rc('font', family='sans-serif') # 표준 영문 폰트 사용

# 3. 사이드바 스타일
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0E1117; }
[data-testid="stSidebar"] * { color: white; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Quality Measurement System")

menu = st.sidebar.radio(
    "Select Menu",
    ["🔄 ZXY Transform", "📈 Graph Analysis", "🧮 Calculator"]
)

# =========================
# 🔄 ZXY 변환 (가로 배열)
# =========================
if menu == "🔄 ZXY Transform":
    st.subheader("🔄 ZXY Data Transformation")

    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({
            "X": [""] * 10,
            "Y": [""] * 10,
            "Z": [""] * 10,
        })

    edited_df = st.data_editor(
        st.session_state.df_zxy,
        use_container_width=True,
        num_rows="dynamic"
    )

    if st.button("Generate ZXY"):
        results = []
        for _, row in edited_df.iterrows():
            x = str(row["X"]).strip()
            y = str(row["Y"]).strip()
            z = str(row["Z"]).strip()
            if x or y or z:
                # 가로로 Z, X, Y 배치
                results.append({"Z": z, "X": x, "Y": y})

        if results:
            result_df = pd.DataFrame(results)
            st.dataframe(result_df, use_container_width=True)
            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Download CSV", csv, "zxy_result.csv")
        else:
            st.warning("No data entered.")

# =========================
# 📈 그래프 분석 (기능 완전 복구)
# =========================
elif menu == "📈 Graph Analysis":
    st.subheader("📈 Quality Graph Analysis")

    uploaded_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])

    # 템플릿 다운로드 기능
    template = pd.DataFrame({"MIN": [30.1], "MAX": [30.7], "VALUE": [30.3]})
    tmp_out = BytesIO()
    with pd.ExcelWriter(tmp_out, engine="openpyxl") as writer:
        template.to_excel(writer, index=False)
    st.download_button("📄 Download Template", tmp_out.getvalue(), "template.xlsx")

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # 판정 및 편차 계산
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1)

        # NG 강조 테이블
        def highlight_ng(row):
            return ['background-color: #ffcccc' if row["판정"] == "NG" else '' for _ in row]
        st.dataframe(df.style.apply(highlight_ng, axis=1), use_container_width=True)

        # 📊 그래프 생성
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df["VALUE"], marker='o', label="VALUE", zorder=3)
        ax.plot(df["MIN"], linestyle='--', color='orange', label="MIN")
        ax.plot(df["MAX"], linestyle='--', color='green', label="MAX")

        # NG 포인트 및 Worst 포인트 강조
        worst_idx = df["편차"].idxmax()
        worst_row = df.loc[worst_idx]

        for i, row in df.iterrows():
            if row["판정"] == "NG":
                ax.scatter(i, row["VALUE"], color='red', s=80, zorder=4)

        if worst_row["편차"] > 0:
            ax.scatter(worst_idx, worst_row["VALUE"], facecolors='none', edgecolors='red', s=300, linewidths=3, zorder=5)
            # 글자 시인성 강화 (말풍선 형태)
            ax.text(worst_idx, worst_row["VALUE"], f" Worst: {worst_row['VALUE']:.3f} ", 
                    fontsize=10, color='black', fontweight='bold', ha='center', va='bottom',
                    bbox=dict(facecolor='white', alpha=0.9, edgecolor='red', boxstyle='round,pad=0.5'), zorder=6)

        # 수치 표시 (영문)
        ax.text(len(df)-1, df["MAX"].iloc[-1], f"MAX: {df['MAX'].iloc[-1]:.3f}", color='green', ha='right')
        ax.text(len(df)-1, df["MIN"].iloc[-1], f"MIN: {df['MIN'].iloc[-1]:.3f}", color='orange', ha='right')

        ax.set_title("Quality Trend Analysis")
        ax.set_xlabel("Sample Index")
        ax.set_ylabel("Value")
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)
        st.pyplot(fig)

        # 📸 이미지 다운로드
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png', bbox_inches='tight')
        st.download_button("📸 Save Graph Image", img_buffer.getvalue(), "quality_graph.png", "image/png")

        # 🔥 [복구] 검사 결과 요약
        st.markdown("---")
        st.markdown("### 📋 Analysis Summary")
        total = len(df)
        ng = len(df[df["판정"] == "NG"])
        ok = total - ng

        st.write(f"▶ Total Samples: {total} / OK: {ok} / NG: {ng}")

        if ng == 0:
            st.success("Result: ALL PASS (Within Specifications)")
        elif ng / total > 0.3:
            st.error("Result: HIGH NG RATE - Process Check Required!")
        else:
            st.warning("Result: SOME NG FOUND - Deviation Warning")

        # [복구] 평균 분석
        avg_val = df["VALUE"].mean()
        avg_max = df["MAX"].mean()
        avg_min = df["MIN"].mean()

        if avg_val > avg_max:
            st.error("Trend: Overall Above Upper Limit")
        elif avg_val < avg_min:
            st.error("Trend: Overall Below Lower Limit")
        else:
            st.info("Trend: Overall Within Specifications")

        # 📄 [복구] 결과 엑셀 다운로드
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📄 Download Result Excel", excel_buffer.getvalue(), "quality_result.xlsx")

# =========================
# 🧮 계산기 (기능 완전 복구)
# =========================
elif menu == "🧮 Calculator":
    st.subheader("🧮 Calculator")
    calc = st.selectbox("Select Function", ["Torque Convert", "Sum", "Average", "Tolerance Check"])

    if calc == "Torque Convert":
        val = st.number_input("Value", 0.0)
        mode = st.selectbox("Unit", ["N·m → kgf·m", "kgf·m → N·m"])
        if mode == "N·m → kgf·m":
            st.success(f"Result: {val * 0.101972:.4f}")
        else:
            st.success(f"Result: {val * 9.80665:.4f}")

    elif calc == "Sum":
        a = st.number_input("Value A", 0.0)
        b = st.number_input("Value B", 0.0)
        st.success(f"Sum: {a + b}")

    elif calc == "Average":
        nums = st.text_input("Input values (comma separated)", "1, 2, 3")
        try:
            vals = [float(x.strip()) for x in nums.split(",") if x.strip()]
            if vals: st.success(f"Average: {sum(vals)/len(vals):.4f}")
        except:
            st.error("Invalid input format.")

    elif calc == "Tolerance Check":
        t = st.number_input("Target", 0.0)
        tol = st.number_input("Tolerance", 0.0)
        v = st.number_input("Measured", 0.0)
        if t - tol <= v <= t + tol:
            st.success("Judgment: OK")
        else:
            st.error("Judgment: NG")
