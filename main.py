import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

st.set_page_config(page_title="덕인 위치도 분석기", layout="wide")
st.title("🎯 위치도 정밀 분석 (빨간 점선 레이어 강화)")

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

with st.sidebar:
    st.header("⚙️ 기준 설정")
    sc = st.number_input("샘플 수", min_value=1, value=4)
    tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
    mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f") # 덕인님 설정값 반영

raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=150)

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

        # --- 📊 그래프 생성 (순서가 중요합니다) ---
        fig = go.Figure()
        view_limit = 0.7 
        
        # 1. 파란색 실선 (기본 공차) - 배경처럼 먼저 그립니다.
        r_base = tol / 2
        fig.add_shape(type="circle", x0=-r_base, y0=-r_base, x1=r_base, y1=r_base,
                      line=dict(color="RoyalBlue", width=2), fillcolor="rgba(65, 105, 225, 0.1)")

        # 2. 빨간색 점선 (최종 합격선) - 파란선 위에 덮어씌웁니다.
        max_r = df['최종공차'].max() / 2
        fig.add_shape(type="circle", x0=-max_r, y0=-max_r, x1=max_r, y1=max_r,
                      line=dict(color="Red", width=3, dash="dashdot")) # 더 굵고 뚜렷한 점선

        # 3. 데이터 점 (가장 위에 표시)
        in_bounds = df[(df['편차_X'].abs() <= view_limit) & (df['편차_Y'].abs() <= view_limit)]
        for res in ["✅ OK", "❌ NG"]:
            sub = in_bounds[in_bounds['판정'] == res]
            if not sub.empty:
                fig.add_trace(go.Scatter(
                    x=sub['편차_X'], y=sub['편차_Y'], mode='markers+text', name=res,
                    text=sub['측정포인트'], textposition="top center",
                    marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", 
                                line=dict(width=1, color="white")),
                    customdata=sub['최종공차'],
                    hovertemplate="위치도: %{y}<br>합격한계: Ø%{customdata:.3f}<extra></extra>"
                ))

        fig.update_layout(
            width=700, height=700, 
            xaxis=dict(range=[-view_limit, view_limit], zeroline=True, gridcolor='lightgrey'),
            yaxis=dict(range=[-view_limit, view_limit], zeroline=True, gridcolor='lightgrey'),
            title=f"🎯 MMC 보너스 적용 (최종 한계: Ø{df['최종공차'].max():.3f})",
            plot_bgcolor='white'
        )

        st.plotly_chart(fig, use_container_width=True)
        
        # 보너스 발생 여부 실시간 확인창
        st.success(f"✅ 현재 보너스 공차가 최대 **{df['보너스'].max():.3f}**만큼 발생하여 빨간 원이 확장되었습니다.")
        st.dataframe(df[['측정포인트', '위치도', '보너스', '최종공차', '판정']])
