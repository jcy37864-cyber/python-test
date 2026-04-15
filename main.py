import streamlit as st
import pandas as pd

st.set_page_config(page_title="데이터 입력", layout="wide")

# ✅ 최초 1회 로드
if "df" not in st.session_state:
    df = pd.read_excel("data.xlsm")

    df.rename(columns={
        "Unnamed: 6": "선택값",
        "Unnamed: 7": "결과"
    }, inplace=True)

    if "결과" not in df.columns:
        df["결과"] = None

    st.session_state.df = df

st.title("데이터 입력")

# ✅ 입력 영역 (절대 건드리지 않음 = 안 튕김 핵심)
edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    num_rows="dynamic",
    key="editor",
    column_config={
        "X": st.column_config.NumberColumn(required=False),
        "Y": st.column_config.NumberColumn(required=False),
        "Z": st.column_config.NumberColumn(required=False),
    }
)

# 👉 입력값만 저장 (여기서 계산 절대 금지)
st.session_state.df = edited_df

# 🔥 계산 함수
def make_result(df):
    values = []
    for _, row in df.iterrows():
        values.extend([
            row.get("Z"),
            row.get("X"),
            row.get("Y")
        ])
    values = values[:len(df)]
    df["결과"] = values
    return df

# ✅ 버튼 눌렀을 때만 계산 (안 튕김 핵심)
if st.button("결과 생성"):
    st.session_state.df = make_result(st.session_state.df.copy())

# ✅ 결과 출력
st.subheader("결과 (Z → X → Y)")
st.dataframe(st.session_state.df, use_container_width=True)

# ✅ 엑셀 저장
if st.button("엑셀 저장"):
    save_df = st.session_state.df.rename(columns={
        "선택값": "Unnamed: 6",
        "결과": "Unnamed: 7"
    })
    save_df.to_excel("data.xlsm", index=False)
    st.success("저장 완료!")

# ✅ 다운로드
st.download_button(
    label="CSV 다운로드",
    data=st.session_state.df.to_csv(index=False).encode("utf-8-sig"),
    file_name="result.csv",
    mime="text/csv"
)
