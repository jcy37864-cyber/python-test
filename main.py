import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 앱 설정
st.set_page_config(page_title="덕인 위치도 분석기", layout="wide")
st.title("🎯 빨간 원 강제 표시 버전")

def parse_smart_data(raw_text, sc):
    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', raw_text)]
    if not nums: return None
    results = []
    step = 1 + sc
    set_len = step * 3
    for i in range(len(nums) // set_len):
        base = i * set_len
        try:
            dia_p = nums[base : base + step]
            x_p = nums[base + step : base + step * 2]
            y_p = nums[base + step * 2 : base + step * 3]
            label = chr(65 + i) if i < 26 else f"P{i+1}"
            for s in range(sc):
                results.append({
                    "측정포인트": f"{label}_S{s+1}",
                    "도면_X": x_p[0], "도면_Y": y_p[0],
                    "측정_X": x_p[s+1], "측정_Y": y_p[s+1],
                    "지름_MMC": dia_p[s+1]
                })
        except: break
    return results

# 2. 사이드바 (기준치를 0.01로 테스트해보세요)
with st.sidebar:
    st.header("⚙️ 기준 설정")
    sc = st.number_input("샘플 수", min_value=1, value=4)
    tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
    mmc_ref = st.number_input("MMC 기준치", value=0.010, format="%.3f") # 값을 확 낮춤

raw_input = st.text_area("데이터 붙여넣기", height=150)

if raw_input:
    data = parse_smart_data(raw_input, sc)
    if data:
        df = pd.DataFrame(data)
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
        df['최종공차'] = (tol + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        fig = go.Figure()
        
        # [중요] 레이어 순서: 파란색을 먼저 배경으로 깔고, 빨간색을 그 위에 그립니다.
        # 파란색 (기본)
        fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2,
                      line=dict(color="RoyalBlue", width=1), fillcolor="rgba(65, 105, 225, 0.05)")

        # 빨간색 (최종 합격선) - 훨씬 굵고 뚜렷하게!
        max_r = df['최종공차'].max() / 2
        fig.add_shape(type="circle", x0=-max_r, y0=-max_r, x1=max_r, y1=max_r,
                      line=dict(color="Red", width=4, dash="dot"))

        # 점 찍기
        for res in ["✅ OK", "❌ NG"]:
            sub = df[df['판정'] == res]
            if not sub.empty:
                fig.add_trace(go.Scatter(
                    x=sub['편차_X'], y=sub['편차_Y'], mode='markers+text', name=res,
                    text=sub['측정포인트'], textposition="top center",
                    marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", line=dict(width=1, color="white"))
                ))

        view_limit = max(0.7, max_r * 1.2)
        fig.update_layout(width=700, height=700, xaxis=dict(range=[-view_limit, view_limit]), yaxis=dict(range=[-view_limit, view_limit]))
        
        st.plotly_chart(fig)
        st.success(f"현재 최대 공차는 Ø{df['최종공차'].max():.3f}입니다. (빨간 원)")
        st.dataframe(df[['측정포인트', '지름_MMC', '보너스', '최종공차', '판정']])
