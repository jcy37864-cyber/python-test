import streamlit as st
import pandas as pd
import numpy as np
import re

# 1. 앱 제목 및 기본 설정
st.set_page_config(page_title="품질 분석기", layout="wide")
st.title("🎯 덕인 위치도 분석 (서버 복구용)")

# 2. 사이드바 입력 설정 (계산 기준)
with st.sidebar:
    st.header("⚙️ 기준 설정")
    sc = st.number_input("샘플 수 (S1~S4면 4)", min_value=1, value=4)
    mmc_ref = st.number_input("MMC 기준값", value=0.350, format="%.3f")
    tol_ref = st.number_input("기본 공차값", value=0.350, format="%.3f")

# 3. 데이터 입력창
raw_input = st.text_area("성적서 데이터를 전체 복사해서 붙여넣으세요", height=300)

# 4. 분석 실행
if st.button("🚀 분석 시작"):
    if not raw_input:
        st.warning("데이터를 입력해 주세요.")
    else:
        try:
            # 모든 숫자만 추출
            nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', raw_input)]
            step = 1 + sc # 도면1 + 샘플n
            
            if len(nums) < step * 3:
                st.error(f"데이터가 부족합니다. (현재 숫자 {len(nums)}개 발견)")
            else:
                data = []
                # 3개 행(P, X, Y)을 한 세트로 묶어서 처리
                for i in range(len(nums) // (step * 3)):
                    base = i * (step * 3)
                    p = nums[base : base + step]
                    x = nums[base + step : base + step * 2]
                    y = nums[base + step * 2 : base + step * 3]
                    
                    for s in range(sc):
                        data.append({
                            "ID": f"{chr(65+i)}_S{s+1}",
                            "X_도면": x[0], "Y_도면": y[0],
                            "X_실측": x[s+1], "Y_실측": y[s+1], "지름": p[s+1]
                        })
                
                # 데이터프레임 생성 및 계산
                df = pd.DataFrame(data)
                # 위치도 = 2 * SQRT( (X실측-X도면)^2 + (Y실측-Y도면)^2 )
                df['위치도'] = (2 * np.sqrt((df['X_실측']-df['X_도면'])**2 + (df['Y_실측']-df['Y_도면'])**2)).round(4)
                df['보너스'] = (df['지름'] - mmc_ref).clip(lower=0).round(4)
                df['최종공차'] = (tol_ref + df['보너스']).round(4)
                df['판정'] = np.where(df['위치도'] <= df['최종공차'], "OK", "NG")
                
                st.success("✅ 분석 완료!")
                st.dataframe(df, use_container_width=True)
                
                # CSV 다운로드 (가장 안전한 저장 방식)
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 결과 다운로드 (CSV)", csv, "result.csv", "text/csv")
                
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")
