import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from io import BytesIO

# --- 1. 페이지 설정 및 스타일 ---
st.set_page_config(page_title="품질 통합 분석 시스템 v6.5", layout="wide")

st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 10px; text-align: center;
    }
    .ng-text { color: #e11d48; font-weight: bold; }
    .ok-text { color: #10b981; font-weight: bold; }
    .guide-box { background-color: #f0f9ff; padding: 15px; border-radius: 10px; border-left: 5px solid #0ea5e9; color: #0c4a6e; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 핀 높이 멀티 캐비티 정밀 분석")

# --- 2. [필수] 템플릿 생성 및 다운로드 버튼 (누락 방지) ---
def get_multi_template():
    points = list(range(1, 55))
    # 이미지 기반 SPEC 설정 (1~6번 등 특정 구간은 높음)
    spec_min = [30.35 if p <= 6 or 15 <= p <= 20 or p in [36, 37, 53, 54] else 30.03 for p in points]
    spec_max = [30.70 if p <= 6 or 15 <= p <= 20 or p in [36, 37, 53, 54] else 30.38 for p in points]
    df_temp = pd.DataFrame({
        "Point": points, "SPEC_MIN": spec_min, "SPEC_MAX": spec_max,
        "Cavity_1": [30.5]*54, "Cavity_2": [30.45]*54, "Cavity_3": [30.4]*54, "Cavity_4": [30.55]*54
    })
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_temp.to_excel(writer, index=False)
    return output.getvalue()

st.markdown('<div class="guide-box"><b>💡 안내:</b> 반드시 아래 템플릿을 다운로드하여 규격과 실측치를 입력 후 업로드해 주세요.</div>', unsafe_allow_html=True)

col_file, col_temp = st.columns([3, 1])
with col_temp:
    st.download_button("📄 분석 템플릿 다운로드", get_multi_template(), "Quality_Template.xlsx", use_container_width=True)
with col_file:
    uploaded_file = st.file_uploader("분석 파일 업로드 (XLSX, CSV)", type=["xlsx", "csv"], label_visibility="collapsed")

# --- 3. 데이터 처리 및 오류 방지 로직 ---
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # [핵심] 컬럼명 자동 보정 (KeyError 방지)
        df.columns = [str(c).strip() for c in df.columns]
        if 'Point' not in df.columns: df.rename(columns={df.columns[0]: 'Point'}, inplace=True)
        for col in df.columns:
            if 'MIN' in col.upper(): df.rename(columns={col: 'SPEC_MIN'}, inplace=True)
            if 'MAX' in col.upper(): df.rename(columns={col: 'SPEC_MAX'}, inplace=True)
        
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        
        if 'SPEC_MIN' not in df.columns or 'SPEC_MAX' not in df.columns:
            st.error("❌ 파일에 SPEC_MIN, SPEC_MAX 열이 필요합니다.")
            st.stop()

        # [중요] 정밀 측정을 위한 Y축 범위 설정 (데이터 밀집도 최적화)
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_range = [all_vals.min() - 0.02, all_vals.max() + 0.02] # 매우 타이트한 범위

        # --- 4. 전 캐비티 통합 산포도 (Scatter Only) ---
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 전 캐비티 통합 산포도 (경향성 비교)")
        
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="SPEC MIN", line=dict(color="#2563eb", width=1.5, dash="dash")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="SPEC MAX", line=dict(color="#dc2626", width=1.5, dash="dash")))

        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd'] # 고대비 색상
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            fig_total.add_trace(go.Scatter(
                x=df["Point"], y=df[cav], name=cav, mode='markers',
                marker=dict(size=8, color=cav_colors[i % len(cav_colors)], opacity=0.7)
            ))
            # NG 포인트 테두리 강조
            ng_df = df[df[f"{cav}_판정"] == "NG"]
            if not ng_df.empty:
                fig_total.add_trace(go.Scatter(x=ng_df["Point"], y=ng_df[cav], mode='markers',
                                               marker=dict(size=12, color='rgba(0,0,0,0)', line=dict(width=2, color='red')),
                                               showlegend=False, hoverinfo='skip'))

        fig_total.update_layout(yaxis_range=y_range, height=550, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor='white')
        st.plotly_chart(fig_total, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- 5. 캐비티별 상세 그래프 (복구 완료) ---
        st.subheader("🔍 캐비티별 상세 분석")
        c_cols = st.columns(2)
        summary_results = []

        for i, cav in enumerate(cav_cols):
            with c_cols[i % 2]:
                st.markdown('<div class="stBox">', unsafe_allow_html=True)
                fig_ind = go.Figure()
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", width=1), showlegend=False))
                fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", width=1), showlegend=False))
                
                # OK/NG 색상 분구
                b_colors = ['#ef4444' if p == "NG" else cav_colors[i % len(cav_colors)] for p in df[f"{cav}_판정"]]
                fig_ind.add_trace(go.Bar(x=df["Point"], y=df[cav], name=cav, marker_color=b_colors))
                fig_ind.update_layout(title=f"<b>{cav} 상세</b>", yaxis_range=y_range, height=350)
                st.plotly_chart(fig_ind, use_container_width=True)
                
                ng_cnt = len(df[df[f"{cav}_판정"] == "NG"])
                summary_results.append({"cav": cav, "ng": ng_cnt, "total": len(df)})
                st.markdown('</div>', unsafe_allow_html=True)

        # --- 6. 요약 대쉬보드 (누락 방지 및 강화) ---
        st.markdown("### 📋 품질 분석 대쉬보드")
        d_cols = st.columns(len(summary_results))
        for i, res in enumerate(summary_results):
            with d_cols[i]:
                rate = ((res['total'] - res['ng']) / res['total']) * 100
                st.markdown(f"""
                    <div class="summary-card">
                        <span style="font-weight:bold;">{res['cav']}</span><br>
                        <span style="font-size:1.5em;" class="{'ok-text' if rate==100 else 'ng-text'}">{rate:.1f}%</span><br>
                        <span>NG: {res['ng']} / {res['total']} EA</span>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        total_ng = sum(r['ng'] for r in summary_results)
        if total_ng > 0:
            st.error(f"🚨 **종합 결론:** 총 {total_ng}개의 포인트에서 규격 이탈이 감지되었습니다.")
            for res in summary_results:
                if res['ng'] > 0:
                    pts = df[df[f"{res['cav']}_판정"] == "NG"]["Point"].tolist()
                    st.write(f"• **{res['cav']}** 부적합 포인트: `{pts}`")
        else:
            st.success("✅ **종합 결론:** 모든 캐비티의 전 포인트가 규격 내에서 안정적으로 관리되고 있습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"파일 처리 오류: {e}. 템플릿 형식을 확인해 주세요.")

else:
    st.info("📊 상단의 버튼을 통해 템플릿을 다운로드하거나 분석 파일을 업로드하세요.")
