import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from io import BytesIO

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="품질 통합 분석 시스템", layout="wide")

# 스타일 설정
st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 10px;
    }
    .ng-text { color: #dc2626; font-weight: bold; }
    .ok-text { color: #10b981; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 전 캐비티 통합 분석 보고서")

# --- 2. 데이터 업로드 및 전처리 ---
uploaded_file = st.sidebar.file_uploader("분석 파일 업로드", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    cav_cols = [c for c in df.columns if 'Cavity' in c]
    
    # [데이터 분석 로직]
    summary_data = []
    for cav in cav_cols:
        # 판정 열 생성
        df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
        total = len(df)
        ng_count = len(df[df[f"{cav}_판정"] == "NG"])
        ok_count = total - ng_count
        pass_rate = (ok_count / total) * 100
        summary_data.append({
            "cav": cav, "total": total, "ng": ng_count, "ok": ok_count, "rate": pass_rate
        })

    # --- 3. 통합 경향성 분석 그래프 (개선됨) ---
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🌐 전 캐비티 데이터 산포 및 NG 구간 분석")
    
    fig_total = go.Figure()
    
    # [시각적 장치] NG 영역 배경색 칠하기 (상사님이 보시기 편하게)
    # SPEC 범위를 벗어나는 영역을 배경색으로 강조할 수도 있으나, 여기서는 점의 색상으로 집중
    
    # SPEC 라인 (점선 유지)
    fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="SPEC 하한", line=dict(color="#2563eb", width=2, dash="dash")))
    fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="SPEC 상한", line=dict(color="#dc2626", width=2, dash="dash")))
    
    # 각 캐비티 데이터 (선 없애고 점으로만 표시)
    colors = ['#10b981', '#f59e0b', '#8b5cf6', '#06b6d4']
    for i, cav in enumerate(cav_cols):
        # NG 포인트만 별도로 추출하여 강조
        ng_mask = df[f"{cav}_판정"] == "NG"
        
        # 기본 점 (OK 포함)
        fig_total.add_trace(go.Scatter(
            x=df["Point"], y=df[cav], 
            name=f"{cav}",
            mode='markers', 
            marker=dict(size=8, opacity=0.6, color=colors[i%4]),
            hovertemplate="Point: %{x}<br>Value: %{y}<br>Status: OK"
        ))
        
        # NG 지점 강조 (테두리가 있는 빨간 점 중첩)
        if ng_mask.any():
            fig_total.add_trace(go.Scatter(
                x=df.loc[ng_mask, "Point"], y=df.loc[ng_mask, cav],
                name=f"{cav} [NG]",
                mode='markers',
                marker=dict(size=10, color='red', symbol='x', line=dict(width=2, color='white')),
                showlegend=False,
                hovertemplate="Point: %{x}<br>Value: %{y}<br>Status: 🚨NG"
            ))

    # Y축 범위 최적화
    all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
    fig_total.update_layout(
        yaxis_range=[all_vals.min() - 0.05, all_vals.max() + 0.05],
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
    )
    st.plotly_chart(fig_total, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. 요약 내용 (하단 브리핑 섹션) ---
    st.markdown("### 📋 품질 분석 종합 요약")
    
    # 상단 메트릭 카드
    m_cols = st.columns(len(summary_data))
    for i, data in enumerate(summary_data):
        with m_cols[i]:
            st.markdown(f"""
                <div class="summary-card">
                    <h4 style='margin:0;'>{data['cav']}</h4>
                    <p style='margin:5px 0;'>합격률: <span class="{'ok-text' if data['rate'] == 100 else 'ng-text'}">{data['rate']:.1f}%</span></p>
                    <p style='margin:0; font-size:0.9em;'>총 {data['total']}개 중 <span class="ng-text">NG {data['ng']}개</span></p>
                </div>
            """, unsafe_allow_html=True)

    # 텍스트 상세 브리핑 (기본 코드 스타일 복구)
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📝 정밀 분석 가이드")
    
    total_ng = sum(d['ng'] for d in summary_data)
    if total_ng == 0:
        st.success("✅ **모든 캐비티 양호:** 전 포인트 규격 내 관리되고 있어 공정이 매우 안정적입니다.")
    else:
        st.warning(f"🚨 **품질 경보:** 총 {total_ng}건의 규격 이탈이 감지되었습니다.")
        
        briefing = ""
        for data in summary_data:
            if data['ng'] > 0:
                # 어느 포인트가 NG인지 리스트업
                ng_points = df[df[f"{data['cav']}_판정"] == "NG"]["Point"].tolist()
                briefing += f"* **{data['cav']}**: 포인트 {ng_points}번에서 이탈 발생 (불량률 {100-data['rate']:.1f}%)\n"
        st.markdown(briefing)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("왼쪽 사이드바에서 파일을 업로드해주세요.")
