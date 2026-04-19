import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="품질 측정 도구", layout="wide")

st.title("📊 품질 측정 통합 프로그램")

# =========================
# 📌 사이드 메뉴 (핵심)
# =========================
menu = st.sidebar.selectbox(
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
        st.dataframe(result_df, use_container_width=True)

        # 다운로드
        csv = result_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("CSV 다운로드", csv, "zxy.csv")

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            result_df.to_excel(writer, index=False)

        st.download_button("엑셀 다운로드", output.getvalue(), "zxy.xlsx")


# =========================
# 📈 그래프 (엑셀 업로드 복구)
# =========================
elif menu == "그래프 분석":

    st.subheader("📈 품질 그래프 분석")

    st.markdown("### 📥 엑셀 업로드 (MIN / MAX / VALUE)")

    uploaded_file = st.file_uploader("엑셀 파일 업로드", type=["xlsx", "csv"])

    # 템플릿 다운로드
    template = pd.DataFrame({
        "MIN": [0],
        "MAX": [10],
        "VALUE": [5]
    })

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template.to_excel(writer, index=False)

    st.download_button(
        "📄 템플릿 다운로드",
        data=output.getvalue(),
        file_name="template.xlsx"
    )

    if uploaded_file:

        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            df["판정"] = df.apply(
                lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG",
                axis=1
            )

            st.dataframe(df)

            fig, ax = plt.subplots()

            ax.plot(df["VALUE"], marker='o', label="VALUE")
            ax.plot(df["MIN"], linestyle='--', label="MIN")
            ax.plot(df["MAX"], linestyle='--', label="MAX")

            # NG 빨간 표시
            for i, row in df.iterrows():
                if row["판정"] == "NG":
                    ax.scatter(i, row["VALUE"], s=100)

            ax.legend()
            ax.grid()

            st.pyplot(fig)

            st.success(f"NG 개수: {len(df[df['판정']=='NG'])}")

        except Exception as e:
            st.error("파일 형식 오류")


# =========================
# 🧮 계산기 (토크 포함)
# =========================
elif menu == "계산기":

    st.subheader("🧮 계산기")

    calc = st.selectbox(
        "선택",
        ["토크 변환", "합계", "평균", "공차 판정"]
    )

    if calc == "토크 변환":

        val = st.number_input("값", value=0.0)

        mode = st.selectbox(
            "변환",
            ["N·m → kgf·m", "kgf·m → N·m"]
        )

        if mode == "N·m → kgf·m":
            st.success(f"{val * 0.101972:.4f} kgf·m")
        else:
            st.success(f"{val * 9.80665:.4f} N·m")

    elif calc == "합계":
        a = st.number_input("A", value=0.0)
        b = st.number_input("B", value=0.0)
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
