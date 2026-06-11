import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="🚗 제동거리 시뮬레이터", page_icon="🚗", layout="wide")

# ─── 상수 ────────────────────────────────────────────
g = 9.8

ROAD_CONDITIONS = {
    "🌞 건조한 아스팔트": 0.75,
    "🌧️ 젖은 아스팔트":  0.45,
    "🌨️ 눈길":           0.25,
    "🧊 빙판":           0.08,
}

# ─── 헤더 ────────────────────────────────────────────
st.title("🚗 제동거리 시뮬레이터")
st.caption("속도 · 노면 상태 · 반응시간 · 경사도에 따른 정지거리를 시뮬레이션합니다")

# ─── 입력 ────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    speed_kmh  = st.slider("🚀 초기 속도 (km/h)", 10, 200, 60, step=10)
with c2:
    road       = st.selectbox("🛣️ 노면 상태", list(ROAD_CONDITIONS.keys()))
with c3:
    t_reaction = st.slider("⏱️ 반응 시간 (초)", 0.5, 3.0, 1.0, step=0.1)
with c4:
    grade      = st.slider("⛰️ 경사도 (%)", -20, 20, 0, step=1,
                            help="양수(+) = 오르막, 음수(-) = 내리막")

mu    = ROAD_CONDITIONS[road]
v0    = speed_kmh / 3.6                  # m/s
theta = np.arctan(grade / 100)           # 경사각 (라디안)

# ─── 경사 포함 감속도 ─────────────────────────────────
# a = g(μcosθ + sinθ)  →  오르막(+θ): 감속 증가 / 내리막(-θ): 감속 감소
deceleration = g * (mu * np.cos(theta) + np.sin(theta))

# 내리막이 너무 가팔라서 마찰이 부족한 경우
cannot_stop = deceleration <= 0

if not cannot_stop:
    t_braking  = v0 / deceleration
    t_total    = t_reaction + t_braking
    d_reaction = v0 * t_reaction
    d_braking  = v0 ** 2 / (2 * deceleration)
    d_total    = d_reaction + d_braking
else:
    t_braking = t_total = d_reaction = d_braking = d_total = float("inf")

# ─── 경보 배너 (정지 불가) ────────────────────────────
if cannot_stop:
    st.error(
        f"🚨 **정지 불가!** 현재 경사도({grade}%)에서 마찰력(μ={mu})이 중력 성분보다 작아 "
        f"차량이 멈출 수 없습니다. 노면 상태를 개선하거나 경사도를 줄여주세요."
    )
    st.stop()

# ─── 경사도 변화 경고 ─────────────────────────────────
if grade < -10:
    st.warning(f"⚠️ 급경사 내리막 ({grade}%) — 평지 대비 제동거리가 크게 증가합니다.")
elif grade > 10:
    st.info(f"ℹ️ 급경사 오르막 ({grade}%) — 제동거리가 평지보다 짧습니다.")

# ─── 평지 기준값 (비교용) ─────────────────────────────
d_braking_flat = v0 ** 2 / (2 * mu * g)
d_total_flat   = v0 * t_reaction + d_braking_flat
delta_d        = d_total - d_total_flat

# ─── KPI 카드 ─────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("🟢 반응거리",      f"{d_reaction:.1f} m")
k2.metric("🔴 제동거리",      f"{d_braking:.1f} m",
          delta=f"{d_braking - d_braking_flat:+.1f} m (평지 대비)",
          delta_color="inverse")
k3.metric("📏 정지거리 합계", f"{d_total:.1f} m",
          delta=f"{delta_d:+.1f} m (평지 대비)",
          delta_color="inverse")
k4.metric("📉 감속도",        f"{deceleration:.2f} m/s²")
k5.metric("📐 경사각",        f"{np.degrees(theta):.1f}°",
          delta="오르막" if grade > 0 else ("내리막" if grade < 0 else "평지"))

st.divider()

