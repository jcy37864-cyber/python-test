import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="ZXY 변환기", layout="wide")

st.title("Z → X → Y 변환기")

# 👉 화면 반 나누기
col1, col2 = st.columns([1, 1])

# =========================
# 📊 왼쪽: ZXY 변환기
# =========================
with col1:

    st.subheader("데이터 입력")

    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame({
            "X": [""] * 100,
            "Y": [""] * 100,
            "Z": [""] * 100,
        })

    edited_df = st.data_editor(
        st.session_state.df,
        num_rows="fixed",
        use_container_width=True,
        key="editor"
    )

    if st.button("결과 생성"):

        df = edited_df.copy()
        results = []

        for _, row in df.iterrows():
            x = str(row["X"]).strip()
            y = str(row["Y"]).strip()
            z = str(row["Z"]).strip()

            if x and y and z:
                results.extend([z, x, y])

        st.subheader("결과 (세로 출력)")

        for r in results:
            st.write(r)

        # CSV 다운로드
        csv_data = "\n".join(results)
        st.download_button(
            "CSV 다운로드",
            data=csv_data,
            file_name="zxy_result.csv"
        )

        # 엑셀 다운로드
        output = BytesIO()
        df_result = pd.DataFrame(results, columns=["결과"])

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_result.to_excel(writer, index=False)

        st.download_button(
            "엑셀 다운로드",
            data=output.getvalue(),
            file_name="zxy_result.xlsx"
        )

# =========================
# 🧩 오른쪽: 확장 + 토크 계산기
# =========================
with col2:

    st.subheader("🧩 확장 공간")

    # 🔧 토크 변환기
    st.markdown("### 🔧 토크 변환기")

    torque_value = st.number_input("값 입력", value=0.0)

    conversion_type = st.selectbox(
        "변환 선택",
        ["N·m → kgf·m", "kgf·m → N·m"]
    )

    if st.button("변환 실행"):

        if conversion_type == "N·m → kgf·m":
            result = torque_value * 0.101972
            st.success(f"{result:.4f} kgf·m")

        else:
            result = torque_value * 9.80665
            st.success(f"{result:.4f} N·m")

    st.markdown("---")

    # 📝 메모 공간 (유지)
    st.markdown("### 📝 메모")

    note = st.text_area(
        "필요한 기능 기록",
        placeholder="여기에 다음에 만들 기능 적기",
        height=200
    )
