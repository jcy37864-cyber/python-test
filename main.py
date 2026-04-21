import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

st.set_page_config(page_title="덕인 위치도 분석기", layout="wide")
st.title("🎯 위치도 분석 (규격치 수치 표기 버전)")

# [데이터 파싱 함수]
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
    mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f")
    
    std_range = round((tol / 2) * 2, 2)
    view_limit = st.slider("그래프 보기 범위(±mm)", 0.1, 5.0, std_range, step=0.1)

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

        fig = go.Figure()
        
        # 1. 파란 원 (기본 공차)
        r_blue = tol / 2
        fig.add_shape(type="circle", x0=-r_blue, y0=-r_blue, x1=r_blue, y1=r_blue,
                      line=dict(color="RoyalBlue", width=2), fillcolor="rgba(65, 105, 225, 0.1)")
        
        # 2. 빨간 원 (보너스 포함 최종 공차)
        max_total_tol = df['최종공차'].max()
        r_red = max_total_tol / 2
        # 화면 밖으로 나갈 경우 테두리에 고정하되, 수치는 실제 수치 표기
        display_r_red = min(r_red, view_limit * 0.98)
        fig.add_shape(type="circle", x0=-display_r_red, y0=-display_r_red, x1=display_r_red, y1=display_r_red,
                      line=dict(color="Red", width=2, dash="dot"))

        # --- [수치 및 명칭 표기 추가] ---
        # 파란색 텍스트
        fig.add_annotation(x=r_blue*0.7, y=r_blue*0.7, text=f"기본 공차: Ø{tol:.3f}",
                           showarrow=False, font=dict(color="RoyalBlue", size=12), bgcolor="white")
        # 빨간색 텍스트 (보너스가 있을 때만 표시)
        if max_total_tol > tol:
            fig.add_annotation(x=display_r_red*0.7, y=-display_r_red*0.7, text=f"최종(MMC): Ø{max_total_tol:.3f}",
                               showarrow=False, font=dict(color="Red", size=12), bgcolor="white")

        # 데이터 점 찍기
        for res in ["✅ OK", "❌ NG"]:
            sub = df[df['판정'] == res]
            visible = sub[(sub['편차_X'].abs() <= view_limit) & (sub['편차_Y'].abs() <= view_limit)]
            if not visible.empty:
                fig.add_trace(go.Scatter(
                    x=visible['편차_X'], y=visible['편차_Y'], mode='markers+text', name=res,
                    text=visible['측정포인트'], textposition="top center",
                    marker=dict(size=10, color="#2ecc71" if res=="✅ OK" else "#e74c3c")
                ))

        fig.update_layout(
            width=700, height=700,
            xaxis=dict(range=[-view_limit, view_limit], zeroline=True),
            yaxis=dict(range=[-view_limit, view_limit], zeroline=True),
            title=f"🎯 위치도 정밀 분석 (표준 범위: ±{view_limit}mm)"
        )
        st.plotly_chart(fig)
        
        st.success(f"📌 **품질 분석 요약**\n- 도면 규제치: Ø{tol:.3f}\n- 최대 보너스 적용 규격: Ø{max_total_tol:.3f}")
        st.dataframe(df[['측정포인트', '위치도', '보너스', '최종공차', '판정']])
