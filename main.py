import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 앱 설정 및 스타일
def init_app():
    st.set_page_config(page_title="덕인 품질 분석기 v10.5", layout="wide")
    st.markdown("""
        <style>
        .stBox { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #ddd; }
        .stButton > button { background-color: #ef4444 !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

# 2. 데이터 파싱 엔진
def parse_data(text, sc):
    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', text)]
    res = []
    step = 1 + sc
    for i in range(len(nums) // (step * 3)):
        base = i * step * 3
        label = chr(65 + i) if i < 26 else f"P{i+1}"
        p_r, x_r, y_r = nums[base:base+step], nums[base+step:base+step*2], nums[base+step*2:base+step*3]
        for s in range(sc):
            res.append({"항목": f"{label}_S{s+1}", "도면_X": x_r[0], "도면_Y": y_r[0], 
                        "실측_X": x_r[s+1], "실측_Y": y_r[s+1], "실측지름": p_r[s+1]})
    return res

def main():
    init_app()
    st.title("🎯 덕인 위치도 분석 솔루션")
    t1, t2, t3 = st.tabs(["입력", "과녁 분석", "리포트"])

    with t1:
        sc = st.number_input("샘플 수", min_value=1, value=4)
        raw = st.text_area("데이터 붙여넣기", height=200)
        if st.button("분석 실행") and raw:
            data = parse_data(raw, sc)
            if data:
                st.session_state.data = pd.DataFrame(data)
                st.success("데이터 로드 완료!")

    with t2:
        if 'data' not in st.session_state:
            st.warning("데이터를 먼저 입력하세요.")
        else:
            m_val = st.number_input("MMC 기준", value=0.350, format="%.3f")
            t_val = st.number_input("공차(Ø)", value=0.350, format="%.3f")
            
            df = st.session_state.data.copy()
            df['위치도'] = (np.sqrt((df['실측_X']-df['도면_X'])**2 + (df['실측_Y']-df['도면_Y'])**2)*2).round(4)
            df['보너스'] = (df['실측지름'] - m_val).clip(lower=0).round(4)
            df['최종공차'] = (t_val + df['보너스']).round(4)
            df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")
            st.session_state.analysed = df
            st.dataframe(df, use_container_width=True)

            # 과녁 그리기
            st.subheader("🎯 위치도 산포도")
            base_r = t_val / 2
            fig = go.Figure()

            # 과녁 배경 (파란 원) - layer를 'above'로 하여 무조건 보이게 설정
            fig.add_shape(type="circle", xref="x", yref="y", x0=-base_r, y0=-base_r, x1=base_r, y1=base_r,
                          fillcolor="rgba(52, 152, 219, 0.4)", line=dict(color="RoyalBlue", width=3), layer="above")

            # 데이터 점 찍기
            for p, c in [("✅ OK", "#2ecc71"), ("❌ NG", "#e74c3c")]:
                sub = df[df['판정'] == p]
                fig.add_trace(go.Scatter(x=sub['실측_X']-sub['도면_X'], y=sub['실측_Y']-sub['도면_Y'],
                                         mode='markers', name=p, marker=dict(color=c, size=10)))

            # 축 범위 설정 (데이터가 너무 멀어도 과녁이 보이게 최소 범위 고정)
            dev_x, dev_y = df['실측_X']-df['도면_X'], df['실측_Y']-df['도면_Y']
            max_v = max(dev_x.abs().max(), dev_y.abs().max(), base_r * 2)
            
            fig.update_layout(width=700, height=700, plot_bgcolor='white',
                              xaxis=dict(range=[-max_v*1.1, max_v*1.1], zeroline=True, zerolinecolor='black'),
                              yaxis=dict(range=[-max_v*1.1, max_v*1.1], zeroline=True, zerolinecolor='black'),
                              title=f"중앙 파란원 = 공차범위 (Ø{t_val})")
            st.plotly_chart(fig, use_container_width=True)

    with t3:
        if 'analysed' in st.session_state:
            ad = st.session_state.analysed
            st.metric("합격률", f"{(ad['판정']=='✅ OK').sum()/len(ad)*100:.1f}%")
            st.download_button("결과 다운로드", ad.to_csv(index=False).encode('utf-8-sig'), "Result.csv")

if __name__ == "__main__":
    main()
