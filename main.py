import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt # 엑셀 내 이미지 생성을 위한 라이브러리
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v7.3", layout="wide")

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
    
    div.stDownloadButton > button {
        width: 100% !important;
        height: 4.5em !important;
        font-size: 1.2em !important;
        font-weight: bold !important;
        background-color: #1e293b !important;
        color: white !important;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 핀 높이 멀티 캐비티 통합 분석 리포트")

# --- 2. 템플릿 다운로드 및 파일 업로드 ---
def get_final_template():
    points = list(range(1, 55))
    df_temp = pd.DataFrame({
        "Point": points, "SPEC_MIN": [30.03]*54, "SPEC_MAX": [30.38]*54,
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

        # --- 3. 캐비티별 상세 분포 (항상 노출) ---
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
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], name=cav, mode='markers', marker=dict(size=7, color=cav_colors[i % 4], opacity=0.4)))
        fig_total.update_layout(yaxis_range=y_range, height=500, template="plotly_white", hovermode="x unified")
        st.plotly_chart(fig_total, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- 6. 분석결과 리포트 (텍스트) ---
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📝 품질 분석 상세 리포트")
        total_ng_sum = sum(r['ng'] for r in summary_results)
        report_content = f"⚠️ 종합 판정: {'부적합' if total_ng_sum > 0 else '양호'}\n\n"
        for res in summary_results:
            report_content += f"■ {res['cav']}: 합격률 {((res['total']-res['ng'])/res['total'])*100:.1f}% (NG: {res['ng']}건)\n"
        st.markdown(f'<div class="report-text">{report_content}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- 7. [핵심기능] 엑셀용 그래프 생성 및 다운로드 ---
        st.markdown("### 💾 결과물 저장 (엑셀 내 그래프 포함)")
        
        # 엑셀 삽입용 이미지 생성 (Matplotlib)
        plt.figure(figsize=(10, 5))
        plt.plot(df["Point"], df["SPEC_MIN"], 'b--', alpha=0.5, label="MIN")
        plt.plot(df["Point"], df["SPEC_MAX"], 'r--', alpha=0.5, label="MAX")
        plt.plot(df["Point"], df['Average'], 'k-', linewidth=2, label="AVG Trend")
        for i, cav in enumerate(cav_cols):
            plt.scatter(df["Point"], df[cav], color=cav_colors[i%4], s=15, alpha=0.3)
        plt.ylim(y_range)
        plt.title("Total Cavity Analysis Graph")
        plt.grid(True, linestyle=':', alpha=0.5)
        
        img_buf = BytesIO()
        plt.savefig(img_buf, format='png', bbox_inches='tight')
        img_buf.seek(0)
        plt.close()

        # 엑셀 파일 생성 및 이미지 삽입
        output_res = BytesIO()
        with pd.ExcelWriter(output_res, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Result')
            worksheet = writer.sheets['Result']
            # 데이터 옆(I열 정도)에 통합 그래프 삽입
            worksheet.insert_image('I2', 'trend_graph.png', {'image_data': img_buf, 'x_scale': 0.8, 'y_scale': 0.8})
        
        st.download_button(
            label="📥 분석 결과 엑셀(XLSX) 다운로드 (그래프 포함)",
            data=output_res.getvalue(),
            file_name="Quality_Final_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")
