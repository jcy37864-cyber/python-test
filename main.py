import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.subheader("🎯 위치도 정밀 분석 (유형 B 보너스 로직 수정)")

    # 세션 상태 유지
    if 'analyzed' not in st.session_state:
        st.session_state.analyzed = False

    with st.expander("⚙️ 양식 및 기준 설정", expanded=True):
        data_type = st.radio("데이터 양식 선택", ["유형 A (좌표 포함)", "유형 B (결과값만)"], horizontal=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수", min_value=1, value=4)
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        with col2:
            mmc_ref = st.number_input("MMC 기준치 (유형 A 전용)", value=0.060, format="%.3f")
        with col3:
            view_mode = st.radio("그래프 범위", ["자동", "수동"])
            
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=200)
    
    if st.button("📊 데이터 분석 시작", type="primary", use_container_width=True):
        st.session_state.analyzed = True

    if st.session_state.analyzed and raw_input:
        try:
            lines = [l.strip() for l in raw_input.split('\n') if l.strip()]
            results = []

            # --- [유형 A: 직접 계산 방식] ---
            if "유형 A" in data_type:
                rows = [ [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)] for l in lines if re.findall(r'[-+]?\d*\.\d+|\d+', l) ]
                for i in range(0, len(rows) // 3 * 3, 3):
                    dia, x, y = rows[i], rows[i+1], rows[i+2]
                    for s in range(1, len(x)):
                        bonus = max(0, (dia[s-1] if (s-1) < len(dia) else dia[-1]) - mmc_ref)
                        results.append({
                            "측정포인트": f"P{(i//3)+1}_S{s}",
                            "위치도": round(np.sqrt((x[s]-x[0])**2 + (y[s]-y[0])**2) * 2, 4),
                            "최종공차": round(tol + bonus, 4),
                            "X_dev": x[s]-x[0], "Y_dev": y[s]-y[0]
                        })

            # --- [유형 B: 결과값 추출 방식 - 수정됨] ---
            else:
                # 숫자 데이터만 추출 (제목줄 번호 제외)
                raw_rows = []
                for l in lines:
                    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)]
                    if nums and any(n != int(n) for n in nums):
                        raw_rows.append(nums)
                
                # 3줄 세트 (위치도, MMC공차, Y좌표)
                for i in range(0, len(raw_rows) // 3 * 3, 3):
                    pos_vals = raw_rows[i][-sc:]  # 위치도 행
                    mmc_vals = raw_rows[i+1][-sc:] # MMC공차 행 (이게 곧 보너스!)
                    
                    for s in range(sc):
                        # 중요: 유형 B의 표에 적힌 0.402 같은 값은 '지름'이 아니라 이미 계산된 'MMC공차'임
                        bonus = mmc_vals[s] 
                        results.append({
                            "측정포인트": f"P{(i//3)+1}_S{s+1}",
                            "위치도": pos_vals[s],
                            "최종공차": round(tol + bonus, 4),
                            "X_dev": (pos_vals[s]/4) * (1 if s<2 else -1),
                            "Y_dev": (pos_vals[s]/4) * (1 if s%2==0 else -1)
                        })

            if results:
                df = pd.DataFrame(results)
                df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

                # 수동 줌 세션 유지
                max_total_tol = df['최종공차'].max()
                if view_mode == "수동":
                    v_limit = st.slider("🔍 그래프 줌 조절", 0.05, 5.0, 0.5, step=0.05)
                else:
                    v_limit = (max_total_tol / 2) * 2.2

                fig = go.Figure()
                fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, line=dict(color="RoyalBlue", width=2))
                fig.add_shape(type="circle", x0=-max_total_tol/2, y0=-max_total_tol/2, x1=max_total_tol/2, y1=max_total_tol/2, line=dict(color="Red", width=1.5, dash="dot"))

                for res in ["✅ OK", "❌ NG"]:
                    sub = df[df['판정'] == res]
                    if not sub.empty:
                        fig.add_trace(go.Scatter(x=sub['X_dev'], y=sub['Y_dev'], mode='markers+text', name=res, text=sub['측정포인트'], marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c")))

                fig.update_layout(width=700, height=700, xaxis=dict(range=[-v_limit, v_limit]), yaxis=dict(range=[-v_limit, v_limit]))
                st.plotly_chart(fig)
                st.dataframe(df[['측정포인트', '위치도', '최종공차', '판정']])

        except Exception as e:
            st.error(f"데이터 형식이 맞지 않습니다. 양식 선택을 확인해 주세요: {e}")
            st.session_state.analyzed = False

if __name__ == "__main__":
    run_position_analysis()