# ─── 시간축 데이터 생성 ───────────────────────────────
t_r = np.linspace(0, t_reaction, 40)
t_b = np.linspace(t_reaction, t_total, 80)

x_r = v0 * t_r
v_r = np.full_like(t_r, v0)

x_b = d_reaction + v0*(t_b - t_reaction) - 0.5*deceleration*(t_b - t_reaction)**2
v_b = np.maximum(v0 - deceleration*(t_b - t_reaction), 0)

def make_layout(title, xtitle, ytitle):
    return dict(
        title=title,
        xaxis_title=xtitle, yaxis_title=ytitle,
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", y=1.12, font=dict(size=11)),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
    )

left, right = st.columns(2)

with left:
    fig_x = go.Figure()
    fig_x.add_trace(go.Scatter(
        x=t_r, y=x_r, name="반응 구간",
        fill="tozeroy", fillcolor="rgba(34,197,94,0.12)",
        line=dict(color="#16A34A", width=2.5),
        hovertemplate="시간: %{x:.2f}s<br>위치: %{y:.1f}m<extra></extra>",
    ))
    fig_x.add_trace(go.Scatter(
        x=t_b, y=x_b, name="제동 구간",
        fill="tozeroy", fillcolor="rgba(239,68,68,0.12)",
        line=dict(color="#DC2626", width=2.5),
        hovertemplate="시간: %{x:.2f}s<br>위치: %{y:.1f}m<extra></extra>",
    ))
    fig_x.update_layout(**make_layout("📍 위치 – 시간 그래프", "시간 (s)", "이동거리 (m)"))
    st.plotly_chart(fig_x, use_container_width=True)

with right:
    fig_v = go.Figure()
    fig_v.add_trace(go.Scatter(
        x=t_r, y=v_r * 3.6, name="반응 구간",
        fill="tozeroy", fillcolor="rgba(34,197,94,0.12)",
        line=dict(color="#16A34A", width=2.5),
        hovertemplate="시간: %{x:.2f}s<br>속도: %{y:.1f}km/h<extra></extra>",
    ))
    fig_v.add_trace(go.Scatter(
        x=t_b, y=v_b * 3.6, name="제동 구간",
        fill="tozeroy", fillcolor="rgba(239,68,68,0.12)",
        line=dict(color="#DC2626", width=2.5),
        hovertemplate="시간: %{x:.2f}s<br>속도: %{y:.1f}km/h<extra></extra>",
    ))
    fig_v.update_layout(**make_layout("💨 속도 – 시간 그래프", "시간 (s)", "속도 (km/h)"))
    st.plotly_chart(fig_v, use_container_width=True)

# ─── 경사 도로 애니메이션 ─────────────────────────────
st.markdown("### 🎬 제동 애니메이션")
st.caption("▶ 재생을 눌러 차량이 멈추는 과정을 확인하세요 (경사 반영)")

N = 60
t_anim = np.linspace(0, t_total, N)
x_anim = []
for t in t_anim:
    if t <= t_reaction:
        x_anim.append(v0 * t)
    else:
        dt = t - t_reaction
        x_anim.append(min(d_reaction + v0*dt - 0.5*deceleration*dt**2, d_total))

# 경사를 반영한 실제 (x, y) 좌표
cos_t, sin_t = np.cos(theta), np.sin(theta)
pad = d_total * 0.12

def road_xy(d_arr):
    """거리 배열 → 경사 도로 위 (x, y) 좌표"""
    return d_arr * cos_t, d_arr * sin_t

r_x0, r_y0 = road_xy(np.array([-pad, d_total + pad]))
react_x, react_y = road_xy(np.array([d_reaction]))
stop_x,  stop_y  = road_xy(np.array([d_total]))

