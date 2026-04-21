import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.subheader("🎯 위치도 정밀 분석 (표 구조 맞춤형)")

    # 1. 설정 영역
    with st.expander("⚙️ 분석 기준 설정", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            # 이미지 표에서 샘플 데이터는 4개입니다 (0.330, 0.526, 0.625, 0.663)
            sc = st.number_input("샘플 수 (한 줄당 데이터 개수)", min_value=1, value=4, key="sc_v5")
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="tol_v5")
        with col2:
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f", key="mmc_v5")
        with col3:
            std_range = round(tol, 2)
            view_mode = st.radio("그래프 범위", ["표준(권장)", "수동 조절"], horizontal=True, key="mode_v5")
            view_limit = std_range if view_mode == "표준(권장)" else st.slider("범위 조절", 0.1, 5.0, std_range, step=0.1, key="zoom_v5")

    # 2. 데이터 입력
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=200, placeholder="이미지의 표 내용을 그대로 복사해서 넣어주세요.")

    if not raw_input:
        st.info("💡 데이터를 입력하면 분석이 시작됩니다.")
        return

    # 3. [핵심] 줄 단위 정밀 매칭 (443 오류 원천 차단)
    try:
        lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
        
        # 줄바꿈 기준으로 데이터 행만 추출
        rows = []
        for line in lines:
            nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', line)]
            if nums: rows.append(nums)

        # 이미지 양식: 3줄(위치도, X좌표, Y좌표)이 한 포인트 세트
        results = []
        for i in range(0, len(rows) // 3 * 3, 3):
            dia_vals = rows[i]   # 1행: [0.330, 0.526, 0.625, 0.663]
            x_vals = rows[i+1]   # 2행: [116.06, 116.043, 115.958, ...]
            y_vals = rows[i+2]   # 3행: [-83.96, -84.124, -84.202, ...]

            label = f"P{(i//3)+1}" # N, O, P 등 순서대로
            
            # 첫 번째 값(vals[0])은 도면값, 그 뒤는 측정값(S1~S4)
            for s in range(1, len(x_vals)):
                # 데이터 개수가 부족할 경우를 대비한 안전장치
                try:
                    results.append({
                        "측정포인트": f"{label}_S{s}",
                        "도면_X": x_vals[0], "도면_Y": y_vals[0],
                        "측정_X": x_vals[s], "측정_Y": y_vals[s],
                        "지름_MMC": dia_vals[s-1] if (s-1) < len(dia_vals) else dia_vals[-1]
                    })
                except IndexError:
                    continue

        df = pd.DataFrame(results)
        
        # 위치도 계산 공식
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
        df['최종공차'] = (tol + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        # 4. 시각화 (기존 모든 기능 포함)
        fig = go.Figure()
        # 원 그리기
        r_blue = tol / 2
        fig.add_shape(type="circle", x0=-r_blue, y0=-r_blue, x1=r_blue, y1=r_blue, line=dict(color="RoyalBlue", width=2.5))
        
        max_total_tol = df['최종공차'].max()
        r_red = max_total_tol / 2
        fig.add_shape(type="circle", x0=-r_red, y0=-r_red, x1=r_red, y1=r_red, line=dict(color="Red", width=2, dash="dot"))

        # 데이터 타점
        for res in ["✅ OK", "❌ NG"]:
            sub = df[df['판정'] == res]
            if not sub.empty:
                fig.add_trace(go.Scatter(x=sub['편차_X'], y=sub['편차_Y'], mode='markers+text', name=res, text=sub['측정포인트'], marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c")))

        fig.update_layout(width=700, height=700, xaxis=dict(range=[-view_limit, view_limit]), yaxis=dict(range=[-view_limit, view_limit]), plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

        # 5. 하단 리스트
        st.dataframe(df[['측정포인트', '위치도', '최종공차', '판정']])

    except Exception as e:
        st.error(f"데이터 형식이 맞지 않습니다: {e}")

if __name__ == "__main__":
    run_position_analysis()
