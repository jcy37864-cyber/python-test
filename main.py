Python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="멀티 캐비티 품질 분석 시스템", layout="wide")

# 2. 스타일 설정
st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
    .guide-box { background-color: #f0f9ff; padding: 15px; border-radius: 10px; border-left: 5px solid #0ea5e9; color: #0c4a6e; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 멀티 캐비티 핀 높이 분석 시스템")

st.markdown("""
    <div class="guide-box">
        <b>💡 다중 데이터 분석 가이드:</b> 4개 캐비티의 데이터를 동시에 분석합니다.<br>
        1. 템플릿을 다운로드하여 핀별 SPEC과 각 캐비티 실측치를 입력하세요.<br>
        2. 파일을 업로드하면 <b>캐비티별 개별 그래프</b>와 <b>통합 비교 그래프</b>가 생성됩니다.
    </div>
""", unsafe_allow_html=True)

# 3. 신규 템플릿 생성 (포인트별 다중 데이터 구조)
def create_template():
    # 이미지 1번의 54개 포인트 구조 예시
    df_temp = pd.DataFrame({
        "Point": range(1, 55),
        "SPEC_MIN": [30.35 if i <= 6 else 30.03 for i in range(1, 55)], # 예시 SPEC
        "SPEC_MAX": [30.70 if i <= 6 else 30.38 for i in range(1, 55)], # 예시 SPEC
        "Cavity_1": [0.0] * 54,
        "Cavity_2": [0.0] * 54,
        "Cavity_3": [0.0] * 54,
        "Cavity_4": [0.0] * 54
    })
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_temp.to_excel(writer, index=False, sheet_name='Data')
    return output.getvalue()

st.markdown('<div class="stBox">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])
with col1:
    st.download_button("📄 다중 캐비티용 템플릿 다운로드", create_template(), "Multi_Cavity_Template.xlsx", use_container_width=True)
with col2:
    uploaded_file = st.file_uploader("분석 파일 업로드", type=["xlsx", "csv"], label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    cavity_cols = [col for col in df.columns if 'Cavity' in col]
    
    # --- Y축 정밀 범위 설정 (전체 데이터 기준) ---
    all_values = df[cavity_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
    y_min, y_max = all_values.min(), all_values.max()
    margin = (y_max - y_min) * 0.2
    y_range = [y_min - margin, y_max + margin]

    # --- 1. 통합 비교 그래프 (이미지 2 형태) ---
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📊 통합 경향성 비교 (Total Comparison)")
    
    fig_total = go.Figure()
    # SPEC 라인
    fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="SPEC MIN", line=dict(color="blue", dash="dash")))
    fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="SPEC MAX", line=dict(color="red", dash="dash")))
    
    # 각 캐비티 데이터 중첩
    colors = ["#10b981", "#8b5cf6", "#f59e0b", "#3b82f6"]
    for i, col in enumerate(cavity_cols):
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df[col], name=col, line=dict(color=colors[i % 4], width=2), mode='lines+markers'))
    
    fig_total.update_layout(yaxis_range=y_range, height=600, hovermode="x unified")
    st.plotly_chart(fig_total, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 2. 캐비티별 개별 분석 ---
    st.subheader("🔍 캐비티별 상세 분석")
    cols = st.columns(2) # 2열 배치
    
    for i, col_name in enumerate(cavity_cols):
        with cols[i % 2]:
            st.markdown(f'<div class="stBox">', unsafe_allow_html=True)
            st.write(f"### {col_name}")
            
            # 판정 로직
            df[f"{col_name}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[col_name] <= x["SPEC_MAX"] else "NG", axis=1)
            ng_points = df[df[f"{col_name}_판정"] == "NG"]
            
            fig_ind = go.Figure()
            fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="MIN", line=dict(color="blue")))
            fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="MAX", line=dict(color="red")))
            fig_ind.add_trace(go.Bar(x=df["Point"], y=df[col_name], name="측정치", 
                                     marker_color=['red' if p == "NG" else "#3b82f6" for p in df[f"{col_name}_판정"]]))
            
            fig_ind.update_layout(yaxis_range=y_range, height=400, showlegend=False)
            st.plotly_chart(fig_ind, use_container_width=True)
            
            st.metric(f"{col_name} 불량 수", f"{len(ng_points)} EA")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. 엑셀 보고서 생성 (이미지 2 스타일 통합 그래프 포함) ---
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📥 최종 보고서 다운로드")
    
    # Matplotlib으로 통합 그래프 생성
    fig_static, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["Point"], df["SPEC_MIN"], 'b--', label="MIN")
    ax.plot(df["Point"], df["SPEC_MAX"], 'r--', label="MAX")
    for i, col in enumerate(cavity_cols):
        ax.plot(df["Point"], df[col], label=col, marker='o', markersize=4)
    ax.set_ylim(y_range)
    ax.legend(loc='upper right')
    
    img_buf = BytesIO()
    fig_static.savefig(img_buf, format='png', bbox_inches='tight')
    plt.close(fig_static)

    # 엑셀 파일 저장
    excel_out = BytesIO()
    with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Result')
        worksheet = writer.sheets['Result']
        worksheet.insert_image('K2', 'total_graph.png', {'image_data': img_buf, 'x_scale': 0.6, 'y_scale': 0.6})
    
    st.download_button("📂 통합 결과 엑셀 다운로드", excel_out.getvalue(), "Integrated_Quality_Report.xlsx", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
