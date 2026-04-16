import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="품질 측정 도구", layout="wide")

st.title("📊 품질 측정 통합 프로그램")

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

    # ---------------------
    # ZXY 변환
    # ---------------------
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

            # CSV 다운로드
            csv_data = "\n".join(results)
            st.download_button("CSV 다운로드", data=csv_data, file_name="zxy.csv")

            # 엑셀 다운로드 (openpyxl 사용 → 오류 없음)
            output = BytesIO()
            df_result = pd.DataFrame(results, columns=["결과"])

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_result.to_excel(writer, index=False)

            st.download_button("엑셀 다운로드", data=output.getvalue(), file_name="zxy.xlsx")

    # ---------------------
    # 토크 변환
    # ---------------------
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

    # ---------------------
    # 합계
    # ---------------------
    if calc == "합계":

        a = st.number_input("A", value=0.0)
        b = st.number_input("B", value=0.0)

        if st.button("계산"):
            st.success(f"결과: {a + b}")

    # ---------------------
    # 평균 / 통계
    # ---------------------
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

    # ---------------------
    # 공차 판정
    # ---------------------
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

    # ---------------------
    # 길이 변환
    # ---------------------
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
