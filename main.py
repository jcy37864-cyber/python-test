import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="품질 통합 분석 시스템", layout="wide")

# --- [수정 포인트] 데이터 읽기 및 열 이름 자동 보정 함수 ---
def load_and_fix_data(file):
    if file.name.endswith('.xlsx'):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file)
    
    # 열 이름의 공백 제거
    df.columns = [str(c).strip() for c in df.columns]
    
    # 1. 'Point' 열이 없는 경우 첫 번째 열을 Point로 지정
    if 'Point' not in df.columns:
        st.warning("⚠️ 'Point' 열을 찾을 수 없어 첫 번째 열을 위치 데이터로 사용합니다.")
        df.rename(columns={df.columns[0]: 'Point'}, inplace=True)
    
    # 2. SPEC 열 자동 찾기 (이름이 완벽하지 않아도 대응)
    for col in df.columns:
        if 'MIN' in col.upper(): df.rename(columns={col: 'SPEC_MIN'}, inplace=True)
        if 'MAX' in col.upper(): df.rename(columns={col: 'SPEC_MAX'}, inplace=True)
    
    return df

# --- UI 부분 ---
st.title("📊 핀 높이 멀티 캐비티 분석 (오류 수정본)")

with st.expander("📂 데이터 업로드", expanded=True):
    uploaded_file = st.file_uploader("분석 파일을 선택하세요", type=["xlsx", "csv"])

if uploaded_file:
    try:
        df = load_and_fix_data(uploaded_file)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        
        if 'SPEC_MIN' not in df.columns or 'SPEC_MAX' not in df.columns:
            st.error("❌ 파일에 SPEC_MIN, SPEC_MAX 열이 필요합니다.")
            st.stop()

        # 캐비티 색상 설정
        cav_colors = {'Cavity_1': '#1f77b4', 'Cavity_2': '#ff7f0e', 'Cavity_3': '#2ca02c', 'Cavity_4': '#9467bd'}

        # --- 1. 통합 산포도 ---
        st.subheader("🌐 전 캐비티 통합 산포도")
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="SPEC MIN", line=dict(color="#2563eb", dash="dash")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="SPEC MAX", line=dict(color="#dc2626", dash="dash")))

        for cav in cav_cols:
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            color = cav_colors.get(cav, '#7f7f7f')
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], name=cav, mode='markers', marker=dict(size=9, color=color, opacity=0.7)))
            
            # NG 강조 (테두리)
            ng_df = df[df[f"{cav}_판정"] == "NG"]
            if not ng_df.empty:
                fig_total.add_trace(go.Scatter(x=ng_df["Point"], y=ng_df[cav], mode='markers', 
                                               marker=dict(size=12, color='rgba(0,0,0,0)', line=dict(width=2, color='red')), 
                                               showlegend=False))

        st.plotly_chart(fig_total, use_container_width=True)

        # --- 2. 개별 그래프 및 요약 ---
        st.subheader("🔍 캐비티별 상세 분석")
        cols = st.columns(2)
        summary_data = []

        for i, cav in enumerate(cav_cols):
            with cols[i % 2]:
                st.write(f"### {cav}")
                fig_ind = go.Figure()
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue"), showlegend=False))
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red"), showlegend=False))
                
                b_colors = ['#ef4444' if p == "NG" else cav_colors.get(cav, '#3b82f6') for p in df[f"{cav}_판정"]]
                fig_ind.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=b_colors))
                st.plotly_chart(fig_ind, use_container_width=True)
                
                ng_cnt = len(df[df[f"{cav}_판정"] == "NG"])
                summary_data.append({"cav": cav, "ng": ng_cnt, "rate": ((len(df)-ng_cnt)/len(df))*100})

        # --- 3. 하단 요약 ---
        st.markdown("---")
        s_cols = st.columns(len(summary_data))
        for i, s in enumerate(summary_data):
            s_cols[i].metric(s['cav'], f"{s['rate']:.1f}%", f"NG: {s['ng']}개", delta_color="inverse")

    except Exception as e:
        st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
