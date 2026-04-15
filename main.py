import streamlit as st

st.set_page_config(page_title="ZXY 변환기", layout="centered")

st.title("Z → X → Y 세로 변환기")

st.write("각 값들을 ,(콤마)로 구분해서 입력하세요")
st.write("예: 1,4,6")

# ✅ 입력 (절대 안 튕김)
x_input = st.text_input("X 값", "")
y_input = st.text_input("Y 값", "")
z_input = st.text_input("Z 값", "")

# 문자열 → 리스트 변환
def parse(text):
    if not text.strip():
        return []
    return [v.strip() for v in text.split(",")]

# 변환 버튼
if st.button("변환 실행"):

    X = parse(x_input)
    Y = parse(y_input)
    Z = parse(z_input)

    # 길이 맞추기 (가장 짧은 기준)
    length = min(len(X), len(Y), len(Z))

    result = []

    # 🔥 핵심: Z → X → Y 순서로 세로 쌓기
    for i in range(length):
        result.append(Z[i])
        result.append(X[i])
        result.append(Y[i])

    # 결과 출력
    st.subheader("결과 (세로 출력)")
    for r in result:
        st.write(r)

    # CSV 다운로드 (줄바꿈 형태)
    csv_data = "\n".join(result)

    st.download_button(
        label="CSV 다운로드",
        data=csv_data,
        file_name="zxy_result.csv",
        mime="text/csv"
    )
