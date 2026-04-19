import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="품질 측정 도구", layout="wide")

# ---------------------
# 🎨 사이드바 스타일 (검정/남색)
# ---------------------
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #0E1117;
}
[data-testid="stSidebar"] * {
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 품질 측정 통합 프로그램")

menu = st.sidebar.radio(
    "메뉴 선택",
    ["ZXY 변환", "그래프 분석", "계산기"]
)

# =========================
# 🔄 ZXY 변환
# =========================
if menu == "ZXY 변환":

    st.subheader("🔄 ZXY 변환")

    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame({
            "X": [""] * 100,
            "Y": [""] * 100,
            "Z": [""] * 100,
        })

    edited_df = st.data_editor(
        st.session_state.df,
        use_container_width=True
    )

    if st.button("ZXY 생성"):

        results = []

        for _, row in edited_df.iterrows():
            x = str(row["X"]).strip()
            y = str(row["Y"]).strip()
            z = str(row["Z"]).strip()

            if x and y and z:
                results.extend([z, x, y])

        result_df = pd.DataFrame(results, columns=["결과"])
        st.dataframe(result_df)

        csv = result_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("CSV 다운로드", csv, "zxy.csv")

# =========================
# 📈 그래프 분석
# =========================
# =========================
# 📈 그래프 (최종 개선)
# =========================
elif menu == "그래프 분석":

    st.subheader("📈 품질 그래프 분석")

    uploaded_file = st.file_uploader("엑셀 업로드", type=["xlsx", "csv"])

    # 템플릿
    template = pd.DataFrame({
        "MIN": [30.1],
        "MAX": [30.7],
        "VALUE": [30.3]
    })

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template.to_excel(writer, index=False)

    st.download_button("📄 템플릿 다운로드", output.getvalue(), "template.xlsx")

    if uploaded_file:

        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # 판정
        df["판정"] = df.apply(
            lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG",
            axis=1
        )

        # 🔴 NG 강조 테이블
        def highlight(row):
            if row["판정"] == "NG":
                return ['background-color: red'] * len(row)
            return [''] * len(row)

        st.dataframe(df.style.apply(highlight, axis=1))

        # ======================
        # 📊 그래프 (핵심 개선)
        # ======================
        fig, ax = plt.subplots(figsize=(10, 4))  # ← 크기 줄임

        ax.plot(df["VALUE"], marker='o', label="VALUE")
        ax.plot(df["MIN"], linestyle='--', label="MIN")
        ax.plot(df["MAX"], linestyle='--', label="MAX")

        # 🔴 NG 표시
        for i, row in df.iterrows():
            if row["판정"] == "NG":
                ax.scatter(i, row["VALUE"], color='red', s=80)

        # ✅ MIN/MAX 값 표시 (중요)
        ax.text(len(df)-1, df["MAX"].iloc[-1], f"MAX: {df['MAX'].iloc[-1]:.3f}",
                color='green', ha='right')

        ax.text(len(df)-1, df["MIN"].iloc[-1], f"MIN: {df['MIN'].iloc[-1]:.3f}",
                color='orange', ha='right')

        ax.set_title("품질 경향 분석")
        ax.legend()
        ax.grid()

        st.pyplot(fig)

        # ======================
        # 📊 분석 결과 (강화)
        # ======================
        total = len(df)
        ng = len(df[df["판정"] == "NG"])
        ok = total - ng

        st.markdown("### 📋 검사 결과 요약")

        st.write(f"""
        ▶ 총 데이터: {total}개  
        ▶ OK: {ok}개 / NG: {ng}개  

        📌 판정 결과:
        """)

        if ng == 0:
            st.success("전체 양호 (모든 값이 규격 내)")
        elif ng / total > 0.3:
            st.error("NG 다수 발생 → 공정 이상 가능성 높음")
        else:
            st.warning("일부 NG 발생 → 공정 편차 존재")

        # 경향 분석
        avg = df["VALUE"].mean()

        if avg > df["MAX"].mean():
            st.error("전체적으로 상한 초과 경향")
        elif avg < df["MIN"].mean():
            st.error("전체적으로 하한 미달 경향")
        else:
            st.info("전체적으로 규격 내 분포")
# =========================
# 🧮 계산기
# =========================
elif menu == "계산기":

    st.subheader("🧮 계산기")

    calc = st.selectbox(
        "선택",
        ["토크 변환", "합계", "평균", "공차 판정"]
    )

    if calc == "토크 변환":
        val = st.number_input("값", 0.0)
        mode = st.selectbox("변환", ["N·m → kgf·m", "kgf·m → N·m"])

        if mode == "N·m → kgf·m":
            st.success(f"{val * 0.101972:.4f}")
        else:
            st.success(f"{val * 9.80665:.4f}")

    elif calc == "합계":
        a = st.number_input("A", 0.0)
        b = st.number_input("B", 0.0)
        st.success(a + b)

    elif calc == "평균":
        nums = st.text_input("입력", "1,2,3")
        try:
            vals = [float(x) for x in nums.split(",")]
            st.success(sum(vals)/len(vals))
        except:
            st.error("오류")

    elif calc == "공차 판정":
        t = st.number_input("기준값", 0.0)
        tol = st.number_input("공차", 0.0)
        v = st.number_input("측정값", 0.0)

        if t-tol <= v <= t+tol:
            st.success("OK")
        else:
            st.error("NG")