frames = []
for i, (t, d) in enumerate(zip(t_anim, x_anim)):
    car_color = "#16A34A" if t <= t_reaction else "#DC2626"
    cx, cy = road_xy(np.array([d]))
    frames.append(go.Frame(
        data=[
            go.Scatter(x=r_x0,   y=r_y0,
                       mode="lines", line=dict(color="#94A3B8", width=6),
                       showlegend=False),
            go.Scatter(x=[react_x[0], react_x[0]], y=[react_y[0]-0.3, react_y[0]+0.3],
                       mode="lines", line=dict(color="#F59E0B", width=2, dash="dash"),
                       showlegend=False),
            go.Scatter(x=[stop_x[0], stop_x[0]], y=[stop_y[0]-0.3, stop_y[0]+0.3],
                       mode="lines", line=dict(color="#DC2626", width=2.5),
                       showlegend=False),
            go.Scatter(x=[cx[0]], y=[cy[0]],
                       mode="markers",
                       marker=dict(size=26, color=car_color, symbol="square",
                                   line=dict(width=1.5, color="white")),
                       text=["🚗"], textposition="middle center",
                       showlegend=False),
        ],
        name=str(i),
    ))

y_range_min = min(r_y0) - 0.8
y_range_max = max(r_y0) + 0.8

fig_anim = go.Figure(
    data=[
        go.Scatter(x=r_x0, y=r_y0,
                   mode="lines", line=dict(color="#94A3B8", width=6), showlegend=False),
        go.Scatter(x=[react_x[0], react_x[0]], y=[react_y[0]-0.3, react_y[0]+0.3],
                   mode="lines", line=dict(color="#F59E0B", width=2, dash="dash"),
                   name="제동 시작"),
        go.Scatter(x=[stop_x[0], stop_x[0]], y=[stop_y[0]-0.3, stop_y[0]+0.3],
                   mode="lines", line=dict(color="#DC2626", width=2.5), name="정지선"),
        go.Scatter(x=[0], y=[0],
                   mode="markers",
                   marker=dict(size=26, color="#16A34A", symbol="square"),
                   showlegend=False),
    ],
    frames=frames,
)

fig_anim.update_layout(
    height=240,
    margin=dict(l=10, r=10, t=10, b=70),
    xaxis=dict(range=[r_x0[0], r_x0[-1]], title="수평 거리 (m)",
               tickfont=dict(size=11), showgrid=False),
    yaxis=dict(range=[y_range_min, y_range_max],
               showticklabels=False, showgrid=False, zeroline=False,
               scaleanchor="x", scaleratio=1),
    legend=dict(orientation="h", y=1.08, font=dict(size=11)),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    updatemenus=[dict(
        type="buttons", showactive=False,
        y=-0.28, x=0.5, xanchor="center",
        buttons=[
            dict(label="▶ 재생", method="animate",
                 args=[None, {"frame": {"duration": 80, "redraw": True},
                              "fromcurrent": True, "transition": {"duration": 0}}]),
            dict(label="⏹ 정지", method="animate",
                 args=[[None], {"frame": {"duration": 0}, "mode": "immediate"}]),
        ],
    )],
)
st.plotly_chart(fig_anim, use_container_width=True)

# ─── 경사도별 제동거리 비교 ───────────────────────────
st.markdown("### 📊 경사도별 & 속도별 정지거리 비교")

tab1, tab2 = st.tabs(["경사도별 비교", "속도별 비교"])

