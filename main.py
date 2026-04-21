import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import re
from io import BytesIO

# ==========================================
# 1. 전역 설정 및 스타일
# ==========================================
def set_global_style():
    st.set_page_config(page_title="덕인 품질 분석 시스템 v10.5", layout="wide")
    st.markdown("""
        <style>
        .stApp { background-color: #f8fafc; }
        .stButton > button { 
            background-color: #ef4444 !important; color: white !important; 
            border-radius: 8px; width: 100%; font-weight: bold;
        }
        .stBox { 
            background-color: #ffffff; padding: 20px; border-radius: 12px; 
            border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)

def clean_float(value):
    try:
        cleaned = re.findall(r"[-+]?\d*\.\d+|\d+", str(value))
        return float(cleaned[0]) if cleaned else 0.0
    except:
        return 0.0

# ==========================================
# 2. 핵심 로직: 유연한 데이터 파서
# ==========================================
def parse_smart_data(raw_text, sample_count):
    # 모든 숫자(실수 포함)만 추출
    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', raw_text)]
    
    results = []
    # 한 세트의 길이: 지름(1+샘플수) + X(1+샘플수) + Y(1+샘플수)
    step = 1 + sample_count
    set_len = step * 3
    
    for i in range(len(nums) // set_len):
        base = i * set_len
        # 슬라이싱을 통한 정확한 데이터 배분
        dia_part = nums[base : base + step]
        x_part = nums[base + step : base + step * 2]
        y_part = nums[base + step * 2 : base + step * 3]
        
        label = chr(65 + i) if i < 26 else f"P{i+1}"
        
        for s in range(sample_count):
            results.append({
                "측정포인트": f"{label}_S{s+1}",
                "도면치수_X": x_part[0],
                "도면치수_Y": y_part[0],
                "측정치_X": x_part[s+1],
                "측정치_Y": y_part[s+1],
                "실측지름_MMC용": dia_part[s+1],
                "기본공차": 0.350
            })
    return results

# ==========================================
# 3. 메뉴별 실행 함수
# ==========================================

def run_data_converter():
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.header("📁 Step 1. 성적서 데이터 변환")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        sample_count = st.number_input("🔢 샘플 수 (S1~S4면 4 입력)", min_value=1, value=4)
    with col2:
        st.info("💡 데이터의 Nominal부터 마지막 실측값까지 모두 복사해 붙여넣으세요.")

    raw_data = st.text_area("성적서 데이터 붙여넣기", height=250, placeholder="데이터를 여기에 붙여넣으세요...")

    if st.button("🚀 데이터 분석 준비") and raw_data:
        data_list = parse_smart_data(raw_data, sample_count)
        if data_list:
            df = pd.DataFrame(data_list)
            st.session_state.data = df
            st.success(f"✅ {len(df)}개의 측정 데이터를 성공적으로 읽어왔습니다!")
            st.dataframe(df, use_container_width=True)
        else:
            st.error("❌ 데이터를 해석할 수 없습니다. 형식을 확인해주세요.")
    st.markdown('</div>', unsafe_allow_html=True)

def run_position_analysis():
    st.header("📊 Step 2. 위치도 결과 분석")
    if 'data' not in st.session_state or st.session_state.data is None:
        st.warning("⚠️ Step 1에서 데이터를 먼저 입력해주세요.")
        return

    df = st.session_state.data.copy()
    
    col_set1, col_set2 = st.columns(2)
    with col_set1:
        mmc_ref = st.number_input("📏 MMC 기준값 (최대 실체 지름)", value=0.350, format="%.3f")
    with col_set2:
        tol_ref = st.number_input("🎯 기본 위치도 공차(Ø)", value=0.350, format="%.3f")

    # 계산 로직
    df['위치도결과'] = (np.sqrt((df['측정치_X'] - df['도면치수_X'])**2 + (df['측정치_Y'] - df['도면치수_Y'])**2) * 2).round(4)
    df['보너스'] = (df['실측지름_MMC용'] - mmc_ref).clip(lower=0).round(4)
    df['최종공차'] = (tol_ref + df['보너스']).round(4)
    df['판정'] = np.where(df['위치도결과'] <= df['최종공차'], "✅ OK", "❌ NG")

    st.subheader("📝 상세 분석 리포트")
    st.dataframe(df.style.apply(lambda x: ['background-color: #DFF2BF' if v == '✅ OK' else 'background-color: #FFBABA' for v in x], subset=['판정']), use_container_width=True)

    # --- 🎯 과녁 그래프 (Plotly 버전: 가시성 최상) ---
    st.divider()
    st.subheader("🎯 위치도 산포도 (과녁 분석)")
    
    dev_x = df['측정치_X'] - df['도면치수_X']
    dev_y = df['측정치_Y'] - df['도면치수_Y']
    
    fig = go.Figure()

    # 1. 파란색 공차 영역 원 (기본공차)
    r = tol_ref / 2
    fig.add_shape(type="circle", x0=-r, y0=-r, x1=r, y1=r, 
                  line=dict(color="RoyalBlue", width=2, dash="dash"),
                  fillcolor="rgba(52, 152, 219, 0.2)", layer="below")

    # 2. 측정 점 찍기
    for p_type, color in [("✅ OK", "#2ecc71"), ("❌ NG", "#e74c3c")]:
        sub = df[df['판정'] == p_type]
        if not sub.empty:
            fig.add_trace(go.Scatter(
                x=sub['측정치_X'] - sub['도면치수_X'], 
                y=sub['측정치_Y'] - sub['도면_Y'] if '도면_Y' in sub else sub['측정치_Y'] - sub['도면치수_Y'],
                mode='markers', name=p_type,
                marker=dict(size=10, color=color, line=dict(width=1, color='white')),
                text=sub['측정포인트']
            ))

    # 3. 그래프 레이아웃 (축 스케일 자동 조정)
    max_dev = max(dev_x.abs().max(), dev_y.abs().max(), r * 1.5)
    fig.update_layout(
        width=700, height=700,
        xaxis=dict(range=[-max_dev*1.2, max_dev*1.2], zeroline=True, zerolinecolor='black'),
        yaxis=dict(range=[-max_dev*1.2, max_dev*1.2], zeroline=True, zerolinecolor='black'),
        showlegend=True, plot_bgcolor='white',
        title=f"중앙 파란 영역: 기본 공차범위 (Ø{tol_ref})"
    )
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 4. 메인 실행부
# ==========================================
def main():
    set_global_style()
    
    st.sidebar.title("💎 QUALITY HUB v10.5")
    menu = st.sidebar.radio("📂 분석 메뉴", ["🎯 위치도 정밀 분석", "📈 멀티 캐비티 분석", "🧮 품질 계산기"])

    if menu == "🎯 위치도 정밀 분석":
        st.title("🎯 위치도 정밀 분석 시스템")
        t1, t2 = st.tabs(["📁 데이터 변환 (Step 1)", "📊 결과 분석 (Step 2)"])
        with t1: run_data_converter()
        with t2: run_position_analysis()
    
    elif menu == "📈 멀티 캐비티 분석":
        st.info("준비 중인 기능입니다.") # 기존 코드의 cavity 분석 함수를 연결하세요.

    elif menu == "🧮 품질 계산기":
        from run_quality_calculator import run_quality_calculator # 필요시 분리된 파일 호출
        st.success("계산기 모드 활성화")

if __name__ == "__main__":
    main()
