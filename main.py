import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.subheader("🎯 위치도 정밀 분석 (자동 범위 & 수동 줌)")

    # 1. 설정 영역
    with st.expander("⚙️ 분석 기준 설정", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수 (S1~S4 기준 4)", min_value=1, value=4, key="sc_v8")
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="tol_v8")
        with col2:
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f", key="mmc_v8")
        with col3:
            # --- [핵심 수정: 자동 범위 계산 로직] ---
            # 나중에 데이터가 들어오면 이 값을 기준으로 자동 범위를 잡습니다.
            view_mode = st.radio("그래프 범위", ["자동(권장)", "수동 조절"], horizontal=True, key="mode_v8")
            
    # 2. 데이터 입력
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=200, placeholder="표 데이터를 복사해서 넣어주세요.")

    if not raw_input:
        st.info("💡 데이터를 입력하면 실시간으로 분석 그래프가 생성됩니다.")
        return

    # 3. 데이터 분석 로직 (이전과 동일)
    try:
        lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
        rows = []
        for line in lines:
            nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', line)]
            if nums: rows.append(nums)

        results = []
        for i in range(0, len(rows) // 3 * 3, 3):
            dia_vals, x_vals, y_vals = rows[i], rows[i+1], rows[i+2]
            label = f"P{(i//3)+1}"
            for s in range(1, len(x_vals)):
                results.append({
                    "측정포인트": f"{label}_S{s}",
                    "도면_X": x_vals[0], "도면_Y": y_vals[0],
                    "측정_X": x_vals[s], "측정_Y": y_vals[s],
                    "지름_MMC": dia_vals[s-1] if (s-1) < len(dia_vals) else dia_vals[-1]
                })

        df = pd.DataFrame(results)
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
        df['최종공차'] = (tol + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        # --- [범위 결정 로직] ---
        max_total_tol = df['최종공차'].max()
        # 자동일 때는 가장 큰 원(빨간 원)의 반지름보다 20% 더 여유 있게 잡음
        auto_limit = round((max_total_tol / 2) * 1.2, 2)
        
        if view_mode == "자동(권장)":
            view_limit = auto_limit
        else:
            # 수동일 때는 덕인님이 직접 줌을 조절 (기존 줌 느낌 유지)
            view_limit = st.slider("줌 조절 (±mm)", 0.1, 5.0, 0.5, step=0.1, key="zoom_v8")

        # 4. 그래프 시각화
        fig = go.Figure()
        
        # 기본 공차 원 (파란색)
        r_blue = tol / 2
        fig.add_shape(type="circle", x0=-r_blue, y0=-r_blue, x1=r_blue, y1=r_blue,
                      line=dict(color="RoyalBlue", width=2.5), fillcolor="rgba(65, 105, 225, 0.05)")
        
        # 최종 공차 원 (빨간색)
        r_red = max_total_tol / 2
        fig.add_shape(type="circle", x0=-r_red, y0=-r_red, x1=r_red, y1=r_red,
                      line=dict(color="Red", width=2, dash="dot"))

        # 타점 표시
        out_of_view = []
        for res in ["✅ OK", "❌ NG"]:
            sub = df[df['판정'] == res]
            vis = sub[(sub['편차_X'].abs() <= view_limit) & (sub['편차_Y'].abs() <= view_limit)]
            inv = sub[(sub['편차_X'].abs() > view_limit) | (sub['편차_Y'].abs() > view_limit)]
            
            if not inv.empty: out_of_view.extend(inv['측정포인트'].tolist())
            if not vis.empty:
                fig.add_trace(go.Scatter(x=vis['편차_X'], y=vis['편차_Y'], mode='markers+text', name=res, 
                                         text=vis['측정포인트'], textposition="top center",
                                         marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", line=dict(width=1, color="white"))))

        fig.update_layout(width=700, height=700, xaxis=dict(range=[-view_limit, view_limit], zeroline=True), 
                          yaxis=dict(range=[-view_limit, view_limit], zeroline=True), plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

        # 5. 하단 리스트 및 알림 (이전과 동일)
        if out_of_view:
            st.warning(f"⚠️ **현재 줌 범위 밖 타점:** {', '.join(out_of_view)}")
        
        st.info(f"📌 **품질 요약** | 기본공차: Ø{tol:.3f} / 최대합격원(빨간색): Ø{max_total_tol:.3f}")
        
        ng_list = df[df['판정'] == "❌ NG"]
        if not ng_list.empty:
            st.error(f"🚨 **규격 이탈(NG) 상세 리스트**")
            ng_html = "".join([f"<p style='color: #d32f2f; margin: 4px 0;'>• <b>{r['측정포인트']}</b>: {r['위치도']:.3f} (규격 Ø{r['최종공차']:.3f} 대비 <b>{r['위치도']-r['최종공차']:.3f} 초과</b>)</p>" for _, r in ng_list.iterrows()])
            st.markdown(f"<div style='height: 180px; overflow-y: auto; border: 1px solid #ff4b4b; padding: 10px; border-radius: 5px; background-color: #fff5f5;'>{ng_html}</div>", unsafe_allow_html=True)
        else:
            st.success("✅ 모든 시료가 최종 합격 범위 내에 있습니다.")

        st.dataframe(df[['측정포인트', '위치도', '보너스', '최종공차', '판정']])

    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")

if __name__ == "__main__":
    run_position_analysis()
