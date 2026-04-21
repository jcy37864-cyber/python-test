import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.subheader("🎯 위치도 정밀 분석 (통합 완결판)")

    # 1. 설정 영역 (마음에 들어 하신 레이아웃)
    with st.expander("⚙️ 분석 기준 및 양식 설정", expanded=True):
        data_type = st.radio("데이터 양식 선택", ["📍 유형 A (좌표 방식)", "📊 유형 B (MMC공차 기입 방식)"], horizontal=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수 (한 줄당)", min_value=1, value=4, key="sc_final")
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="tol_final")
        with col2:
            mmc_ref = st.number_input("MMC 기준치 (유형 A 전용)", value=0.060, format="%.3f", key="mmc_final")
        with col3:
            view_mode = st.radio("그래프 범위", ["자동(권장)", "수동 조절"], horizontal=True, key="mode_final")

    # 2. 데이터 입력 및 분석 버튼
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=200, placeholder="이미지의 표 내용을 그대로 복사해서 넣어주세요.")
    analyze_button = st.button("📊 데이터 분석 시작", type="primary", use_container_width=True)

    if analyze_button and raw_input:
        try:
            lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
            results = []

            # --- [유형 A 분석 로직] ---
            if "유형 A" in data_type:
                rows = []
                for line in lines:
                    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', line)]
                    if nums: rows.append(nums)
                
                for i in range(0, len(rows) // 3 * 3, 3):
                    dia_vals, x_vals, y_vals = rows[i], rows[i+1], rows[i+2]
                    label = f"P{(i//3)+1}"
                    for s in range(1, len(x_vals)):
                        dev_x = round(x_vals[s] - x_vals[0], 4)
                        dev_y = round(y_vals[s] - y_vals[0], 4)
                        bonus = max(0, (dia_vals[s-1] if (s-1) < len(dia_vals) else dia_vals[-1]) - mmc_ref)
                        results.append({
                            "측정포인트": f"{label}_S{s}",
                            "편차_X": dev_x, "편차_Y": dev_y,
                            "위치도": round(np.sqrt(dev_x**2 + dev_y**2) * 2, 4),
                            "최종공차": round(tol + bonus, 4),
                            "보너스": round(bonus, 4)
                        })

            # --- [유형 B 분석 로직: 핵심 수정] ---
            else:
                v_rows = []
                for line in lines:
                    nums = re.findall(r'[-+]?\d*\.\d+|\d+', line)
                    if nums: v_rows.append([float(n) for n in nums])
                
                for i in range(0, len(v_rows) // 3 * 3, 3):
                    pos_vals = v_rows[i][-sc:]      # 위치도 값
                    mmc_bonus = v_rows[i+1][-sc:]   # 성적서에 적힌 보너스
                    label = f"P{(i//3)+1}"
                    for s in range(sc):
                        # 그래프 시각화를 위해 위치도 기반 가상 좌표 생성 (사방으로 뿌려줌)
                        angle = (2 * np.pi / sc) * s
                        dist = pos_vals[s] / 2
                        results.append({
                            "측정포인트": f"{label}_S{s+1}",
                            "편차_X": round(dist * np.cos(angle), 4),
                            "편차_Y": round(dist * np.sin(angle), 4),
                            "위치도": pos_vals[s],
                            "최종공차": round(tol + mmc_bonus[s], 4), # 중복 더하기 방지
                            "보너스": mmc_bonus[s]
                        })

            df = pd.DataFrame(results)
            df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

            # 3. 시각화 (마음에 들어 하신 디자인)
            max_tol = df['최종공차'].max()
            view_limit = round((max_tol / 2) * 1.5, 2) if view_mode == "자동(권장)" else st.slider("줌 조절", 0.1, 2.0, 0.5)

            fig = go.Figure()
            # 파란 원 (기본), 빨간 원 (최대 합격 범위)
            fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, line=dict(color="RoyalBlue", width=2), fillcolor="rgba(65, 105, 225, 0.05)")
            fig.add_shape(type="circle", x0=-max_tol/2, y0=-max_tol/2, x1=max_tol/2, y1=max_tol/2, line=dict(color="Red", width=1.5, dash="dot"))

            for res in ["✅ OK", "❌ NG"]:
                sub = df[df['판정'] == res]
                if not sub.empty:
                    fig.add_trace(go.Scatter(x=sub['편차_X'], y=sub['편차_Y'], mode='markers+text', name=res,
                                             text=sub['측정포인트'], textposition="top center",
                                             marker=dict(size=10, color="#2ecc71" if res=="✅ OK" else "#e74c3c", line=dict(width=1, color="white"))))

            fig.update_layout(width=600, height=600, xaxis=dict(range=[-view_limit, view_limit], zeroline=True),
                              yaxis=dict(range=[-view_limit, view_limit], zeroline=True), plot_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)

            # 4. NG 상세 리스트 (스크롤 박스)
            st.info(f"📌 **품질 요약** | 기본공차: Ø{tol:.3f} / 최대 합격원: Ø{max_tol:.3f}")
            ng_list = df[df['판정'] == "❌ NG"]
            if not ng_list.empty:
                st.error(f"🚨 **규격 이탈(NG) 상세 리스트**")
                ng_html = "".join([f"<p style='color: #d32f2f; margin: 4px 0;'>• <b>{r['측정포인트']}</b>: {r['위치도']:.3f} (공차 Ø{r['최종공차']:.3f} 대비 <b>{r['위치도']-r['최종공차']:.3f} 초과</b>)</p>" for _, r in ng_list.iterrows()])
                st.markdown(f"<div style='height: 150px; overflow-y: auto; border: 1px solid #ff4b4b; padding: 10px; border-radius: 5px; background-color: #fff5f5;'>{ng_html}</div>", unsafe_allow_html=True)
            else:
                st.success("✅ 모든 샘플이 합격 범위 내에 있습니다.")

            st.dataframe(df[['측정포인트', '위치도', '보너스', '최종공차', '판정']])

        except Exception as e:
            st.error(f"데이터 형식을 확인해주세요: {e}")

if __name__ == "__main__":
    run_position_analysis()
