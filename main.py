import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 앱 설정
st.set_page_config(page_title="덕인 위치도 분석기", layout="wide")
st.title("🎯 위치도 정밀 분석 (범위 밖 시료 별도 표시)")

# 2. 데이터 파싱 함수
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

# 3. 사이드바 설정
with st.sidebar:
    st.header("⚙️ 기준 설정")
    sc = st.number_input("샘플 수", min_value=1, value=4)
    tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
    mmc_ref = st.number_input("MMC 기준치", value=0.350, format="%.3f")

# 4. 데이터 입력
raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=150)

if raw_input:
    data = parse_smart_data(raw_input, sc)
    if data:
        df = pd.DataFrame(data)
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        df['최종공차'] = (tol + (df['지름_MMC'] - mmc_ref).clip(lower=0)).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        # --- 📊 그래프 및 범위 밖 처리 ---
        view_limit = 0.7  # 과녁 시인성을 위해 ±0.7mm로 화면 고정
        
        # 화면 밖으로 나간 NG 시료 필터링
        out_of_bounds = df[(df['편차_X'].abs() > view_limit) | (df['편차_Y'].abs() > view_limit)]
        in_bounds = df[(df['편차_X'].abs() <= view_limit) & (df['편차_Y'].abs() <= view_limit)]

        fig = go.Figure()
        
        # 가이드 원 (기본공차/최대공차)
        r_base = tol / 2
        r_max = df['최종공차'].max() / 2
        fig.add_shape(type="circle", x0=-r_base, y0=-r_base, x1=r_base, y1=r_base,
                      line=dict(color="RoyalBlue", width=2), fillcolor="rgba(65, 105, 225, 0.1)")
        fig.add_shape(type="circle", x0=-r_max, y0=-r_max, x1=r_max, y1=r_max,
                      line=dict(color="Red", width=1.5, dash="dot"))

        # 화면 안의 데이터만 그래프에 표시
        for res in ["✅ OK", "❌ NG"]:
            sub = in_bounds[in_bounds['판정'] == res]
            if not sub.empty:
                fig.add_trace(go.Scatter(
                    x=sub['편차_X'], y=sub['편차_Y'], mode='markers+text', name=res,
                    text=sub['측정포인트'], textposition="top center",
                    marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", line=dict(width=1, color="white"))
                ))

        fig.update_layout(
            width=600, height=600,
            xaxis=dict(range=[-view_limit, view_limit], title="X 편차"),
            yaxis=dict(range=[-view_limit, view_limit], title="Y 편차"),
            title=f"🎯 과녁 중심부 (Ø{tol} 기준)"
        )

        # UI 출력
        col1, col2 = st.columns([2, 1])
        with col1:
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.metric("합격(OK)", f"{len(df[df['판정']=='✅ OK'])} 개")
            st.error(f"불합격(NG): {len(df[df['판정']=='❌ NG'])} 개")
            
            # --- 💡 범위 밖 시료 따로 표시 ---
            if not out_of_bounds.empty:
                st.warning("⚠️ 그래프 범위 밖 NG 시료")
                for _, row in out_of_bounds.iterrows():
                    st.write(f"**{row['측정포인트']}**: X({row['편차_X']}), Y({row['편차_Y']})")

        st.subheader("📋 전체 상세 데이터")
        st.dataframe(df[['측정포인트', '편차_X', '편차_Y', '위치도', '최종공차', '판정']], use_container_width=True)
