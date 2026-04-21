import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.set_page_config(page_title="위치도 분석 시스템", layout="wide")
    st.subheader("🎯 위치도 정밀 분석 (유형 B 시각화 최적화)")

    if 'analyzed' not in st.session_state: st.session_state.analyzed = False

    with st.expander("⚙️ 설정", expanded=True):
        data_type = st.radio("데이터 양식", ["📍 유형 A (좌표 방식)", "📊 유형 B (MMC공차 기입 방식)"], horizontal=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수", min_value=1, value=4, key="sc_v")
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="tol_v")
        with col2:
            mmc_ref = st.number_input("MMC 기준치 (유형 A 전용)", value=0.060, format="%.3f", key="mmc_v")
        with col3:
            view_mode = st.radio("그래프 범위", ["자동", "수동"], horizontal=True, key="mode_v")

    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=200)
    
    if st.button("📊 데이터 분석 시작", type="primary", use_container_width=True):
        st.session_state.analyzed = True

    if st.session_state.analyzed and raw_input:
        try:
            lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
            results = []

            if "유형 A" in data_type:
                rows = []
                for line in lines:
                    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', line)]
                    if nums: rows.append(nums)
                for i in range(0, len(rows) // 3 * 3, 3):
                    dia_vals, x_vals, y_vals = rows[i], rows[i+1], rows[i+2]
                    for s in range(1, len(x_vals)):
                        bonus = max(0, (dia_vals[s-1] if (s-1) < len(dia_vals) else dia_vals[-1]) - mmc_ref)
                        results.append({
                            "측정포인트": f"P{(i//3)+1}_S{s}",
                            "위치도": round(np.sqrt((x_vals[s]-x_vals[0])**2 + (y_vals[s]-y_vals[0])**2) * 2, 4),
                            "최종공차": round(tol + bonus, 4),
                            "편차_X": x_vals[s]-x_vals[0], "편차_Y": y_vals[s]-y_vals[0]
                        })
            else:
                v_rows = []
                for line in lines:
                    nums = re.findall(r'[-+]?\d*\.\d+|\d+', line)
                    if nums and any('.' in n for n in nums):
                        v_rows.append([float(n) for n in nums])
                
                for i in range(0, len(v_rows) // 3 * 3, 3):
                    pos_vals, mmc_vals = v_rows[i][-sc:], v_rows[i+1][-sc:]
                    for s in range(sc):
                        # [시각화 개선] 위치도 값을 반경으로 삼아 사방으로 랜덤 분산
                        radius = pos_vals[s] / 2
                        angle = np.random.uniform(0, 2 * np.pi) # 랜덤 각도
                        results.append({
                            "측정포인트": f"P{(i//3)+1}_S{s+1}",
                            "위치도": pos_vals[s],
                            "최종공차": round(tol + mmc_vals[s], 4),
                            "편차_X": radius * np.cos(angle), 
                            "편차_Y": radius * np.sin(angle)
                        })

            if results:
                df = pd.DataFrame(results)
                df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")
                max_total_tol = df['최종공차'].max()
                
                view_limit = round((max_total_tol / 2) * 1.5, 2) if view_mode == "자동" else st.slider("🔍 줌", 0.05, 5.0, 0.5, step=0.05)

                fig = go.Figure()
                fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, line=dict(color="RoyalBlue", width=2.5), fillcolor="rgba(65, 105, 225, 0.05)")
                fig.add_shape(type="circle", x0=-max_total_tol/2, y0=-max_total_tol/2, x1=max_total_tol/2, y1=max_total_tol/2, line=dict(color="Red", width=1.5, dash="dot"))

                for res in ["✅ OK", "❌ NG"]:
                    sub = df[df['판정'] == res]
                    if not sub.empty:
                        fig.add_trace(go.Scatter(x=sub['편차_X'], y=sub['편차_Y'], mode='markers+text', name=res, text=sub['측정포인트'],
                                                 marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", line=dict(width=1, color="white"))))

                fig.update_layout(width=700, height=700, xaxis=dict(range=[-view_limit, view_limit], zeroline=True), 
                                  yaxis=dict(range=[-view_limit, view_limit], zeroline=True), plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df[['측정포인트', '위치도', '최종공차', '판정']])

        except Exception as e:
            st.error(f"⚠️ 오류: {e}")
            st.session_state.analyzed = False

if __name__ == "__main__":
    run_position_analysis()
