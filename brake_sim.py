import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="🚗 제동거리 시뮬레이터", page_icon="🚗", layout="wide")

# ─── 상수 ───────────────────────────────────────────
g = 9.8

ROAD_CONDITIONS = {
    "🌞 건조한 아스팔트": 0.75,
    "🌧️ 젖은 아스팔트":  0.45,
    "🌨️ 눈길":           0.25,
    "🧊 빙판":           0.08,
}

# ─── 헤더 ───────────────────────────────────────────
st.title("🚗 제동거리 시뮬레이터")
st.caption("속도 · 노면 상태 · 반응시간에 따른 정지거리를 시뮬레이션합니다")

# ─── 입력 ───────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    speed_kmh  = st.slider("🚀 초기 속도 (km/h)", 10, 200, 60, step=10)
with c2:
    road       = st.selectbox("🛣️ 노면 상태", list(ROAD_CONDITIONS.keys()))
with c3:
    t_reaction = st.slider("⏱️ 반응 시간 (초)", 0.5, 3.0, 1.0, step=0.1)

mu           = ROAD_CONDITIONS[road]
v0           = speed_kmh / 3.6          # m/s
deceleration = mu * g                   # m/s²
t_braking    = v0 / deceleration        # 제동에 걸리는 시간
t_total      = t_reaction + t_braking

d_reaction   = v0 * t_reaction
d_braking    = v0 ** 2 / (2 * mu * g)
d_total      = d_reaction + d_braking

# ─── KPI 카드 ─────────────────────────────────────
st.markdown("")
k1, k2, k3, k4 = st.columns(4)
k1.metric("🟢 반응거리",      f"{d_reaction:.1f} m",  help="브레이크를 밟기까지 이동한 거리")
k2.metric("🔴 제동거리",      f"{d_braking:.1f} m",   help="브레이크 후 완전히 멈출 때까지")
k3.metric("📏 정지거리 합계", f"{d_total:.1f} m")
k4.metric("📉 감속도",        f"{deceleration:.1f} m/s²")

st.divider()

# ─── 시간-위치 / 시간-속도 데이터 ────────────────────
t_r = np.linspace(0, t_reaction, 40)
t_b = np.linspace(t_reaction, t_total, 80)

x_r = v0 * t_r
v_r = np.full_like(t_r, v0)

x_b = d_reaction + v0*(t_b - t_reaction) - 0.5*deceleration*(t_b - t_reaction)**2
v_b = v0 - deceleration*(t_b - t_reaction)

# ─── 그래프 2개 (위치-시간 / 속도-시간) ─────────────
left, right = st.columns(2)

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

# ─── 애니메이션 ───────────────────────────────────────
st.markdown("### 🎬 제동 애니메이션")
st.caption("▶ 재생을 눌러 차량이 멈추는 과정을 확인하세요")

N = 60
t_anim = np.linspace(0, t_total, N)
x_anim = []
for t in t_anim:
    if t <= t_reaction:
        x_anim.append(v0 * t)
    else:
        dt = t - t_reaction
        x_anim.append(min(d_reaction + v0*dt - 0.5*deceleration*dt**2, d_total))

pad = d_total * 0.12

frames = []
for i, (t, x) in enumerate(zip(t_anim, x_anim)):
    car_color = "#16A34A" if t <= t_reaction else "#DC2626"
    frames.append(go.Frame(
        data=[
            # 도로
            go.Scatter(x=[-pad, d_total + pad], y=[0, 0],
                       mode="lines", line=dict(color="#94A3B8", width=6),
                       showlegend=False),
            # 반응거리 표시선
            go.Scatter(x=[d_reaction, d_reaction], y=[-0.4, 0.4],
                       mode="lines", line=dict(color="#F59E0B", width=2, dash="dash"),
                       showlegend=False),
            # 정지선
            go.Scatter(x=[d_total, d_total], y=[-0.4, 0.4],
                       mode="lines", line=dict(color="#DC2626", width=2.5),
                       showlegend=False),
            # 차량
            go.Scatter(x=[x], y=[0],
                       mode="markers+text",
                       marker=dict(size=28, color=car_color, symbol="square",
                                   line=dict(width=1.5, color="white")),
                       text=["🚗"], textposition="middle center",
                       showlegend=False),
        ],
        name=str(i),
    ))

