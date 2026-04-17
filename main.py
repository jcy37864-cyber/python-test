import streamlit as st
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(page_title="품질 측정 도구", layout="wide")

st.title("📊 품질 측정 통합 프로그램")

# =========================
# 🔥 메인 메뉴
# =========================
menu = st.selectbox(
    "기능 선택",
    ["기존 기능", "📈 그래프 분석"]
)

# =========================
# 기존 기능 (그대로 유지)
# =========================
if menu == "기존 기능":

    col1, col2 = st.columns([1, 1])

    # =========================
    # 🔄 변환기
    # =========================
    with col1:

        st.subheader("🔄 변환기")

        selected = st.selectbox(
            "변환기 선택",
            ["ZXY 변환", "토크 변환"]
        )

        if selected == "ZXY 변환":

            if "df" not in st.session_state:
                st.session_state.df = pd.DataFrame({
                    "X": [""] * 100,
                    "Y": [""] * 100,
                    "Z": [""] * 100,
                })

            edited_df = st.data_editor(
                st.session_state.df,
                use_container_width=True,
                key="editor"
            )

            if st.button("ZXY 생성"):

                results = []

                for _, row in edited_df.iterrows():
                    x = str(row["X"]).strip()
                    y = str(row["Y"]).strip()
                    z = str(row["Z"]).strip()

                    if x and y and z:
                        results.extend([z, x, y])

                st.subheader("결과 (세로)")

                for r in results:
                    st.write(r)

                csv_data = "\n".join(results)
                st.download_button("CSV 다운로드", data=csv_data, file_name="zxy.csv")

                output = BytesIO()
                df_result = pd.DataFrame(results, columns=["결과"])

                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df_result.to_excel(writer, index=False)

                st.download_button("엑셀 다운로드", data=output.getvalue(), file_name="zxy.xlsx")

        elif selected == "토크 변환":

            val = st.number_input("값 입력", value=0.0)

            mode = st.selectbox(
                "변환 선택",
                ["N·m → kgf·m", "kgf·m → N·m"]
            )

            if st.button("변환 실행"):

                if mode == "N·m → kgf·m":
                    result = val * 0.101972
                    st.success(f"{result:.4f} kgf·m")
                else:
                    result = val * 9.80665
                    st.success(f"{result:.4f} N·m")

    # =========================
    # 🧮 계산기
    # =========================
    with col2:

        st.subheader("🧮 계산기")

        calc = st.selectbox(
            "계산기 선택",
            ["합계", "평균/통계", "공차 판정", "길이 변환"]
        )

        if calc == "합계":

            a = st.number_input("A", value=0.0)
            b = st.number_input("B", value=0.0)

            if st.button("계산"):
                st.success(f"결과: {a + b}")

        elif calc == "평균/통계":

            nums = st.text_input("숫자 입력 (콤마로 구분)", "1,2,3")

            if st.button("계산 실행"):
                try:
                    values = [float(x.strip()) for x in nums.split(",")]

                    avg = sum(values) / len(values)
                    mx = max(values)
                    mn = min(values)

                    st.success(f"평균: {avg:.4f}")
                    st.info(f"최대: {mx} / 최소: {mn}")

                except:
                    st.error("입력 형식 오류")

        elif calc == "공차 판정":

            target = st.number_input("기준값", value=0.0)
            tol = st.number_input("허용오차 (±)", value=0.0)
            measured = st.number_input("측정값", value=0.0)

            if st.button("판정 실행"):

                lower = target - tol
                upper = target + tol

                if lower <= measured <= upper:
                    st.success(f"OK (범위: {lower} ~ {upper})")
                else:
                    st.error(f"NG (범위: {lower} ~ {upper})")

        elif calc == "길이 변환":

            length = st.number_input("길이 입력", value=0.0)

            mode = st.selectbox(
                "변환",
                ["mm → inch", "inch → mm"]
            )

            if st.button("변환"):

                if mode == "mm → inch":
                    result = length / 25.4
                    st.success(f"{result:.4f} inch")
                else:
                    result = length * 25.4
                    st.success(f"{result:.4f} mm")


# =========================
# 📈 그래프 분석 (신규 기능)
# =========================
elif menu == "📈 그래프 분석":

    st.subheader("📈 측정값 그래프 분석")

    uploaded_file = st.file_uploader("엑셀 업로드", type=["xlsx"])

    if uploaded_file:

        df = pd.read_excel(uploaded_file)

        st.write("데이터 미리보기")
        st.dataframe(df)

        col_min = st.selectbox("MIN 컬럼", df.columns)
        col_max = st.selectbox("MAX 컬럼", df.columns)
        col_val = st.selectbox("측정값 컬럼", df.columns)

        if st.button("그래프 생성"):

            df = df.dropna()

            df["기준값"] = (df[col_min] + df[col_max]) / 2

            fig, ax = plt.subplots(figsize=(14,6))

            # 측정값
            ax.plot(df[col_val].values, marker='o', label="측정값")

            # 공차 영역
            ax.fill_between(
                range(len(df)),
                df[col_min],
                df[col_max],
                alpha=0.2,
                label="공차"
            )

            # 기준선
            ax.plot(df["기준값"], linestyle='--', label="기준값")

            # 일부만 숫자 표시
            for i, val in enumerate(df[col_val]):
                if i % 5 == 0:
                    ax.text(i, val, f"{val:.3f}", fontsize=8, ha='center')

            # 최대 / 최소 강조
            max_idx = df[col_val].idxmax()
            min_idx = df[col_val].idxmin()

            max_val = df.loc[max_idx, col_val]
            min_val = df.loc[min_idx, col_val]

            ax.scatter(max_idx, max_val, s=120)
            ax.text(max_idx, max_val, f"MAX\n{max_val:.3f}", ha='center')

            ax.scatter(min_idx, min_val, s=120)
            ax.text(min_idx, min_val, f"MIN\n{min_val:.3f}", ha='center')

            ax.legend()
            ax.grid()

            st.pyplot(fig)
