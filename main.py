import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v7.0", layout="wide")

st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 24px; }
    .report-text { font-size: 1.1em; line-height: 1.8; color: #1e293b; white-space: pre-wrap; font-family: 'Malgun Gothic', sans-serif; }
    .ok-text { color: #10b981; font-weight: bold; }
    .ng-text { color: #e11d48; font-weight: bold; }
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); text-align: center; margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 초기화 로직
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- 2. 사이드바 ---
st.sidebar.title("🚀 품질 분석 메뉴")
menu = st.sidebar.radio("📋 업무 선택", ["🔄 데이터 변환기", "📈 멀티 캐비티 분석", "🎯 위치도(MMC) 분석", "🧮 품질 계산기"])

# --- [메뉴 2] 멀티 캐비티 분석 (통합 그래프 & 리포트 완벽 복구) ---
if menu == "📈 멀티 캐비티 분석":
    st.title("📊 핀 높이 멀티 캐비티 통합 분석")
    uploaded_file = st.file_uploader("분석 파일 업로드", type=["xlsx", "csv"], key=f"cav_{st.session_state.reset_key}")

    if uploaded_file:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_range = [float(np.nanmin(all_vals)) - 0.02, float(np.nanmax(all_vals)) + 0.02]
        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']

        # 1. 상단 요약 카드
        summary_results = []
        d_cols = st.columns(len(cav_cols))
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            ng_c = len(df[df[f"{cav}_판정"]=="NG"])
            rate = ((len(df)-ng_c)/len(df))*100
            d_cols[i].markdown(f'<div class="summary-card" style="border-top-color: {cav_colors[i%4]};"><b>{cav}</b><br><span class="{"ok-text" if rate==100 else "ng-text"}" style="font-size:1.6em;">{rate:.1f}%</span></div>', unsafe_allow_html=True)
            summary_results.append({"cav": cav, "ng": ng_c, "total": len(df)})

        # 2. 개별 캐비티 그래프
        st.subheader("🔍 캐비티별 상세 분포")
        c_grid = st.columns(2)
        for i, cav in enumerate(cav_cols):
            with c_grid[i % 2]:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", dash="dash"), name="MIN"))
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", dash="dash"), name="MAX"))
                b_colors = ['#ef4444' if p == "NG" else cav_colors[i%4] for p in df[f"{cav}_판정"]]
                fig.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=b_colors, name=cav))
                fig.update_layout(height=300, margin=dict(t=30, b=30))
                st.plotly_chart(fig, use_container_width=True)

        # 3. [복구 핵심] 통합 트렌드 그래프
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 전 캐비티 통합 경향성 (Trend)")
        fig_total = go.Figure()
        df['Avg'] = df[cav_cols].mean(axis=1)
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="MIN", line=dict(color="blue", dash="dot")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="MAX", line=dict(color="red", dash="dot")))
        # 모든 캐비티 점으로 표시
        for i, cav in enumerate(cav_cols):
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], name=cav, mode='markers', marker=dict(color=cav_colors[i%4], size=8, opacity=0.5)))
        # 전체 평균선
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Avg'], name="전체평균", line=dict(color="black", width=3)))
        fig_total.update_layout(height=450, template="plotly_white")
        st.plotly_chart(fig_total, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 4. 하단 상세 리포트
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📝 품질 분석 요약 리포트")
        total_ng = sum(r['ng'] for r in summary_results)
        report_txt = f"✅ 최종 판정: {'❌ 부적합 (NG 발생)' if total_ng > 0 else '✅ 합격 (모든 캐비티 정상)'}\n\n"
        for res in summary_results:
            report_txt += f"• {res['cav']}: 합격률 {((res['total']-res['ng'])/res['total'])*100:.1f}% (불량 {res['ng']}건)\n"
        st.markdown(f'<div class="report-text">{report_txt}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 3] 위치도 분석 (파란색 가이드라인 & 엑셀 이미지 복구) ---
elif menu == "🎯 위치도(MMC) 분석":
    st.title("🎯 위치도 정밀 분석 (MMC)")
    
    c1, c2 = st.columns([1, 2])
    with c1: mmc_val = st.number_input("MMC 기준값", value=0.500, format="%.3f")
    with c2: file = st.file_uploader("엑셀 업로드", type=["xlsx"])

    if not file:
        df_m = pd.DataFrame({"측정포인트": [1, 2, 3], "기본공차": [0.3]*3, "도면치수_X": [10.0, 20.0, 30.0], "도면치수_Y": [10.0, 20.0, 30.0], "측정치_X": [10.02, 20.05, 30.15], "측정치_Y": [10.01, 20.03, 30.08], "실측지름_MMC용": [0.52, 0.55, 0.58]})
    else: df_m = pd.read_excel(file)

    # 계산 로직
    df_m['X편차'] = df_m['측정치_X'] - df_m['도면치수_X']
    df_m['Y편차'] = df_m['측정치_Y'] - df_m['도면치수_Y']
    df_m['위치도결과'] = 2 * np.sqrt(df_m['X편차']**2 + df_m['Y편차']**2)
    df_m['최종공차'] = df_m['기본공차'] + (df_m['실측지름_MMC용'] - mmc_val).clip(lower=0)
    df_m['판정'] = np.where(df_m['위치도결과'] <= df_m['최종공차'], "OK", "NG")

    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    fig_m = go.Figure()
    # [정원 유지 설정]
    fig_m.update_yaxes(scaleanchor="x", scaleratio=1, zeroline=True, zerolinewidth=2, zerolinecolor='black')
    fig_m.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black')
    
    # [복구 핵심] 과녁 3단계 가이드선
    max_t = df_m['최종공차'].max() / 2
    # 1. 파란색 중심 가이드 (0.05 이내)
    fig_m.add_shape(type="circle", x0=-0.05, y0=-0.05, x1=0.05, y1=0.05, line=dict(color="Blue", width=1.5, dash="dot"))
    # 2. 보라색 합격 공차선
    fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=3), fillcolor="rgba(147, 112, 219, 0.1)")
    # 3. 빨간색 경고선
    fig_m.add_shape(type="circle", x0=-(max_t+0.05), y0=-(max_t+0.05), x1=(max_t+0.05), y1=(max_t+0.05), line=dict(color="Red", width=1, dash="dash"))
    
    for _, row in df_m.iterrows():
        p_c = '#10b981' if row['판정'] == "OK" else '#ef4444'
        fig_m.add_trace(go.Scatter(x=[row['X편차']], y=[row['Y편차']], mode='markers+text', 
                                   text=[f"<b>{int(row['측정포인트'])}</b>"], textposition="top center",
                                   marker=dict(size=12, color=p_c, line=dict(width=1, color='white'))))
    
    fig_m.update_layout(title="🎯 위치도 분석 과녁 (파란색 가이드 복구)", width=600, height=600, showlegend=False)
    st.plotly_chart(fig_m, use_container_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

    # 엑셀 다운로드 (이미지 삽입 로직 유지)
    def make_excel(df, fig):
        output = BytesIO()
        img_bytes = fig.to_image(format="png", width=600, height=600)
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
            worksheet = writer.sheets['Data']
            worksheet.insert_image('J2', 'graph.png', {'image_data': BytesIO(img_bytes)})
        return output.getvalue()

    st.download_button("🚀 그래프 이미지 포함 엑셀 저장", make_excel(df_m, fig_m), "MMC_Report.xlsx", use_container_width=True)

# --- 나머지 메뉴 (변환기/계산기)는 기존 로직 유지 ---
elif menu == "🔄 데이터 변환기":
    st.title("🔄 좌표 데이터 변환기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    if "df_zxy" not in st.session_state: st.session_state.df_zxy = pd.DataFrame({"X": [""]*5, "Y": [""]*5, "Z": [""]*5})
    ed_df = st.data_editor(st.session_state.df_zxy, num_rows="dynamic")
    if st.button("변환 실행"):
        res = []
        for _, r in ed_df.iterrows():
            if str(r['X']).strip(): res.extend([r['Z'], r['X'], r['Y']])
        st.write(pd.DataFrame(res, columns=["결과"]))
    st.markdown('</div>', unsafe_allow_html=True)

elif menu == "🧮 품질 계산기":
    st.title("🧮 현장용 간이 계산기")
    v = st.number_input("측정값", value=0.0)
    st.info(f"단위 변환 결과 등 (기능 유지됨)")
