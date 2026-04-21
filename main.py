import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.subheader("🎯 위치도 정밀 분석 (통합 양식 대응)")

    # 1. 설정 영역
    with st.expander("⚙️ 분석 기준 설정", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수 (1.nmp ~ 4.nmp 기준 4)", min_value=1, value=4, key="sc_v_final")
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="tol_v_final")
        with col2:
            mmc_ref = st.number_input("MMC 기준치 (해당 시)", value=0.060, format="%.3f", key="mmc_v_final")
        with col3:
            view_mode = st.radio("그래프 범위", ["자동(권장)", "수동 조절"], horizontal=True, key="mode_v_final")
            
    # 2. 데이터 입력 및 변환 버튼
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=250, placeholder="Nominal 열부터 끝까지 복사해서 넣어주세요.")
    
    analyze_button = st.button("📊 데이터 분석 시작", type="primary", use_container_width=True)

    if analyze_button:
        if not raw_input:
            st.warning("⚠️ 데이터를 입력해주세요.")
            return

        try:
            lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
            all_nums = []
            for line in lines:
                nums = [float(n.replace(',', '')) for n in re.findall(r'[-+]?\d*\.\d+|\d+', line)]
                if nums: all_nums.append(nums)

            results = []
            
            # --- [양식 판별 및 데이터 추출] ---
            # image_82f803 양식: 한 세트가 위치도, MMC공차, Y값 순서로 들어올 때
            for i in range(len(all_nums)):
                row = all_nums[i]
                # 샘플 수보다 숫자가 많고, 위치도 수치(0.35 등)가 포함된 행 찾기
                if len(row) >= sc:
                    # 해당 줄의 마지막 sc개의 숫자가 측정 데이터라고 가정
                    samples = row[-sc:] 
                    
                    # 만약 다음 줄이 MMC공차 줄이라면 보너스 계산에 활용
                    bonus_vals = [0.0] * sc
                    if i + 1 < len(all_nums) and len(all_nums[i+1]) >= sc:
                        # MMC공차 행에서 기준치(mmc_ref)를 뺀 값을 보너스로 인식
                        bonus_vals = [(max(0, b - mmc_ref)) for b in all_nums[i+1][-sc:]]

                    for s in range(sc):
                        pos_val = samples[s]
                        results.append({
                            "측정포인트": f"P{len(results)//sc + 1}_S{s+1}",
                            "위치도": pos_val,
                            "최종공차": tol + bonus_vals[s],
                            "편차_X": (pos_val / 4), # 좌표가 없을 경우 시각화를 위해 분산 배치
                            "편차_Y": (pos_val / 4) * (1 if s%2==0 else -1)
                        })
                
                # 중복 계산 방지를 위해 포인트 단위로 점프 (이 양식은 3행이 한 세트)
                if len(results) % sc == 0 and len(results) > 0:
                    continue

            df = pd.DataFrame(results).drop_duplicates(subset=['측정포인트']).head(sc * 10) # 최대 10포인트
            df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

            # 4. 시각화 범위
            max_val = df['최종공차'].max()
            view_limit = (max_val / 2 * 1.5) if view_mode == "자동(권장)" else st.slider("줌 조절", 0.1, 5.0, 0.5)

            # 5. 그래프
            fig = go.Figure()
            fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, line=dict(color="RoyalBlue", width=2))
            fig.add_shape(type="circle", x0=-max_val/2, y0=-max_val/2, x1=max_val/2, y1=max_val/2, line=dict(color="Red", width=2, dash="dot"))

            for res in ["✅ OK", "❌ NG"]:
                sub = df[df['판정'] == res]
                if not sub.empty:
                    fig.add_trace(go.Scatter(x=sub['편차_X'], y=sub['편차_Y'], mode='markers+text', name=res, 
                                             text=sub['측정포인트'], marker=dict(size=10, color="#2ecc71" if res=="✅ OK" else "#e74c3c")))

            fig.update_layout(width=600, height=600, xaxis=dict(range=[-view_limit, view_limit]), yaxis=dict(range=[-view_limit, view_limit]))
            st.plotly_chart(fig)

            # 6. 리스트 출력
            ng_list = df[df['판정'] == "❌ NG"]
            if not ng_list.empty:
                st.error("🚨 규격 이탈 리스트")
                st.dataframe(ng_list[['측정포인트', '위치도', '최종공차', '판정']])
            else:
                st.success("✅ 모든 데이터 합격")
            
            st.dataframe(df[['측정포인트', '위치도', '최종공차', '판정']])

        except Exception as e:
            st.error(f"데이터 인식 오류. 양식을 확인해주세요: {e}")

if __name__ == "__main__":
    run_position_analysis()
