import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from io import BytesIO

# --- 1. 페이지 설정 및 라이브러리 체크 ---
st.set_page_config(page_title="멀티 캐비티 분석", layout="wide")

# 라이브러리 미설치 대비 기본 엔진 설정
try:
    import xlsxwriter
    engine = 'xlsxwriter'
except ImportError:
    engine = None

# --- 2. 스타일 ---
st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .guide-box { background-color: #f0f9ff; padding: 15px; border-radius: 10px; border-left: 5px solid #0ea5e9; color: #0c4a6e; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 멀티 캐비티 핀 높이 통합 분석")

# --- 3. 템플릿 생성 함수 (에러 방지를 위한 내부 정의) ---
def get_template():
    # 이미지 1번과 유사한 54개 포인트 구조
    points = list(range(1, 55))
    # 예시 SPEC: 1~6번은 다름, 나머지는 동일 (이미지 참조)
    spec_min = [30.35 if p <= 6 or 15 <= p <= 20 or p in [36, 37, 53, 54] else 30.03 for p in points]
    spec_max = [30.70 if p <= 6 or 15 <= p <= 20 or p in [36, 37, 53, 54] else 30.38 for p in points]
    
    df_temp = pd.DataFrame({
        "Point": points,
        "SPEC_MIN": spec_min,
        "SPEC_MAX": spec_max,
        "Cavity_1": [30.5] * 54,
        "Cavity_2": [30.4] * 54,
        "Cavity_3": [30.45] * 54,
        "Cavity_4": [30.55] * 54
    })
    output = BytesIO()
    if engine:
        with pd.ExcelWriter(output, engine=engine) as writer:
            df_temp.to_excel(writer, index=False)
    else:
        df_temp.to_csv(output, index=False)
    return output.getvalue()

# --- 4. 파일 업로드 섹션 ---
st.markdown('<div class="stBox">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])
with col1:
    st.download_button("📄 새 템플릿 다운로드", get_template(), "Template.xlsx", use_container_width=True)
with col2:
    uploaded_file = st.file_uploader("분석 파일(CSV/XLSX) 업로드", type=["xlsx", "csv"], label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    # 데이터 읽기
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # 실측 데이터 컬럼 자동 식별 (Cavity라는 글자가 들어간 열들)
        cav_cols = [c for c in df.columns if 'Cavity' in c]
        
        if not cav_cols:
            st.error("⚠️ 파일에 'Cavity'로 시작하는 열이 없습니다. 템플릿을 확인해주세요.")
        else:
            # --- 5. 통합 비교 그래프 (이미지 2 스타일) ---
            st.markdown('<div class="stBox">', unsafe_allow_html=True)
            st.subheader("📊 전 캐비티 통합 경향성 분석")
            
            # Y축 범위 계산
            all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
            y_range = [all_vals.min() - 0.1, all_vals.max() + 0.1]

            fig_total = go.Figure()
            # SPEC 라인 (계단형으로 그려서 이미지 2와 동일하게 구현)
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="SPEC MIN", line=dict(color="#2563eb", width=2, dash="dash"), mode="lines"))
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="SPEC MAX", line=dict(color="#dc2626", width=2, dash="dash"), mode="lines"))
            
            # 각 캐비티 데이터 중첩
            for col in cav_cols:
                fig_total.add_trace(go.Scatter(x=df["Point"], y=df[col], name=col, mode="lines+markers", marker=dict(size=6)))
            
            fig_total.update_layout(yaxis_range=y_range, height=600, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_total, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # --- 6. 개별 캐비티 상세 분석 (2개씩 배치) ---
            st.subheader("🔍 캐비티별 개별 판정")
            grid = st.columns(2)
            
            for i, cav in enumerate(cav_cols):
                with grid[i % 2]:
                    st.markdown('<div class="stBox">', unsafe_allow_html=True)
                    st.write(f"**{cav} 분석**")
                    
                    # NG 판정 (하나라도 범위 밖이면 빨간색)
                    df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
                    
                    fig_ind = go.Figure()
                    fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", width=1), showlegend=False))
                    fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", width=1), showlegend=False))
                    # 측정값 막대 그래프
                    fig_ind.add_trace(go.Bar(x=df["Point"], y=df[cav], 
                                             marker_color=['red' if p == "NG" else "#3b82f6" for p in df[f"{cav}_판정"]]))
                    
                    fig_ind.update_layout(yaxis_range=y_range, height=350, margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(fig_ind, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
    except Exception as e:
        st.error(f"❌ 에러 발생: {e}")
        st.info("파일 형식이나 컬럼명(Point, SPEC_MIN, SPEC_MAX, Cavity_1...)이 템플릿과 일치하는지 확인해주세요.")
