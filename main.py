import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 앱 설정
st.set_page_config(page_title="덕인 품질 분석기", layout="wide")

def parse_data(text, sc):
    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', text)]
    res = []
    step = 1 + sc
    for i in range(len(nums) // (step * 3)):
        base = i * step * 3
        label = chr(65 + i) if i < 26 else f"P{i+1}"
        p_r = nums[base:base+step]
        x_r = nums[base+step:base+step*2]
        y_r = nums[base+step*2:base+step*3]
        for s in range(sc):
            res.append({"항목": f"{label}_S{s+1}", "도면_X": x_r[0], "도면_Y": y_r[0], 
                        "실측_X": x_r[s+1], "실측_Y": y_r[s+1], "실측지름": p_r[s+1]})
    return res

st.title("🎯 덕인 위치도 분석 (과녁 복구 버전)")

# 입력창
sc = st.sidebar.number_input("샘플 수", min_value=1, value=4)
m_val = st.sidebar.number_input("MMC 기준", value=0.350, format="%.3f")
t_val = st.sidebar.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
raw = st.text_area("성적서 데이터를 붙여넣으세요", height=200)

if raw:
    data = parse_data(raw, sc)
    if data:
        df = pd.DataFrame(data)
        df['위치도'] = (np.sqrt((df['실측_X']-df['도면_X'])**2 + (df['실측_Y']-df['도면_Y'])**2)*2).round(4)
        df['보너스'] = (df['실측지름'] - m_val).clip(lower=0).round(4)
        df['최종공차'] = (t_val + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        # --- 과녁 시각화 ---
        base_r = t_val / 2
        fig = go.Figure()

        # 1. 과녁 배경 (파란색 원) - 무조건 위로 오게 설정
        fig.add_shape(type="circle", xref="x", yref="y", x0=-base_r, y0=-base_r, x1=base_r, y1=base_r,
                      fillcolor="rgba(52, 152, 219, 0.5)", line=dict(color="blue", width=4), layer="above")

        # 2. 점 찍기
        dev_x = df['실측_X'] - df['도면_X']
        dev_y = df['실측_Y'] - df['도면_Y']
        
        fig.add_trace(go.Scatter(x=dev_x, y=dev_y, mode='markers', 
                                 marker=dict(color=np.where(df['판정']=="✅ OK", "#2ecc71", "#e74c3c"), size=10),
                                 text=df['항목'], name="측정포인트"))

        # 3. 배율 조정 (이미지 4번처럼 데이터가 너무 크면 과녁이 안 보이므로 범위를 제한)
        # 과녁을 보기 위해 축 범위를 공차의 3배 정도로 고정합니다.
        limit = t_val * 1.5 
        
        fig.update_layout(
            width=700, height=700,
            xaxis=dict(range=[-limit, limit], zeroline=True, zerolinecolor='black', title="X 편차"),
            yaxis=dict(range=[-limit, limit], zeroline=True, zerolinecolor='black', title="Y 편차"),
            title=f"🎯 과녁 중심부 확대 (공차 범위: Ø{t_val})"
        )
        
        st.plotly_chart(fig)
        st.dataframe(df)
