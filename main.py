import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="ZXY 변환기", layout="wide")

st.title("Z → X → Y 세로 변환기")

# ✅ 초기 데이터 (100행)
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "X": [""] * 100,
        "Y": [""] * 100,
        "Z": [""] * 100,
    })

# ✅ 입력 테이블 (안 튕기게)
edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    num_rows="fixed"   # 🔥 중요 (안정성)
)

# 👉 입력 저장만 (계산 X)
st.session_state.df = edited_df

# 🔥 결과 생성 버튼
if st.button("결과 생성"):

    df = st.session_state.df.copy()
    results = []

    for _, row in df.iterrows():
        x = str(row.get("X", "")).strip()
        y = str(row.get("Y", "")).strip()
        z = str(row.get("Z", "")).strip()

        # 값이 다 있을 때만 처리
        if x and y and z:
            results.extend([z, x, y])  # 🔥 Z → X → Y

    st.subheader("결과 (세로 출력)")

    # 👉 화면 출력
    for r in results:
        st.write(r)

    # =========================
    # 📥 CSV 다운로드
    # =========================
    csv_data = "\n".join(results)

    st.download_button(
        label="CSV 다운로드",
        data=csv_data,
        file_name="zxy_result.csv",
        mime="text/csv"
    )

    # =========================
    # 📥 엑셀 다운로드 (.xlsx)
    # =========================
    output = BytesIO()
    df_result = pd.DataFrame(results, columns=["결과"])

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_result.to_excel(writer, index=False)

    st.download_button(
        label="엑셀 다운로드",
        data=output.getvalue(),
        file_name="zxy_result.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
