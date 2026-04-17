import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# ✅ 한글 폰트 (Streamlit / 서버 대응)
# -----------------------------
import matplotlib
matplotlib.rcParams['font.family'] = 'DejaVu Sans'  # 기본 (서버용)
matplotlib.rcParams['axes.unicode_minus'] = False

# -----------------------------
# ✅ 데이터 (엑셀 연동 시 교체)
# -----------------------------
df = pd.read_excel("data.xlsx")  # 너 파일명 맞춰

# 컬럼명 맞추기
# df.columns = ['핀', '측정값', 'Min', 'Max']

# -----------------------------
# ✅ 정규화 (핵심)
# -----------------------------
center = (df['Min'] + df['Max']) / 2
half_range = (df['Max'] - df['Min']) / 2
df['편차'] = (df['측정값'] - center) / half_range * 100

# -----------------------------
# ✅ 경향선 (이동평균)
# -----------------------------
df['경향'] = df['편차'].rolling(window=3, min_periods=1).mean()

# -----------------------------
# ✅ 자동 분석 (차별화 핵심🔥)
# -----------------------------
trend_slope = np.polyfit(df['핀'], df['편차'], 1)[0]

if trend_slope > 2:
    trend_msg = "➡️ 뒤쪽 핀으로 갈수록 증가 (공정 밀림 가능)"
elif trend_slope < -2:
    trend_msg = "⬅️ 앞쪽 핀으로 갈수록 증가"
else:
    trend_msg = "➡️ 큰 경향 없음"

out_of_spec = df[(df['편차'].abs() > 100)]

# -----------------------------
# ✅ 그래프
# -----------------------------
plt.figure(figsize=(12,6))

# 🔵 배경 영역
plt.axhspan(-100, 100, alpha=0.05)
plt.axhspan(-100, -80, color='red', alpha=0.15)
plt.axhspan(80, 100, color='red', alpha=0.15)
plt.axhspan(-80, 80, color='green', alpha=0.1)

# -----------------------------
# ✅ 점 색상 (이상 강조)
# -----------------------------
colors = []
for val in df['편차']:
    if abs(val) > 100:
        colors.append('red')
    elif abs(val) > 80:
        colors.append('orange')
    else:
        colors.append('gray')

plt.scatter(df['핀'], df['편차'], c=colors, s=60, zorder=3)

# -----------------------------
# ✅ 경향선 (굵게)
# -----------------------------
plt.plot(df['핀'], df['경향'], linewidth=3, zorder=2)

# -----------------------------
# ✅ 기준선
# -----------------------------
plt.axhline(0, linestyle='--')
plt.axhline(100, linestyle='--')
plt.axhline(-100, linestyle='--')

# -----------------------------
# ❌ 범례 제거 → 직접 표시
# -----------------------------
plt.text(df['핀'].max()+0.5, 0, '중심', va='center')
plt.text(df['핀'].max()+0.5, 100, '상한', va='center')
plt.text(df['핀'].max()+0.5, -100, '하한', va='center')

# -----------------------------
# 🔥 핵심: 자동 해석 문구
# -----------------------------
plt.title(f'핀 위치별 치수 경향 분석\n{trend_msg}', fontsize=14)

# -----------------------------
# ✅ 축
# -----------------------------
plt.xlabel('핀 위치')
plt.ylabel('편차 (%)')

plt.ylim(-120, 120)
plt.grid(alpha=0.3)

plt.tight_layout()
plt.show()

# -----------------------------
# 🔥 콘솔 출력 (보고서용)
# -----------------------------
print("===== 분석 결과 =====")
print(trend_msg)

if len(out_of_spec) > 0:
    print(f"❌ 불량 핀: {list(out_of_spec['핀'])}")
else:
    print("✅ 전체 정상 범위")