with tab1:
    grades_list = list(range(-20, 21, 2))
    d_bs_grade, d_rs_grade, colors_grade = [], [], []
    for gr in grades_list:
        th = np.arctan(gr / 100)
        dec = g * (mu * np.cos(th) + np.sin(th))
        if dec > 0:
            d_bs_grade.append((v0**2) / (2 * dec))
            d_rs_grade.append(d_reaction)
        else:
            d_bs_grade.append(None)
            d_rs_grade.append(None)
        colors_grade.append("#DC2626" if gr == grade else "#FCA5A5")

    grade_labels = [f"{gr}%" for gr in grades_list]

    fig_g = go.Figure()
    fig_g.add_trace(go.Bar(
        x=grade_labels, y=d_rs_grade, name="반응거리",
        marker_color=["#16A34A" if gr == grade else "#86EFAC" for gr in grades_list],
        hovertemplate="%{x}<br>반응거리: %{y:.1f} m<extra></extra>",
    ))
    fig_g.add_trace(go.Bar(
        x=grade_labels, y=d_bs_grade, name="제동거리",
        marker_color=colors_grade,
        hovertemplate="%{x}<br>제동거리: %{y:.1f} m<extra></extra>",
    ))
    fig_g.add_shape(
        type="line", x0=0, x1=1, xref="paper",
        y0=d_total_flat, y1=d_total_flat,
        line=dict(dash="dot", color="#6B7280", width=1.5),
    )
    fig_g.add_annotation(
        x=1, xref="paper", y=d_total_flat,
        text=f"  평지 기준 ({d_total_flat:.0f}m)",
        showarrow=False, font=dict(size=10, color="#6B7280"), xanchor="left",
    )
    fig_g.update_layout(
        barmode="stack", height=340,
        margin=dict(l=0, r=60, t=10, b=0),
        xaxis_title="경사도 (%)",
        yaxis_title="거리 (m)",
        legend=dict(orientation="h", y=1.05, font=dict(size=11)),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
    )
    st.caption(f"진한 색 = 현재 경사도 ({grade}%)")
    st.plotly_chart(fig_g, use_container_width=True)

with tab2:
    speeds = [30, 50, 60, 80, 100, 120, 150]
    d_rs_sp = [s/3.6 * t_reaction for s in speeds]
    d_bs_sp = [(s/3.6)**2 / (2 * deceleration) for s in speeds]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=[f"{s} km/h" for s in speeds], y=d_rs_sp, name="반응거리",
        marker_color=["#16A34A" if s == speed_kmh else "#86EFAC" for s in speeds],
        hovertemplate="%{x}<br>반응거리: %{y:.1f} m<extra></extra>",
    ))
    fig_bar.add_trace(go.Bar(
        x=[f"{s} km/h" for s in speeds], y=d_bs_sp, name="제동거리",
        marker_color=["#DC2626" if s == speed_kmh else "#FCA5A5" for s in speeds],
        hovertemplate="%{x}<br>제동거리: %{y:.1f} m<extra></extra>",
    ))
    fig_bar.update_layout(
        barmode="stack", height=340,
        margin=dict(l=0, r=0, t=10, b=0),
        yaxis_title="거리 (m)",
        legend=dict(orientation="h", y=1.05, font=dict(size=11)),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
    )
    st.caption(f"현재 경사도 {grade}% 반영 · 진한 색 = 현재 속도 ({speed_kmh} km/h)")
    st.plotly_chart(fig_bar, use_container_width=True)

# ─── 공식 설명 ────────────────────────────────────────
with st.expander("📐 공식 보기"):
    st.markdown(f"""
    **경사 포함 감속도**
    $$a = g(\\mu \\cos\\theta + \\sin\\theta) = 9.8 \\times ({mu} \\times \\cos {np.degrees(theta):.1f}° + \\sin {np.degrees(theta):.1f}°) = {deceleration:.2f} \\text{{ m/s²}}$$

    > 오르막(+θ): sinθ > 0 → 감속 증가 → 제동거리 **감소**  
    > 내리막(−θ): sinθ < 0 → 감속 감소 → 제동거리 **증가**

    **반응거리** = v × t = {v0:.2f} × {t_reaction} = **{d_reaction:.2f} m**

    **제동거리** = v² / 2a = {v0:.2f}² / (2 × {deceleration:.2f}) = **{d_braking:.2f} m**

    **정지거리** = **{d_total:.2f} m** (평지 대비 {delta_d:+.1f} m)
    """)

st.divider()
st.caption(
    f"μ = {mu} | 경사도 = {grade}% | θ = {np.degrees(theta):.2f}° | "
    f"g = 9.8 m/s² | 감속도 = {deceleration:.2f} m/s²"
)
