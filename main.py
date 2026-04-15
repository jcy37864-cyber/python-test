import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="ZXY 변환기", layout="wide")

st.title("Z → X → Y 변환기")

# 👉 화면 반으로 나누기
col1, col2 = st.columns([1, 1])

# =========================
# 📊 왼쪽: ZXY 변환기
# =========================
with col1:

    st.subheader("데이터 입력")

    # 초기 데이터
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
            file_name="zxy_result.csv",
            mime="text/csv"
        )

        # 엑셀 다운로드
        output = BytesIO()
        df_result = pd.DataFrame(results, columns=["결과"])

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_result.to_excel(writer, index=False)

        st.download_button(
            "엑셀 다운로드",
            data=output.getvalue(),
            file_name="zxy_result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# =========================
# 🧩 오른쪽: 확장 공간 (중요)
# =========================
with col2:

    st.subheader("🧩 확장 공간 (여기에 기능 추가 예정)")

    st.write("👉 여기에 나중에 계산기, 자동화 기능 등을 추가할 수 있습니다.")

    # 🔥 핵심: 자유 입력 공간 (메모/설계용)
    user_note = st.text_area(
        "필요한 기능을 적어두세요",
        placeholder="예: 평균 계산, 특정 조건 필터, 자동 변환 등...",
        height=300
    )

    # 👉 임시 저장 느낌
    if st.button("메모 저장"):
        st.success("저장됨 (임시)")
