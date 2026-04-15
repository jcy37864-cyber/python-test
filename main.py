import streamlit as st
import pandas as pd

df = pd.read_excel("data.xlsm")

st.title("데이터 입력")

edited_df = st.data_editor(df)
edited_df["Unnamed: 7"] = edited_df.apply(
    lambda row: row["Z"] if str(row["변환값"]).strip().upper() == "Z"
    else row["X"] if str(row["변환값"]).strip().upper() == "X"
    else row["Y"] if str(row["변환값"]).strip().upper() == "Y"
    else None,
    axis=1
)
if st.button("저장"):

    # 🔥 Unnamed: 7 자동 생성 (핵심)
    edited_df["Unnamed: 7"] = edited_df.apply(
        lambda row: row["Z"] if row["변환값"] == "Z"
        else row["X"] if row["변환값"] == "X"
        else row["Y"] if row["변환값"] == "Y"
        else None,
        axis=1
    )

    # 저장
    edited_df.to_excel("data.xlsm", index=False)
    st.success("저장 완료!")

# 결과 표시
if "Unnamed: 7" in edited_df.columns:
    result = edited_df[["Unnamed: 7"]]

    st.subheader("결과")
    st.dataframe(result)

    # 🔽 다운로드 버튼 추가 (여기 중요)
    st.download_button(
        label="다운로드",
        data=result.to_csv(index=False).encode("utf-8-sig"),
        file_name="result.csv",
        mime="text/csv"
    )
