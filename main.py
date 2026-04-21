# NG 점을 더 크게, 테두리는 더 진하게 (눈에 띄게 수정)
for res, color, size in zip(["✅ OK", "❌ NG"], ["#2ecc71", "#ff0000"], [10, 18]):
    pdf = df[df['RES'] == res]
    if not pdf.empty:
        fig.add_trace(go.Scatter(
            x=pdf['DX'], y=pdf['DY'], 
            mode='markers+text', 
            name=res,
            text=pdf['ID'],
            textposition="top center",
            marker=dict(
                size=size, # NG는 18로 크게!
                color=color, 
                line=dict(width=2, color="white" if res == "✅ OK" else "black") # NG는 검정 테두리
            )
        ))

# 그래프 축을 공차 원에 딱 맞춰서 "선 넘은 게" 잘 보이도록 고정
# 데이터가 중앙에 있어도 공차 원을 크게 보여줘서 긴장감 유지
limit_range = tol * 1.2 
fig.update_layout(
    xaxis=dict(range=[-limit_range, limit_range], title="X 편차"),
    yaxis=dict(range=[-limit_range, limit_range], title="Y 편차"),
    title="<b>[보고용] 위치도 정밀 분석 결과</b>"
)
