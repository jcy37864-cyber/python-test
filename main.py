import streamlit as st
import pandas as pd

# 엑셀 불러오기
df = pd.read_excel("data.xlsm")

st.title("데이터 입력")

# 데이터 수정
edited_df = st.data_editor(df)

# 저장 버튼
if st.button("저장"):
    edited_df.to_excel("data.xlsm", index=False)
    st.success("저장 완료!")

# 🔽 Unnamed: 7 컬럼 그대로 표시 (정렬 없음)
if "Unnamed: 7" in edited_df.columns:
    result = edited_df[["Unnamed: 7"]]

    st.subheader("결과 (입력 순서 그대로)")
    st.dataframe(result)

    # 다운로드 버튼
    st.download_button(
        label="다운로드",
        data=result.to_csv(index=False).encode("utf-8-sig"),
        file_name="data.csv",
        mime="text/csv"
    )
else:
    st.error("Unnamed: 7 컬럼이 없음")
