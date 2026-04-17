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
    # 🔥 ZXY 변환 (최종 완성)
    # ---------------------
    if selected == "ZXY 변환":

        st.markdown("### 📋 엑셀처럼 입력 (복사 → 붙여넣기 가능)")

        # 초기 테이블
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

        # 🔥 자동 실행 (버튼 없음)
        results = []

        for _, row in edited_df.iterrows():
            x = str(row["X"]).strip()
            y = str(row["Y"]).strip()
            z = str(row["Z"]).strip()

            if x and y and z:
                results.extend([z, x, y])

        # 결과 표시
        st.markdown("### 🔽 결과 (세로)")

        if len(results) == 0:
            st.info("데이터 입력하면 자동 변환됨")
        else:
            result_df = pd.DataFrame(results, columns=["결과"])
            st.dataframe(result_df, use_container_width=True)

            # CSV 다운로드
            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 CSV 다운로드",
                data=csv,
                file_name="zxy_result.csv"
            )

            # 엑셀 다운로드
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                result_df.to_excel(writer, index=False)

            st.download_button(
                "📥 엑셀 다운로드",
                data=output.getvalue(),
                file_name="zxy_result.xlsx"
            )

    # ---------------------
    # 🔩 토크 변환
    # ---------------------
    elif selected == "토크 변환":

        val = st.number_input("값 입력", value=0.0)

        mode = st.selectbox(
            "변환 선택",
            ["N·m → kgf·m", "kgf·m → N·m"]
        )

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

    # 합계
    if calc == "합계":
        a = st.number_input("A", value=0.0)
        b = st.number_input("B", value=0.0)
        st.success(f"결과: {a + b}")

    # 평균/통계
    elif calc == "평균/통계":
        nums = st.text_input("숫자 입력 (콤마)", "1,2,3")

        try:
            values = [float(x.strip()) for x in nums.split(",")]
            avg = sum(values) / len(values)
            st.success(f"평균: {avg:.4f}")
            st.info(f"최대: {max(values)} / 최소: {min(values)}")
        except:
            st.error("입력 오류")

    # 공차 판정
    elif calc == "공차 판정":
        target = st.number_input("기준값", value=0.0)
        tol = st.number_input("허용오차 ±", value=0.0)
        measured = st.number_input("측정값", value=0.0)

        lower = target - tol
        upper = target + tol

        if lower <= measured <= upper:
            st.success(f"OK ({lower} ~ {upper})")
        else:
            st.error(f"NG ({lower} ~ {upper})")

    # 길이 변환
    elif calc == "길이 변환":
        length = st.number_input("길이", value=0.0)

        mode = st.selectbox("변환", ["mm → inch", "inch → mm"])

        if mode == "mm → inch":
            st.success(f"{length / 25.4:.4f} inch")
        else:
            st.success(f"{length * 25.4:.4f} mm")
