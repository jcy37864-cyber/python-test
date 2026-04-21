import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.subheader("🎯 위치도 정밀 분석 (데이터 정제 강화 버전)")

    # 1. 설정 영역
    with st.expander("⚙️ 분석 기준 설정", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수 (S1~S4 기준 4)", min_value=1, value=4, key="sc_final_v3")
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="tol_final_v3")
        with col2:
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f", key="mmc_final_v3")
        with col3:
            std_range = round(tol, 2)
            view_mode = st.radio("그래프 범위", ["표준(권장)", "수동 조절"], horizontal=True, key="mode_final_v3")
            view_limit = std_range if view_mode == "표준(권장)" else st.slider("범위 조절(±mm)", 0.1, 5.0, std_range, step=0.1, key="zoom_final_v3")

    # 2. 데이터 입력
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=200, placeholder="숫자 데이터를 입력해주세요.")

    if not raw_input:
        st.info("💡 데이터를 입력하면 실시간으로 분석 그래프가 생성됩니다.")
        return

    # 3. 데이터 분석 및 계산
    try:
        # 모든 숫자 추출 (소수점 포함)
        nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', raw_input)]
        
        step = 1 + sc  # 도면값1 + 샘플수 (예: 1+4=5)
        set_len = step * 3  # 지름, X, Y 세 그룹 (예: 5*3=15개 숫자가 한 세트)

        if len(nums) < set_len:
            st.warning(f"데이터가 부족합니다. 한 포인트당 최소 {set_len}개의 숫자가 필요합니다.")
            return

        results = []
        # 데이터가 남지 않도록 정확히 세트 단위로만 분석
        for i in range(len(nums) // set_len):
            base = i * set_len
            try:
                # [중요] 그룹별 슬라이싱을 명확히 함
                dia_group = nums[base : base + step]
                x_group = nums[base + step : base + step * 2]
                y_group = nums[base + step * 2 : base + step * 3]
                
                label = chr(65 + i) if i < 26 else f"P{i+1}"
                for s in range(sc):
                    results.append({
                        "측정포인트": f"{label}_S{s+1}",
                        "도면_X": x_group[0], "도면_Y": y_group[0],
                        "측정_X": x_group[s+1], "측정_Y": y_group[s+1],
                        "지름_MMC": dia_group[s+1]
                    })
            except IndexError:
                break
        
        if not results:
            st.error("데이터 매칭 실패. 입력 데이터의 개수를 확인해주세요.")
            return

        df = pd.DataFrame(results)
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
        df['최종공차'] = (tol + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        # 4. 시각화 및 NG 리스트 출력
        # (기존의 그래프 코드는 그대로 유지하되, NG 리스트에서 튀는 값 경고 추가)
        
        # [그래프 생성 부분 - 이전과 동일]
        fig = go.Figure()
        r_blue = tol / 2
        fig.add_shape(type="circle", x0=-r_blue, y0=-r_blue, x1=r_blue, y1=r_blue, line=dict(color="RoyalBlue", width=2.5))
        
        max_total_tol = df['최종공차'].max()
        r_red = max_total_tol / 2
        display_r_red = min(r_red, view_limit * 0.98)
        fig.add_shape(type="circle", x0=-display_r_red, y0=-display_r_red, x1=display_r_red, y1=display_r_red, line=dict(color="Red", width=2, dash="dot"))

        # [타점 표시]
        for res in ["✅ OK", "❌ NG"]:
            sub = df[df['판정'] == res]
            vis = sub[(sub['편차_X'].abs() <= view_limit) & (sub['편차_Y'].abs() <= view_limit)]
            if not vis.empty:
                fig.add_trace(go.Scatter(x=vis['편차_X'], y=vis['편차_Y'], mode='markers+text', name=res, text=vis['측정포인트'], marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c")))

        fig.update_layout(width=700, height=700, xaxis=dict(range=[-view_limit, view_limit]), yaxis=dict(range=[-view_limit, view_limit]))
        st.plotly_chart(fig, use_container_width=True)

        # 5. NG 스크롤 리스트 (비정상 수치 경고 추가)
        ng_list = df[df['판정'] == "❌ NG"]
        if not ng_list.empty:
            st.error(f"🚨 **규격 이탈(NG) 리스트**")
            ng_html_content = ""
            for _, row in ng_list.iterrows():
                excess = row['위치도'] - row['최종공차']
                # 10mm 초과 시 데이터 입력 순서 오류 경고
                error_hint = " <br><span style='font-size:12px; color:blue;'>⚠️ 좌표값이 위치도로 인식된 것 같습니다. 데이터 순서를 확인하세요.</span>" if row['위치도'] > 10 else ""
                ng_html_content += f"<p style='color: #d32f2f; margin: 8px 0;'>• <b>{row['측정포인트']}</b>: {row['위치도']:.3f} (규격 Ø{row['최종공차']:.3f} 대비 {excess:.3f} 초과){error_hint}</p>"
            
            st.markdown(f"""<div style='height: 200px; overflow-y: auto; border: 1px solid #ff4b4b; padding: 10px; border-radius: 5px; background-color: #fff5f5;'>{ng_html_content}</div>""", unsafe_allow_html=True)
        
        st.dataframe(df[['측정포인트', '위치도', '최종공차', '판정']])

    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")

# 실행
if __name__ == "__main__":
    run_position_analysis()
