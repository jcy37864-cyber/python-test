import streamlit as st
import pandas as pd

df = pd.read_excel("data.xlsm")

st.title("데이터 입력")

edited_df = st.data_editor(df)

# 🔥 입력 즉시 계산
edited_df["Unnamed: 7"] = edited_df.apply(
    lambda row: row["Z"] if str(row["변환값"]).strip().upper() == "Z"
    else row["X"] if str(row["변환값"]).strip().upper() == "X"
    else row["Y"] if str(row["변환값"]).strip().upper() == "Y"
    else None,
    axis=1
)

# 결과 표시
st.subheader("결과")
st.dataframe(edited_df[["Unnamed: 7"]])

# 저장 버튼 (선택)
if st.button("저장"):
    edited_df.to_excel("data.xlsm", index=False)
    st.success("저장 완료!")

# 다운로드
st.download_button(
    label="다운로드",
    data=edited_df[["Unnamed: 7"]].to_csv(index=False).encode("utf-8-sig"),
    file_name="result.csv",
    mime="text/csv"
)
