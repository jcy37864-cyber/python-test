import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="ZXY 변환기", layout="wide")

st.title("Z → X → Y 세로 변환기")

# ✅ 초기 데이터 (한 번만 생성)
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "X": [""] * 100,
        "Y": [""] * 100,
        "Z": [""] * 100,
    })

# ✅ data_editor는 key만 사용 (🔥 핵심)
edited_df = st.data_editor(
    st.session_state.df,
    num_rows="fixed",
    use_container_width=True,
    key="editor"
)

# 🔥 버튼 눌렀을 때만 저장 + 계산
if st.button("결과 생성"):

    df = edited_df.copy()   # 👉 여기서만 사용

    results = []

    for _, row in df.iterrows():
        x = str(row["X"]).strip()
        y = str(row["Y"]).strip()
        z = str(row["Z"]).strip()

        if x and y and z:
            results.extend([z, x, y])

    st.subheader("결과")

    # 👉 출력
    for r in results:
        st.write(r)

    # =====================
    # CSV 다운로드
    # =====================
    csv_data = "\n".join(results)

    st.download_button(
        "CSV 다운로드",
        data=csv_data,
        file_name="zxy_result.csv",
        mime="text/csv"
    )

    # =====================
    # 엑셀 다운로드 (openpyxl 사용)
    # =====================
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
