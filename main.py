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

    # 다운로드 버튼 (한글 깨짐 방지)
    st.download_button(
        label="다운로드",
        data=edited_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="data.csv",
        mime="text/csv"
    )
