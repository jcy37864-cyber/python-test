import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v6.7", layout="wide")

st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 10px; text-align: center;
    }
    .ng-text { color: #e11d48; font-weight: bold; }
    .ok-text { color: #10b981; font-weight: bold; }
    .guide-box { background-color: #f8fafc; padding: 15px; border-radius: 10px; border-left: 5px solid #64748b; color: #1e293b; margin-bottom: 20px; font-size: 0.95em; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 핀 높이 멀티 캐비티 정밀 분석 리포트")

# --- 2. 템플릿 및 파일 업로드 (요구사항 1번: 버튼 유지) ---
def get_main_template():
    points = list(range(1, 55))
    # 이미지 1 기반 SPEC 자동 설정 (특수 구간 반영)
    spec_min = [30.35 if p <= 6 or 15 <= p <= 20 or p in [36, 37, 53, 54] else 30.03 for p in points]
    spec_max = [30.70 if p <= 6 or 15 <= p <= 20 or p in [36, 37, 53, 54] else 30.38 for p in points]
    df_temp = pd.DataFrame({
        "Point": points, "SPEC_MIN": spec_min, "SPEC_MAX": spec_max,
        "Cavity_1": [30.5]*54, "Cavity_2": [30.48]*54, "Cavity_3": [30.42]*54, "Cavity_4": [30.58]*54
    })
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_temp.to_excel(writer, index=False)
    return output.getvalue()

st.markdown('<div class="guide-box"><b>[보고 가이드]</b> 상단 통합 산포도의 검은색 실선은 전체 캐비티의 평균 트렌드입니다. 특정 구간의 치수 쏠림을 확인하세요.</div>', unsafe_allow_html=True)

col_file, col_temp = st.columns([3, 1])
with col_temp:
    st.download_button("📄 분석용 템플릿 다운로드", get_main_template(), "Quality_Template_v6.7.xlsx", use_container_width=True)
with col_file:
    uploaded_file = st.file_uploader("분석 파일 업로드 (XLSX, CSV)", type=["xlsx", "csv"], label_visibility="collapsed")

# --- 3. 데이터 처리 로직 (요구사항 4번: 누락 방지) ---
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # 컬럼명 자동 보정
        df.columns = [str(c).strip() for c in df.columns]
        if 'Point' not in df.columns: df.rename(columns={df.columns[0]: 'Point'}, inplace=True)
        for col in df.columns:
            if 'MIN' in col.upper(): df.rename(columns={col: 'SPEC_MIN'}, inplace=True)
            if 'MAX' in col.upper(): df.rename(columns={col: 'SPEC_MAX'}, inplace=True)
        
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        
        # [요구사항 2번] 정밀 범위를 위한 Y축 계산 (SPEC 라인에 바짝 붙임)
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_range = [all_vals.min() - 0.03, all_vals.max() + 0.03]

        # --- 4. 통합 경향성 산포도 (상사 보고용 핵심 그래프) ---
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 전 캐비티 통합 경향성 분석")
        
        fig_total = go.Figure()
        
        # SPEC 라인
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="SPEC MIN", line=dict(color="blue", width=1.5, dash="dash")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="SPEC MAX", line=dict(color="red", width=1.5, dash="dash")))

        # [신규] 전체 평균선 (Trend Line)
        df['Average'] = df[cav_cols].mean(axis=1)
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Average'], name="전체 평균선", line=dict(color="black", width=3), mode='lines'))

        # 캐비티별 점 (고대비 색상 적용)
        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            fig_total.add_trace(go.Scatter(
                x=df["Point"], y=df[cav], name=cav, mode='markers',
                marker=dict(size=8, color=cav_colors[i % 4], opacity=0.5)
            ))
            # NG 지점 강조
            ng_df = df[df[f"{cav}_판정"] == "NG"]
            if not ng_df.empty:
                fig_total.add_trace(go.Scatter(x=ng_df["Point"], y=ng_df[cav], mode='markers',
                                               marker=dict(size=12, color='rgba(0,0,0,0)', line=dict(width=2, color='red')),
                                               showlegend=False, hoverinfo='skip'))

        fig_total.update_layout(yaxis_range=y_range, height=550, margin=dict(l=10, r=10, t=10, b=10), 
                                plot_bgcolor='white', hovermode="x unified")
        st.plotly_chart(fig_total, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- 5. 캐비티별 상세 분석 (복구) ---
        st.subheader("🔍 캐비티별 상세 분석")
        c_cols = st.columns(2)
        summary_results = []

        for i, cav in enumerate(cav_cols):
            with c_cols[i % 2]:
                st.markdown('<div class="stBox">', unsafe_allow_html=True)
                fig_ind = go.Figure()
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", width=1), showlegend=False))
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", width=1), showlegend=False))
                
                b_colors = ['#ef4444' if p == "NG" else cav_colors[i % 4] for p in df[f"{cav}_판정"]]
                fig_ind.add_trace(go.Bar(x=df["Point"], y=df[cav], name=cav, marker_color=b_colors))
                fig_ind.update_layout(title=f"<b>{cav} 분석</b>", yaxis_range=y_range, height=350)
                st.plotly_chart(fig_ind, use_container_width=True)
                
                ng_cnt = len(df[df[f"{cav}_판정"] == "NG"])
                summary_results.append({"cav": cav, "ng": ng_cnt, "total": len(df)})
                st.markdown('</div>', unsafe_allow_html=True)

        # --- 6. 요약 대쉬보드 (요구사항 3번: 보존) ---
        st.markdown("### 📋 품질 분석 대쉬보드")
        d_cols = st.columns(len(summary_results))
        for i, res in enumerate(summary_results):
            with d_cols[i]:
                rate = ((res['total'] - res['ng']) / res['total']) * 100
                st.markdown(f"""
                    <div class="summary-card">
                        <span style="font-weight:bold;">{res['cav']}</span><br>
                        <span style="font-size:1.5em;" class="{'ok-text' if rate==100 else 'ng-text'}">{rate:.1f}%</span><br>
                        <span>합격: {res['total']-res['ng']} / 불량: {res['ng']}</span>
                    </div>
                """, unsafe_allow_html=True)

        # 결론 섹션
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        total_ng = sum(r['ng'] for r in summary_results)
        if total_ng > 0:
            st.error(f"🚨 **종합 분석 결론:** 총 {total_ng}건의 규격 이탈 확인. 검은색 평균선이 규격 한계선에 근접한 구간의 금형 점검이 필요합니다.")
        else:
            st.success("✅ **종합 분석 결론:** 전 캐비티가 규격 중앙치에서 안정적으로 관리되고 있습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
else:
    st.info("📊 파일을 업로드하면 정밀 분석 보고서가 생성됩니다.")