fig_anim = go.Figure(
    data=[
        go.Scatter(x=[-pad, d_total + pad], y=[0, 0],
                   mode="lines", line=dict(color="#94A3B8", width=6), showlegend=False),
        go.Scatter(x=[d_reaction, d_reaction], y=[-0.4, 0.4],
                   mode="lines", line=dict(color="#F59E0B", width=2, dash="dash"),
                   name="제동 시작"),
        go.Scatter(x=[d_total, d_total], y=[-0.4, 0.4],
                   mode="lines", line=dict(color="#DC2626", width=2.5),
                   name="정지선"),
        go.Scatter(x=[0], y=[0],
                   mode="markers",
                   marker=dict(size=28, color="#16A34A", symbol="square"),
                   showlegend=False),
    ],
    frames=frames,
)

fig_anim.update_layout(
    height=220,
    margin=dict(l=10, r=10, t=10, b=70),
    xaxis=dict(range=[-pad, d_total + pad], title="거리 (m)",
               tickfont=dict(size=11), showgrid=False),
    yaxis=dict(range=[-0.8, 0.8], showticklabels=False,
               showgrid=False, zeroline=False),
    legend=dict(orientation="h", y=1.08, font=dict(size=11)),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    updatemenus=[dict(
        type="buttons", showactive=False,
        y=-0.25, x=0.5, xanchor="center",
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

# ─── 속도별 정지거리 비교 막대 그래프 ────────────────
st.markdown("### 📊 속도별 정지거리 비교")

speeds  = [30, 50, 60, 80, 100, 120, 150]
d_rs    = [s/3.6 * t_reaction for s in speeds]
d_bs    = [(s/3.6)**2 / (2*mu*g) for s in speeds]
labels  = [f"{s} km/h" for s in speeds]
colors_r = ["#16A34A" if s == speed_kmh else "#86EFAC" for s in speeds]
colors_b = ["#DC2626" if s == speed_kmh else "#FCA5A5" for s in speeds]

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    x=labels, y=d_rs, name="반응거리",
    marker_color=colors_r,
    hovertemplate="%{x}<br>반응거리: %{y:.1f} m<extra></extra>",
))
fig_bar.add_trace(go.Bar(
    x=labels, y=d_bs, name="제동거리",
    marker_color=colors_b,
    hovertemplate="%{x}<br>제동거리: %{y:.1f} m<extra></extra>",
))
fig_bar.update_layout(
    barmode="stack",
    height=320,
    margin=dict(l=0, r=0, t=10, b=0),
    yaxis_title="거리 (m)",
    legend=dict(orientation="h", y=1.05, font=dict(size=11)),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
)
st.caption(f"진한 색 막대 = 현재 선택한 속도 ({speed_kmh} km/h)")
st.plotly_chart(fig_bar, use_container_width=True)

# ─── 공식 설명 ────────────────────────────────────────
with st.expander("📐 공식 보기"):
    st.markdown(f"""
    **반응거리** = v × t_반응 = {v0:.2f} × {t_reaction} = **{d_reaction:.2f} m**

    **제동거리** = v² / (2μg) = {v0:.2f}² / (2 × {mu} × 9.8) = **{d_braking:.2f} m**

    **정지거리** = 반응거리 + 제동거리 = **{d_total:.2f} m**

    > 속도가 2배 → 제동거리는 **4배**, 속도가 3배 → 제동거리는 **9배**
    """)

st.divider()
st.caption(f"μ = {mu} | g = 9.8 m/s² | 감속도 = {deceleration:.2f} m/s²")
