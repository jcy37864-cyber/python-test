import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.subheader("🎯 위치도 정밀 분석 (수동 줌 고정 버전)")

    # 1. 분석 실행 상태 초기화
    if 'analyzed' not in st.session_state:
        st.session_state.analyzed = False

    # 2. 설정 영역
    with st.expander("⚙️ 양식 및 기준 설정", expanded=True):
        data_type = st.radio(
            "데이터 양식 선택", 
            ["유형 A (좌표 포함)", "유형 B (결과값만)"],
            horizontal=True
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수", min_value=1, value=4)
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        with col2:
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f")
        with col3:
            view_mode = st.radio("그래프 범위", ["자동", "수동"], key="view_mode_select")
            
    # 3. 데이터 입력
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=200)
    
    # 분석 시작 버튼 (누르면 상태 저장)
    if st.button("📊 데이터 분석 시작", type="primary", use_container_width=True):
        st.session_state.analyzed = True

    # 4. 분석 결과 출력 (버튼을 눌렀거나, 이미 분석된 상태일 때)
    if st.session_state.analyzed and raw_input:
        try:
            lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
            results = []

            # --- 데이터 파싱 로직 (유형 A/B 동일) ---
            if "유형 A" in data_type:
                rows = [ [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)] for l in lines if re.findall(r'[-+]?\d*\.\d+|\d+', l) ]
                for i in range(0, len(rows) // 3 * 3, 3):
                    dia, x, y = rows[i], rows[i+1], rows[i+2]
                    for s in range(1, len(x)):
                        results.append({
                            "측정포인트": f"P{(i//3)+1}_S{s}",
                            "위치도": round(np.sqrt((x[s]-x[0])**2 + (y[s]-y[0])**2) * 2, 4),
                            "최종공차": round(tol + max(0, (dia[s-1] if (s-1) < len(dia) else dia[-1]) - mmc_ref), 4),
                            "X_dev": x[s]-x[0], "Y_dev": y[s]-y[0]
                        })
            else:
                valid_rows = [ [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)] for l in lines if any(n != int(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', l)) ]
                for i in range(0, len(valid_rows) // 3 * 3, 3):
                    pos_row, mmc_row = valid_rows[i], valid_rows[i+1]
                    s_vals, b_vals = pos_row[-sc:], mmc_row[-sc:]
                    for s in range(sc):
                        results.append({
                            "측정포인트": f"P{(i//3)+1}_S{s+1}",
                            "위치도": s_vals[s],
                            "최종공차": round(tol + max(0, b_vals[s] - mmc_ref), 4),
                            "X_dev": (s_vals[s]/4) * (1 if s<2 else -1),
                            "Y_dev": (s_vals[s]/4) * (1 if s%2==0 else -1)
                        })

            if results:
                df = pd.DataFrame(results)
                df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

                # --- [수정 포인트: 슬라이더 위치를 분석 결과 아래에 배치하여 상태 유지] ---
                max_r = df['최종공차'].max() / 2
                if view_mode == "수동":
                    v_limit = st.slider("🔍 그래프 줌 조절 (±mm)", 0.05, 5.0, 0.5, step=0.05)
                else:
                    v_limit = max_r * 2.2

                # 그래프 그리기
                fig = go.Figure()
                fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, line=dict(color="RoyalBlue", width=2))
                fig.add_shape(type="circle", x0=-max_r, y0=-max_r, x1=max_r, y1=max_r, line=dict(color="Red", width=1.5, dash="dot"))

                for res in ["✅ OK", "❌ NG"]:
                    sub = df[df['판정'] == res]
                    if not sub.empty:
                        fig.add_trace(go.Scatter(x=sub['X_dev'], y=sub['Y_dev'], mode='markers+text', name=res, 
                                                 text=sub['측정포인트'], marker=dict(size=11, color="#2ecc71" if res=="✅ OK" else "#e74c3c")))

                fig.update_layout(width=700, height=700, xaxis=dict(range=[-v_limit, v_limit]), yaxis=dict(range=[-v_limit, v_limit]), plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(df[['측정포인트', '위치도', '최종공차', '판정']])

        except Exception as e:
            st.error(f"오류 발생: {e}")
            st.session_state.analyzed = False # 오류 시 초기화

if __name__ == "__main__":
    run_position_analysis()
