import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v7.2", layout="wide")

st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 10px; text-align: center;
    }
    .ng-text { color: #e11d48; font-weight: bold; }
    .ok-text { color: #10b981; font-weight: bold; }
    .report-text { font-size: 1.05em; line-height: 1.8; color: #1e293b; white-space: pre-wrap; font-family: sans-serif; }
    
    /* 하단 대형 버튼 스타일 */
    div.stDownloadButton > button {
        width: 100% !important;
        height: 4em !important;
        font-size: 1.2em !important;
        font-weight: bold !important;
        background-color: #1e293b !important;
        color: white !important;
        border-radius: 10px;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 핀 높이 멀티 캐비티 통합 분석 리포트")

# --- 2. 템플릿 다운로드 및 파일 업로드 ---
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
    st.download_button("📄 데이터 입력 템플릿 받기", get_final_template(), "Quality_Template.xlsx", use_container_width=True)
with col_file:
    uploaded_file = st.file_uploader("분석 파일 업로드 (XLSX, CSV)", type=["xlsx", "csv"], label_visibility="collapsed")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        df.columns = [str(c).strip() for c in df.columns]
        if 'Point' not in df.columns: df.rename(columns={df.columns[0]: 'Point'}, inplace=True)
        for col in df.columns:
            if 'MIN' in col.upper(): df.rename(columns={col: 'SPEC_MIN'}, inplace=True)
            if 'MAX' in col.upper(): df.rename(columns={col: 'SPEC_MAX'}, inplace=True)
        
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_range = [float(all_vals.min()) - 0.02, float(all_vals.max()) + 0.02]
        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']

        # --- 3. 캐비티별 상세 분포 분석 (항상 노출) ---
        st.subheader("🔍 캐비티별 상세 분포 분석")
        c_grid = st.columns(2)
        summary_results = []
        
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            with c_grid[i % 2]:
                st.markdown('<div class="stBox">', unsafe_allow_html=True)
                fig_ind = go.Figure()
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", width=1, dash="dash"), name="MIN"))
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", width=1, dash="dash"), name="MAX"))
                
                b_colors = ['#ef4444' if p == "NG" else cav_colors[i % 4] for p in df[f"{cav}_판정"]]
                fig_ind.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=b_colors, name="측정값"))
                
                # 오류 수정: yanchor 제거
                fig_ind.update_layout(title=f"<b>{cav} 개별 데이터</b>", yaxis_range=y_range, height=300, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig_ind, use_container_width=True)
                
                ng_cnt = len(df[df[f"{cav}_판정"] == "NG"])
                summary_results.append({"cav": cav, "ng": ng_cnt, "total": len(df), "color": cav_colors[i % 4]})
                st.markdown('</div>', unsafe_allow_html=True)

        # --- 4. 품질현황 요약 대쉬보드 ---
        st.subheader("📋 품질현황 요약 대쉬보드")
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

        # --- 5. 통합 경향성 분석 그래프 ---
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 전 캐비티 통합 경향성 (평균 Trend)")
        
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="SPEC MIN", line=dict(color="blue", dash="dot")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="SPEC MAX", line=dict(color="red", dash="dot")))
        
        df['Average'] = df[cav_cols].mean(axis=1)
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Average'], name="전체 평균 Trend", line=dict(color="black", width=3)))

        for i, cav in enumerate(cav_cols):
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], name=cav, mode='markers', 
                                           marker=dict(size=7, color=cav_colors[i % 4], opacity=0.4)))
        
        fig_total.update_layout(yaxis_range=y_range, height=500, template="plotly_white", hovermode="x unified")
        st.plotly_chart(fig_total, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- 6. 분석결과 리포트 (글자 형태) ---
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📝 품질 분석 상세 리포트")
        
        total_ng_sum = sum(r['ng'] for r in summary_results)
        report_content = ""
        
        if total_ng_sum > 0:
            report_content += f"⚠️ 종합 판정: 부적합 (총 {total_ng_sum}개 포인트 이탈)\n\n"
            for res in summary_results:
                report_content += f"■ {res['cav']}\n"
                report_content += f"  - 합격률: {((res['total']-res['ng'])/res['total'])*100:.1f}%\n"
                if res['ng'] > 0:
                    ng_list = df[df[f"{res['cav']}_판정"] == "NG"]["Point"].tolist()
                    report_content += f"  - 부적합 포인트: {ng_list}\n"
                else:
                    report_content += "  - 특이사항 없음 (전 포인트 합격)\n"
                report_content += "\n"
        else:
            report_content += "✅ 종합 판정: 양호\n\n- 전 캐비티의 측정값이 규격 내에 존재함.\n- 평균 트렌드 분석 결과 공정 치우침 현상 없음.\n- 현재 설비 상태 유지 권장."
        
        st.markdown(f'<div class="report-text">{report_content}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- 7. 하단 대형 다운로드 버튼 섹션 ---
        st.markdown("### 💾 결과물 저장")
        
        # 엑셀 다운로드
        output_res = BytesIO()
        with pd.ExcelWriter(output_res, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 분석 결과 엑셀(XLSX) 파일로 저장하기",
            data=output_res.getvalue(),
            file_name="Quality_Analysis_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.info("💡 그래프 이미지는 각 그래프 우측 상단의 '카메라 아이콘'을 클릭하여 PNG로 즉시 저장할 수 있습니다.")

    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")
