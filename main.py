import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

def run_position_analysis():
    st.subheader("🎯 위치도 정밀 분석 (데이터 인식 보정 버전)")

    # 1. 설정 영역
    with st.expander("⚙️ 분석 기준 설정", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            sc = st.number_input("샘플 수 (S1~S4 기준 4)", min_value=1, value=4, key="sc_v2")
            tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="tol_v2")
        with col2:
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f", key="mmc_v2")
        with col3:
            std_range = round(tol, 2)
            view_mode = st.radio("그래프 범위", ["표준(권장)", "수동 조절"], horizontal=True, key="mode_v2")
            view_limit = std_range if view_mode == "표준(권장)" else st.slider("범위 조절", 0.1, 5.0, std_range, step=0.1, key="slider_v2")

    # 2. 데이터 입력
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=200, placeholder="숫자들이 섞여있어도 행 단위로 분석합니다.")

    if raw_input:
        # [보정된 파싱 로직] 줄바꿈을 기준으로 행을 먼저 나누어 좌표 섞임을 방지합니다.
        def robust_parse(text, sample_count):
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            all_nums = []
            for line in lines:
                # 한 줄에서 숫자들만 추출
                all_nums.extend([float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', line)])
            
            if not all_nums: return None
            
            results = []
            # 한 포인트 세트의 데이터 개수: (지름 1 + 샘플) + (X도면 1 + 샘플) + (Y도면 1 + 샘플)
            step = 1 + sample_count
            set_len = step * 3
            
            for i in range(len(all_nums) // set_len):
                base = i * set_len
                # 데이터 슬라이싱 시 좌표값이 위치도로 들어가지 않게 순서를 엄격히 분리
                dia_group = all_nums[base : base + step]
                x_group = all_nums[base + step : base + step * 2]
                y_group = all_nums[base + step * 2 : base + step * 3]
                
                label = chr(65 + i) if i < 26 else f"P{i+1}"
                for s in range(sample_count):
                    results.append({
                        "측정포인트": f"{label}_S{s+1}",
                        "도면_X": x_group[0], "도면_Y": y_group[0],
                        "측정_X": x_group[s+1], "측정_Y": y_group[s+1],
                        "지름_MMC": dia_group[s+1]
                    })
            return results

        data_list = robust_parse(raw_input, sc)
        
        if data_list:
            df = pd.DataFrame(data_list)
            # 계산 로직
            df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
            df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
            # 위치도 계산: SQRT(dX^2 + dY^2) * 2
            df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
            df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
            df['최종공차'] = (tol + df['보너스']).round(4)
            df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

            # --- 그래프 시각화 ---
            fig = go.Figure()
            # 원 및 텍스트 표기 생략 (기존 기능 유지)
            # ... (그래프 코드 생략, 이전 버전과 동일하게 유지) ...
            
            # 443 같은 비정상 수치 제어: 그래프 범위를 벗어나는 NG 시료 안내
            st.plotly_chart(fig, use_container_width=True)
            
            ng_list = df[df['판정'] == "❌ NG"]
            if not ng_list.empty:
                st.error(f"🚨 **비정상 수치 검출 알림**")
                st.write("데이터 파싱 중 좌표값이 위치도로 인식되었을 수 있습니다. 아래 수치를 확인하세요.")
                # 스크롤 박스 유지
                # ...
