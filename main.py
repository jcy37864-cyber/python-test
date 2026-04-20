import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v7.0", layout="wide")

st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 10px; text-align: center;
    }
    .ng-text { color: #e11d48; font-weight: bold; }
    .ok-text { color: #10b981; font-weight: bold; }
    .briefing-text { font-size: 1.05em; line-height: 1.6; color: #334155; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 핀 높이 멀티 캐비티 통합 정밀 분석")

# --- 2. 템플릿 및 파일 업로드 섹션 ---
def get_final_template():
    points = list(range(1, 55))
    spec_min = [30.03] * 54
    spec_max = [30.38] * 54
    df_temp = pd.DataFrame({
        "Point": points, "SPEC_MIN": spec_min, "SPEC_MAX": spec_max,
        "Cavity_1": [30.2]*54, "Cavity_2": [30.22]*54, "Cavity_3": [30.18]*54, "Cavity_4": [30.25]*54
    })
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_temp.to_excel(writer, index=False)
    return output.getvalue()

col_file, col_temp = st.columns([3, 1])
with col_temp:
    st.download_button("📄 분석용 템플릿 다운로드", get_final_template(), "Quality_Template.xlsx", use_container_width=True)
with col_file:
    uploaded_file = st.file_uploader("분석 파일 업로드 (XLSX, CSV)", type=["xlsx", "csv"], label_visibility="collapsed")

# --- 3. 데이터 분석 및 시각화 ---
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # 열 이름 자동 보정
        df.columns = [str(c).strip() for c in df.columns]
        if 'Point' not in df.columns: df.rename(columns={df.columns[0]: 'Point'}, inplace=True)
        for col in df.columns:
            if 'MIN' in col.upper(): df.rename(columns={col: 'SPEC_MIN'}, inplace=True)
            if 'MAX' in col.upper(): df.rename(columns={col: 'SPEC_MAX'}, inplace=True)
        
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        
        # 정밀 측정을 위한 Y축 설정
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_range = [float(all_vals.min()) - 0.02, float(all_vals.max()) + 0.02]

        # --- 4. 통합 경향성 분석 및 이미지 다운로드 기능 ---
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        
        header_col1, header_col2 = st.columns([4, 1])
        with header_col1:
            st.subheader("🌐 전 캐비티 통합 경향성 분석")
        
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="SPEC 하한", line=dict(color="blue", dash="dash", width=1.5)))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="SPEC 상한", line=dict(color="red", dash="dash", width=1.5)))

        df['Average'] = df[cav_cols].mean(axis=1)
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Average'], name="전체 평균 Trend", line=dict(color="black", width=3)))

        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']
        summary_results = []

        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], name=cav, mode='markers', 
                                           marker=dict(size=8, color=cav_colors[i % 4], opacity=0.5)))
            
            ng_df = df[df[f"{cav}_판정"] == "NG"]
            if not ng_df.empty:
                fig_total.add_trace(go.Scatter(x=ng_df["Point"], y=ng_df[cav], mode='markers', 
                                               marker=dict(size=12, color='rgba(0,0,0,0)', line=dict(width=2, color='red')), showlegend=False))
            summary_results.append({"cav": cav, "ng": len(ng_df), "total": len(df), "color": cav_colors[i % 4]})

        fig_total.update_layout(yaxis_range=y_range, height=600, template="plotly_white", hovermode="x unified",
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        
        # [핵심] 이미지 다운로드 버튼 추가
        st.plotly_chart(fig_total, use_container_width=True, config={'displayModeBar': True, 'toImageButtonOptions': {'format': 'png', 'filename': 'Quality_Analysis_Graph'}})
        st.markdown('</div>', unsafe_allow_html=True)

        # --- 5. 실시간 품질 대쉬보드 ---
        st.subheader("📋 품질 현황 대쉬보드")
        d_cols = st.columns(len(summary_results))
        for i, res in enumerate(summary_results):
            rate = ((res['total'] - res['ng']) / res['total']) * 100
            with d_cols[i]:
                st.markdown(f"""
                    <div class="summary-card" style="border-top-color: {res['color']};">
                        <span style="font-weight:bold; color:#64748b;">{res['cav']}</span><br>
                        <span style="font-size:1.8em;" class="{'ok-text' if rate==100 else 'ng-text'}">{rate:.1f}%</span><br>
                        <span style="font-size:0.9em; color:#94a3b8;">불량: {res['ng']} / {res['total']} EA</span>
                    </div>
                """, unsafe_allow_html=True)

        # --- 6. 상세 요약 문구 및 최종 보고서 다운로드 ---
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📝 종합 분석 리포트")
        
        total_ng_sum = sum(r['ng'] for r in summary_results)
        if total_ng_sum > 0:
            st.markdown(f"<p class='briefing-text'>🚨 <b>부적합 경보:</b> 전체 포인트 중 총 <span class='ng-text'>{total_ng_sum}건</span>의 규격 이탈이 확인되었습니다.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='briefing-text'>✅ <b>공정 안정:</b> 전 캐비티의 치수가 규격 내에서 안정적으로 관리되고 있습니다.</p>", unsafe_allow_html=True)

        # [핵심] 결과 엑셀 다운로드 버튼
        output_result = BytesIO()
        with pd.ExcelWriter(output_result, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Analysis_Result')
        
        st.download_button(
            label="📂 분석 결과 엑셀 파일로 저장",
            data=output_result.getvalue(),
            file_name="Quality_Analysis_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # 캐비티별 상세 분포 (접기/펼치기 유지)
        with st.expander("🔍 캐비티별 개별 분포 상세 보기"):
            c_grid = st.columns(2)
            for i, cav in enumerate(cav_cols):
                with c_grid[i % 2]:
                    fig_ind = go.Figure()
                    fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", width=1), showlegend=False))
                    fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", width=1), showlegend=False))
                    b_colors = ['#ef4444' if p == "NG" else cav_colors[i % 4] for p in df[f"{cav}_판정"]]
                    fig_ind.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=b_colors))
                    fig_ind.update_layout(title=f"{cav} 개별 분포", yaxis_range=y_range, height=300)
                    st.plotly_chart(fig_ind, use_container_width=True)

    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")
