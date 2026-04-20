import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v6.8", layout="wide")

# --- 2. [오류 방지 핵심] 데이터 로드 및 열 이름 강제 보정 함수 ---
def safe_load_data(file):
    if file.name.endswith('.xlsx'):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file)
    
    # 모든 열 이름의 공백 제거 및 대문자 변환하여 비교
    df.columns = [str(c).strip() for c in df.columns]
    col_map = {c.upper(): c for c in df.columns}

    # Point 열 찾기 (없으면 첫 번째 열 사용)
    if 'POINT' in col_map:
        df.rename(columns={col_map['POINT']: 'Point'}, inplace=True)
    else:
        df.rename(columns={df.columns[0]: 'Point'}, inplace=True)

    # SPEC_MIN 찾기
    spec_min_col = next((c for c in df.columns if 'MIN' in c.upper()), None)
    if spec_min_col:
        df.rename(columns={spec_min_col: 'SPEC_MIN'}, inplace=True)
    else:
        # SPEC_MIN이 아예 없으면 데이터 최소값 기준으로 임의 생성 (에러 방지)
        df['SPEC_MIN'] = df.iloc[:, 1:].min().min() * 0.99

    # SPEC_MAX 찾기
    spec_max_col = next((c for c in df.columns if 'MAX' in c.upper()), None)
    if spec_max_col:
        df.rename(columns={spec_max_col: 'SPEC_MAX'}, inplace=True)
    else:
        df['SPEC_MAX'] = df.iloc[:, 1:].max().max() * 1.01

    return df

# --- 3. UI 및 템플릿 (요구사항 유지) ---
def get_main_template():
    points = list(range(1, 55))
    spec_min = [30.03] * 54
    spec_max = [30.38] * 54
    df_temp = pd.DataFrame({
        "Point": points, "SPEC_MIN": spec_min, "SPEC_MAX": spec_max,
        "Cavity_1": [30.2]*54, "Cavity_2": [30.25]*54, "Cavity_3": [30.15]*54, "Cavity_4": [30.3]*54
    })
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_temp.to_excel(writer, index=False)
    return output.getvalue()

st.title("📊 핀 높이 멀티 캐비티 정밀 분석")

col_file, col_temp = st.columns([3, 1])
with col_temp:
    st.download_button("📄 정석 템플릿 다운로드", get_main_template(), "Template_v6.8.xlsx", use_container_width=True)
with col_file:
    uploaded_file = st.file_uploader("분석 파일 업로드", type=["xlsx", "csv"], label_visibility="collapsed")

# --- 4. 메인 분석 로직 ---
if uploaded_file:
    try:
        # 안전하게 데이터 로드
        df = safe_load_data(uploaded_file)
        
        # 캐비티 열 인식
        cav_cols = [c for c in df.columns if 'CAV' in c.upper()]
        
        if not cav_cols:
            st.error("❌ 'Cavity' 또는 'Cav' 문구가 포함된 데이터 열을 찾을 수 없습니다.")
            st.stop()

        # 정밀 Y축 범위 계산
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_range = [float(all_vals.min()) - 0.02, float(all_vals.max()) + 0.02]

        # --- 통합 그래프 ---
        st.markdown('<div style="background-color:white; padding:20px; border-radius:10px; border:1px solid #ddd;">', unsafe_allow_html=True)
        st.subheader("🌐 전 캐비티 통합 경향성 분석")
        
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="SPEC MIN", line=dict(color="blue", dash="dash")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="SPEC MAX", line=dict(color="red", dash="dash")))

        # 평균 트렌드선
        df['Average'] = df[cav_cols].mean(axis=1)
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Average'], name="평균 Trend", line=dict(color="black", width=3)))

        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], name=cav, mode='markers', 
                                           marker=dict(size=8, color=cav_colors[i % 4], opacity=0.5)))

        fig_total.update_layout(yaxis_range=y_range, height=550, template="plotly_white", hovermode="x unified")
        st.plotly_chart(fig_total, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- 상세 및 요약 대쉬보드 ---
        st.subheader("🔍 캐비티별 상세 및 요약")
        sum_cols = st.columns(len(cav_cols))
        
        for i, cav in enumerate(cav_cols):
            ng_cnt = len(df[df[f"{cav}_판정"] == "NG"])
            rate = ((len(df) - ng_cnt) / len(df)) * 100
            with sum_cols[i]:
                st.metric(cav, f"{rate:.1f}%", f"NG: {ng_cnt}건", delta_color="inverse")

    except Exception as e:
        st.error(f"데이터 분석 중 오류 발생: {e}")
