import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.subheader("🎯 위치도 정밀 분석 (최종 완결판)")

    # 1. 설정 영역
    with st.expander("⚙️ 분석 기준 설정", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수 (한 줄당 데이터 개수)", min_value=1, value=4, key="sc_v_final")
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="tol_v_final")
        with col2:
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f", key="mmc_v_final")
        with col3:
            view_mode = st.radio("그래프 범위", ["자동(권장)", "수동 조절"], horizontal=True, key="mode_v_final")
            
    # 2. 데이터 입력 및 [변환 버튼] 생성
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=200, placeholder="이미지의 표 내용을 그대로 복사해서 넣어주세요.")
    
    # --- [핵심: 변환 버튼 추가] ---
    analyze_button = st.button("📊 데이터 분석 시작", type="primary", use_container_width=True)

    # 버튼을 눌렀을 때만 아래 로직이 실행됩니다.
    if analyze_button:
        if not raw_input:
            st.warning("⚠️ 입력된 데이터가 없습니다. 성적서 내용을 붙여넣어 주세요.")
            return

        try:
            # 3. 데이터 분석 로직 (정밀 파싱)
            lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
            rows = []
            for line in lines:
                nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', line)]
                if nums: rows.append(nums)

            results = []
            # 3줄 세트(지름, X, Y)로 분석
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

            # 4. 범위 결정 (자동/수동)
            max_total_tol = df['최종공차'].max()
            auto_limit = round((max_total_tol / 2) * 1.2, 2)
            
            if view_mode == "자동(권장)":
                view_limit = auto_limit
            else:
                view_limit = st.slider("줌 조절 (±mm)", 0.1, 5.0, 0.5, step=0.1, key="zoom_final")

            # 5. 그래프 시각화
            fig = go.Figure()
            r_blue, r_red = tol / 2, max_total_tol / 2
            
            # 파란 원(기본), 빨간 원(최대 MMC)
            fig.add_shape(type="circle", x0=-r_blue, y0=-r_blue, x1=r_blue, y1=r_blue, line=dict(color="RoyalBlue", width=2.5), fillcolor="rgba(65, 105, 225, 0.05)")
            fig.add_shape(type="circle", x0=-r_red, y0=-r_red, x1=r_red, y1=r_red, line=dict(color="Red", width=2, dash="dot"))

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

            # 6. 결과 리포트 및 NG 스크롤 박스
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
            st.error(f"데이터 형식을 다시 확인해주세요. (지름/X/Y 3줄 세트 필수): {e}")

if __name__ == "__main__":
    run_position_analysis()
