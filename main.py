import streamlit as st
import pandas as pd

df = pd.read_excel("data.xlsm")

st.title("데이터 입력")

edited_df = st.data_editor(df)

if st.button("저장"):
    edited_df.to_excel("data.xlsm", index=False)
    st.success("저장 완료!")