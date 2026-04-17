import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="품질 측정 통합 프로그램", layout="wide")

st.title("📊 품질 측정 통합 프로그램")

col1, col2 = st.columns([1, 1])

# =========================
# 🔄 변환기 영역
# =========================
with col1:

    st.subheader("🔄 변환기")

    selected = st.selectbox(
        "선택",
        ["ZXY 변환", "토크 변환"]
    )

    # ---------------------
    # 🔥 ZXY 변환 (완전 복구)
    # ---------------------
    if selected == "ZXY 변환":

        st.markdown("### 📋 데이터 입력 (엑셀처럼 복붙 가능)")

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

            if len(results) == 0:
                st.warning("데이터 없음")
            else:
                st.subheader("결과 (세로)")

                result_df = pd.DataFrame(results, columns=["결과"])
                st.dataframe(result_df, use_container_width=True)

                # CSV 다운로드
                csv = result_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("CSV 다운로드", csv, "zxy.csv")

                # 엑셀 다운로드
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    result_df.to_excel(writer, index=False)

                st.download_button("엑셀 다운로드", output.getvalue(), "zxy.xlsx")

    # ---------------------
    # 🔩 토크 변환
    # ---------------------
    elif selected == "토크 변환":

        val = st.number_input("값 입력", value=0.0)

        mode = st.selectbox(
            "변환",
            ["N·m → kgf·m", "kgf·m → N·m"]
        )

        if mode == "N·m → kgf·m":
            st.success(f"{val * 0.101972:.4f} kgf·m")
        else:
            st.success(f"{val * 9.80665:.4f} N·m")


# =========================
# 📈 그래프 + 계산기 영역
# =========================
with col2:

    tab1, tab2 = st.tabs(["📈 그래프", "🧮 계산기"])

    # ---------------------
    # 📈 그래프
    # ---------------------
    with tab1:

        st.subheader("📈 품질 데이터 그래프")

        st.markdown("### 📋 입력 형식: MIN / MAX / VALUE")

        if "graph_df" not in st.session_state:
            st.session_state.graph_df = pd.DataFrame({
                "MIN": [""] * 50,
                "MAX": [""] * 50,
                "VALUE": [""] * 50,
            })

        graph_df = st.data_editor(
            st.session_state.graph_df,
            use_container_width=True
        )

        if st.button("그래프 생성"):

            try:
                df = graph_df.copy()
                df = df.replace("", pd.NA).dropna()

                df["MIN"] = df["MIN"].astype(float)
                df["MAX"] = df["MAX"].astype(float)
                df["VALUE"] = df["VALUE"].astype(float)

                df["판정"] = df.apply(
                    lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG",
                    axis=1
                )

                # 결과 테이블
                st.dataframe(df, use_container_width=True)

                # 그래프
                fig, ax = plt.subplots()

                ax.plot(df["VALUE"].values, marker='o', label="VALUE")
                ax.plot(df["MIN"].values, linestyle='--', label="MIN")
                ax.plot(df["MAX"].values, linestyle='--', label="MAX")

                # NG 강조
                for i, row in df.iterrows():
                    if row["판정"] == "NG":
                        ax.scatter(i, row["VALUE"], s=100)

                ax.set_title("품질 측정 그래프")
                ax.legend()
                ax.grid()

                st.pyplot(fig)

                # 요약
                total = len(df)
                ng = len(df[df["판정"] == "NG"])

                st.success(f"총 {total}개 중 NG {ng}개")

            except Exception as e:
                st.error("데이터 오류")

    # ---------------------
    # 🧮 계산기
    # ---------------------
    with tab2:

        st.subheader("🧮 계산기")

        calc = st.selectbox(
            "선택",
            ["합계", "평균", "공차 판정", "길이 변환"]
        )

        if calc == "합계":
            a = st.number_input("A", value=0.0)
            b = st.number_input("B", value=0.0)
            st.success(f"결과: {a + b}")

        elif calc == "평균":
            nums = st.text_input("숫자 입력", "1,2,3")

            try:
                values = [float(x.strip()) for x in nums.split(",")]
                st.success(f"평균: {sum(values)/len(values):.4f}")
            except:
                st.error("입력 오류")

        elif calc == "공차 판정":
            target = st.number_input("기준값", value=0.0)
            tol = st.number_input("±공차", value=0.0)
            val = st.number_input("측정값", value=0.0)

            if target - tol <= val <= target + tol:
                st.success("OK")
            else:
                st.error("NG")

        elif calc == "길이 변환":
            val = st.number_input("값", value=0.0)
            mode = st.selectbox("변환", ["mm→inch", "inch→mm"])

            if mode == "mm→inch":
                st.success(f"{val/25.4:.4f} inch")
            else:
                st.success(f"{val*25.4:.4f} mm")
