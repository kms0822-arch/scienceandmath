import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="🏔️ 오르막 자유 운동",
    page_icon="🏔️",
    layout="wide",
)

g = 9.8

ROAD_CONDITIONS = {
    "🌞 건조한 아스팔트": 0.75,
    "🌧️ 젖은 아스팔트":  0.45,
    "🌨️ 눈길":           0.25,
    "🧊 빙판":           0.08,
}

# ─────────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────────
st.title("🏔️ 오르막 자유 운동 시뮬레이터")
st.caption(
    "브레이크 없이 오르막을 올라가다 최고점에 멈추고, "
    "다시 미끄러져 내려오는 운동을 시뮬레이션합니다"
)

# ─────────────────────────────────────────────
# 입력
# ─────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    speed_kmh = st.slider("🚀 초기 속도 (km/h)", 10, 200, 60, step=10)
with c2:
    road  = st.selectbox("🛣️ 노면 상태", list(ROAD_CONDITIONS.keys()))
with c3:
    grade = st.slider("⛰️ 경사도 (%)", 5, 45, 20, step=1,
                      help="오르막 경사도 (양수 = 오르막)")

mu    = ROAD_CONDITIONS[road]
v0    = speed_kmh / 3.6          # m/s
theta = np.arctan(grade / 100)   # 라디안
cos_t = np.cos(theta)
sin_t = np.sin(theta)

# ─────────────────────────────────────────────
# 물리 계산
# ─────────────────────────────────────────────
# 올라갈 때: 중력 + 마찰 모두 운동 방향 반대
a_up   = g * (sin_t + mu * cos_t)
# 내려올 때: 중력(추진) - 마찰(저항)
a_down = g * (sin_t - mu * cos_t)

can_slide = a_down > 0   # 마찰 < 중력 성분일 때만 미끄러짐

t_up  = v0 / a_up
s_max = v0 ** 2 / (2 * a_up)
h_max = s_max * sin_t

if can_slide:
    t_down  = np.sqrt(2 * s_max / a_down)
    v_final = np.sqrt(2 * a_down * s_max)
else:
    t_down  = None
    v_final = 0.0

# 에너지 (단위 질량 기준, J/kg)
KE_init     = 0.5 * v0 ** 2
PE_max      = g * h_max
E_fric_up   = mu * g * cos_t * s_max
E_fric_down = mu * g * cos_t * s_max if can_slide else 0
KE_final    = 0.5 * v_final ** 2

# ─────────────────────────────────────────────
# 상태 배너
# ─────────────────────────────────────────────
if not can_slide:
    st.info(
        f"🛑 **차가 다시 내려오지 않습니다.** "
        f"경사각 tan θ = {np.tan(theta):.3f} < μ = {mu}  →  "
        f"정적 마찰력이 차를 붙잡습니다."
    )
else:
    loss_pct = (KE_init - KE_final) / KE_init * 100
    st.success(
        f"🔄 차가 최고점에서 미끄러져 내려옵니다.  "
        f"출발 속도의 **{v_final/v0*100:.1f}%** 속력으로 도착 "
        f"(마찰 에너지 손실 **{loss_pct:.1f}%**)."
    )

# ─────────────────────────────────────────────
# KPI 카드
# ─────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("📏 최고점까지 거리",  f"{s_max:.1f} m")
k2.metric("🏔️ 최대 높이",       f"{h_max:.1f} m")
k3.metric("⏱️ 올라가는 시간",    f"{t_up:.2f} s")
k4.metric("⏱️ 내려오는 시간",    f"{t_down:.2f} s" if can_slide else "—")
k5.metric("💨 바닥 도착 속력",   f"{v_final*3.6:.1f} km/h" if can_slide else "정지")

st.divider()

# ─────────────────────────────────────────────
# 시간축 데이터
# ─────────────────────────────────────────────
T_total = t_up + (t_down if can_slide else 0)
N = 400
t_arr = np.linspace(0, T_total, N)
s_arr, v_arr, h_arr, KE_arr, PE_arr, Eth_arr = [], [], [], [], [], []

for t in t_arr:
    if t <= t_up:
        s = v0*t - 0.5*a_up*t**2
        v = v0 - a_up*t
    else:
        tp = t - t_up
        if can_slide:
            s = max(0.0, s_max - 0.5*a_down*tp**2)
            v = -a_down * tp          # 음수 = 내려오는 방향
        else:
            s = s_max
            v = 0.0
    h  = s * sin_t
    KE = 0.5 * v**2
    PE = g * h
    Eth = max(0.0, KE_init - KE - PE)

    s_arr.append(s);  v_arr.append(v)
    h_arr.append(h);  KE_arr.append(KE)
    PE_arr.append(PE); Eth_arr.append(Eth)

s_arr  = np.array(s_arr);  v_arr  = np.array(v_arr)
h_arr  = np.array(h_arr);  KE_arr = np.array(KE_arr)
PE_arr = np.array(PE_arr); Eth_arr = np.array(Eth_arr)

def base_layout(title, xtitle, ytitle, height=280):
    return dict(
        title=dict(text=title, font=dict(size=13)),
        xaxis_title=xtitle, yaxis_title=ytitle,
        height=height,
        margin=dict(l=0, r=0, t=36, b=0),
        legend=dict(orientation="h", y=1.15, font=dict(size=10)),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
    )

# ─────────────────────────────────────────────
# 그래프 3개
# ─────────────────────────────────────────────
ch1, ch2, ch3 = st.columns(3)

# ── 위치-시간 ─────────────────────────────────
with ch1:
    fig_s = go.Figure()
    # 올라가는 구간
    mask_up   = t_arr <= t_up
    mask_down = t_arr > t_up
    fig_s.add_trace(go.Scatter(
        x=t_arr[mask_up], y=s_arr[mask_up],
        name="올라가는 구간",
        line=dict(color="#16A34A", width=2.5),
        fill="tozeroy", fillcolor="rgba(22,163,74,0.08)",
        hovertemplate="t=%{x:.2f}s<br>거리=%{y:.1f}m<extra></extra>",
    ))
    if can_slide and mask_down.any():
        fig_s.add_trace(go.Scatter(
            x=t_arr[mask_down], y=s_arr[mask_down],
            name="내려오는 구간",
            line=dict(color="#DC2626", width=2.5),
            fill="tozeroy", fillcolor="rgba(220,38,38,0.08)",
            hovertemplate="t=%{x:.2f}s<br>거리=%{y:.1f}m<extra></extra>",
        ))
    # 최고점 마커
    fig_s.add_trace(go.Scatter(
        x=[t_up], y=[s_max], mode="markers",
        marker=dict(size=12, color="#7C3AED", symbol="star"),
        name="최고점", hovertemplate=f"최고점<br>t={t_up:.2f}s<br>s={s_max:.1f}m<extra></extra>",
    ))
    # t_up 수직선
    fig_s.add_shape(type="line", x0=t_up, x1=t_up, y0=0, y1=1, yref="paper",
                    line=dict(dash="dot", color="#7C3AED", width=1))
    fig_s.update_layout(**base_layout("📍 거리 – 시간", "시간 (s)", "경사면 거리 (m)"))
    st.plotly_chart(fig_s, use_container_width=True)

# ── 속도-시간 ─────────────────────────────────
with ch2:
    fig_v = go.Figure()
    v_kmh = v_arr * 3.6
    fig_v.add_trace(go.Scatter(
        x=t_arr[mask_up], y=v_kmh[mask_up],
        name="올라가는 구간",
        line=dict(color="#16A34A", width=2.5),
        fill="tozeroy", fillcolor="rgba(22,163,74,0.08)",
        hovertemplate="t=%{x:.2f}s<br>속도=%{y:.1f}km/h<extra></extra>",
    ))
    if can_slide and mask_down.any():
        fig_v.add_trace(go.Scatter(
            x=t_arr[mask_down], y=v_kmh[mask_down],
            name="내려오는 구간",
            line=dict(color="#DC2626", width=2.5),
            fill="tozeroy", fillcolor="rgba(220,38,38,0.08)",
            hovertemplate="t=%{x:.2f}s<br>속도=%{y:.1f}km/h (하강)<extra></extra>",
        ))
    fig_v.add_shape(type="line", x0=t_up, x1=t_up, y0=0, y1=1, yref="paper",
                    line=dict(dash="dot", color="#7C3AED", width=1))
    fig_v.add_shape(type="line", x0=0, x1=1, xref="paper", y0=0, y1=0,
                    line=dict(dash="dash", color="#6B7280", width=1))
    fig_v.update_layout(**base_layout("💨 속도 – 시간", "시간 (s)", "속도 (km/h)"))
    st.plotly_chart(fig_v, use_container_width=True)

# ── 에너지-시간 ───────────────────────────────
with ch3:
    fig_e = go.Figure()
    fig_e.add_trace(go.Scatter(
        x=t_arr, y=KE_arr,
        name="운동 에너지 (KE)",
        stackgroup="energy",
        line=dict(color="#2563EB", width=0),
        fillcolor="rgba(37,99,235,0.55)",
        hovertemplate="t=%{x:.2f}s<br>KE=%{y:.1f} J/kg<extra></extra>",
    ))
    fig_e.add_trace(go.Scatter(
        x=t_arr, y=PE_arr,
        name="위치 에너지 (PE)",
        stackgroup="energy",
        line=dict(color="#16A34A", width=0),
        fillcolor="rgba(22,163,74,0.55)",
        hovertemplate="t=%{x:.2f}s<br>PE=%{y:.1f} J/kg<extra></extra>",
    ))
    fig_e.add_trace(go.Scatter(
        x=t_arr, y=Eth_arr,
        name="마찰 열에너지",
        stackgroup="energy",
        line=dict(color="#DC2626", width=0),
        fillcolor="rgba(220,38,38,0.45)",
        hovertemplate="t=%{x:.2f}s<br>열=%{y:.1f} J/kg<extra></extra>",
    ))
    # 초기 에너지 기준선
    fig_e.add_shape(type="line", x0=0, x1=1, xref="paper", y0=KE_init, y1=KE_init,
                    line=dict(dash="dot", color="#6B7280", width=1.2))
    fig_e.add_annotation(
        x=1, xref="paper", y=KE_init,
        text=f"  초기 KE ({KE_init:.0f} J/kg)", showarrow=False,
        font=dict(size=9, color="#6B7280"), xanchor="left",
    )
    fig_e.add_shape(type="line", x0=t_up, x1=t_up, y0=0, y1=1, yref="paper",
                    line=dict(dash="dot", color="#7C3AED", width=1))
    fig_e.update_layout(**base_layout("⚡ 에너지 – 시간 (단위 질량)", "시간 (s)", "에너지 (J/kg)"))
    st.plotly_chart(fig_e, use_container_width=True)

st.caption(
    "🟣 점선 = 최고점 도달 시각 · "
    "에너지 합계(KE+PE+열)는 항상 초기 운동에너지와 같습니다 (에너지 보존)"
)

st.divider()

# ─────────────────────────────────────────────
# 애니메이션
# ─────────────────────────────────────────────
st.markdown("### 🎬 오르막 운동 애니메이션")
st.caption("▶ 재생: 초록=올라가는 중 · 보라=최고점 · 빨강=내려오는 중")

N_up   = 55
N_mid  = 14
N_dn   = 55 if can_slide else 0

t_up_f  = np.linspace(0, t_up, N_up)
s_up_f  = v0*t_up_f - 0.5*a_up*t_up_f**2
v_up_f  = v0 - a_up*t_up_f

s_mid_f = np.full(N_mid, s_max)
v_mid_f = np.zeros(N_mid)

if can_slide:
    t_dn_f = np.linspace(0, t_down, N_dn)
    s_dn_f = np.maximum(0, s_max - 0.5*a_down*t_dn_f**2)
    v_dn_f = -a_down * t_dn_f
else:
    s_dn_f = np.array([])
    v_dn_f = np.array([])

all_s_f = np.concatenate([s_up_f, s_mid_f, s_dn_f])
all_v_f = np.concatenate([v_up_f, v_mid_f, v_dn_f])
phases  = (["up"]*N_up + ["top"]*N_mid +
           (["down"]*N_dn if can_slide else []))

PCOL = {"up": "#16A34A", "top": "#7C3AED", "down": "#DC2626"}
PLBL = {"up": "⬆️ 올라가는 중", "top": "🏔️ 최고점", "down": "⬇️ 내려오는 중"}

# 도로 좌표
slope_len = s_max * 1.25
sx0, sy0 = 0, 0
sx1, sy1 = slope_len * cos_t, slope_len * sin_t
top_x, top_y = s_max * cos_t, s_max * sin_t

# x, y 축 범위
x_pad = s_max * cos_t * 0.15
y_pad = max(s_max * sin_t * 0.35, 1.5)
xr = [-x_pad, slope_len * cos_t + x_pad]
yr = [-y_pad * 0.5, slope_len * sin_t + y_pad]

frames = []
for i, (s, v, ph) in enumerate(zip(all_s_f, all_v_f, phases)):
    cx = s * cos_t
    cy = s * sin_t
    col = PCOL[ph]
    spd = abs(v) * 3.6

    frames.append(go.Frame(
        data=[
            # 지면 (수평)
            go.Scatter(x=[xr[0], xr[1]], y=[0, 0], mode="lines",
                       line=dict(color="#CBD5E1", width=2), showlegend=False),
            # 경사면
            go.Scatter(x=[sx0, sx1], y=[sy0, sy1], mode="lines",
                       line=dict(color="#64748B", width=7), showlegend=False),
            # 높이 지시선 (수직 파선)
            go.Scatter(x=[cx, cx], y=[0, cy], mode="lines",
                       line=dict(color="#93C5FD", width=1.5, dash="dash"),
                       showlegend=False),
            # 수평 거리 지시선 (점선)
            go.Scatter(x=[0, cx], y=[cy, cy], mode="lines",
                       line=dict(color="#FCD34D", width=1.2, dash="dot"),
                       showlegend=False),
            # 최고점 별 마커
            go.Scatter(x=[top_x], y=[top_y], mode="markers",
                       marker=dict(size=14, color="#7C3AED", symbol="star"),
                       showlegend=False),
            # 차량
            go.Scatter(x=[cx], y=[cy], mode="markers",
                       marker=dict(size=26, color=col, symbol="square",
                                   line=dict(width=2, color="white")),
                       showlegend=False),
            # 속도 텍스트
            go.Scatter(
                x=[cx + x_pad*0.4], y=[cy + y_pad*0.18],
                mode="text",
                text=[f"{spd:.1f} km/h"],
                textfont=dict(size=12, color=col),
                showlegend=False,
            ),
            # 높이 텍스트
            go.Scatter(
                x=[cx + x_pad*0.1], y=[cy * 0.5],
                mode="text",
                text=[f"h = {cy:.1f} m"],
                textfont=dict(size=10, color="#3B82F6"),
                showlegend=False,
            ),
            # 상태 레이블
            go.Scatter(
                x=[(xr[0]+xr[1])*0.5], y=[yr[1]*0.88],
                mode="text",
                text=[PLBL[ph]],
                textfont=dict(size=13, color=col),
                showlegend=False,
            ),
        ],
        name=str(i),
    ))

# 초기 데이터
init_data = [
    go.Scatter(x=[xr[0], xr[1]], y=[0, 0], mode="lines",
               line=dict(color="#CBD5E1", width=2), showlegend=False),
    go.Scatter(x=[sx0, sx1], y=[sy0, sy1], mode="lines",
               line=dict(color="#64748B", width=7), showlegend=False),
    go.Scatter(x=[0, 0], y=[0, 0], mode="lines",
               line=dict(color="#93C5FD", width=1.5, dash="dash"), showlegend=False),
    go.Scatter(x=[0, 0], y=[0, 0], mode="lines",
               line=dict(color="#FCD34D", width=1.2, dash="dot"), showlegend=False),
    go.Scatter(x=[top_x], y=[top_y], mode="markers",
               marker=dict(size=14, color="#7C3AED", symbol="star"), showlegend=False),
    go.Scatter(x=[0], y=[0], mode="markers",
               marker=dict(size=26, color="#16A34A", symbol="square",
                           line=dict(width=2, color="white")), showlegend=False),
    go.Scatter(x=[x_pad*0.4], y=[y_pad*0.18], mode="text",
               text=[f"{speed_kmh} km/h"],
               textfont=dict(size=12, color="#16A34A"), showlegend=False),
    go.Scatter(x=[x_pad*0.1], y=[0], mode="text",
               text=["h = 0.0 m"],
               textfont=dict(size=10, color="#3B82F6"), showlegend=False),
    go.Scatter(x=[(xr[0]+xr[1])*0.5], y=[yr[1]*0.88], mode="text",
               text=["⬆️ 올라가는 중"],
               textfont=dict(size=13, color="#16A34A"), showlegend=False),
]

fig_anim = go.Figure(data=init_data, frames=frames)
fig_anim.update_layout(
    height=360,
    margin=dict(l=10, r=10, t=10, b=80),
    xaxis=dict(range=xr, title="수평 거리 (m)", showgrid=False,
               tickfont=dict(size=10)),
    yaxis=dict(range=yr, title="높이 (m)", showgrid=False,
               tickfont=dict(size=10),
               scaleanchor="x", scaleratio=1),
    plot_bgcolor="rgba(241,245,249,0.4)",
    paper_bgcolor="rgba(0,0,0,0)",
    updatemenus=[dict(
        type="buttons", showactive=False,
        y=-0.22, x=0.5, xanchor="center",
        buttons=[
            dict(label="▶ 재생", method="animate",
                 args=[None, {"frame": {"duration": 55, "redraw": True},
                              "fromcurrent": True,
                              "transition": {"duration": 0}}]),
            dict(label="⏹ 정지", method="animate",
                 args=[[None], {"frame": {"duration": 0},
                                "mode": "immediate"}]),
        ],
    )],
)
st.plotly_chart(fig_anim, use_container_width=True)

# ─────────────────────────────────────────────
# 물리 요약
# ─────────────────────────────────────────────
st.divider()
with st.expander("📐 물리 공식 & 계산 과정 보기"):
    st.markdown(f"""
    **올라가는 운동** (감속)
    $$a_{{up}} = g(\\sin\\theta + \\mu\\cos\\theta)
    = 9.8 \\times ({sin_t:.3f} + {mu} \\times {cos_t:.3f})
    = {a_up:.3f} \\text{{ m/s²}}$$

    **최고점까지 거리**
    $$s_{{max}} = \\frac{{v_0^2}}{{2a_{{up}}}}
    = \\frac{{{v0:.2f}^2}}{{2 \\times {a_up:.3f}}}
    = {s_max:.2f} \\text{{ m}}$$

    **최대 높이**
    $$h_{{max}} = s_{{max}} \\cdot \\sin\\theta
    = {s_max:.2f} \\times {sin_t:.3f}
    = {h_max:.2f} \\text{{ m}}$$

    ---

    **내려오는 운동** {'(가속)' if can_slide else '— 마찰이 중력보다 커서 정지'}

    {"$$a_{down} = g(\\sin\\theta - \\mu\\cos\\theta) = " +
     f"9.8 \\times ({sin_t:.3f} - {mu} \\times {cos_t:.3f}) = {a_down:.3f}" +
     "\\text{ m/s²}$$" if can_slide else
     f"$$\\tan\\theta = {np.tan(theta):.3f} < \\mu = {mu}  \\Rightarrow \\text{{정지}}$$"}

    {"**바닥 도착 속력**" if can_slide else ""}
    {"$$v_{final} = \\sqrt{2 a_{down} s_{max}} = " +
     f"\\sqrt{{2 \\times {a_down:.3f} \\times {s_max:.2f}}} = {v_final:.2f}" +
     "\\text{ m/s} = " + f"{v_final*3.6:.1f}" + "\\text{ km/h}$$" if can_slide else ""}

    ---

    **에너지 정산 (단위 질량)**

    | 항목 | 값 (J/kg) |
    |------|----------|
    | 초기 운동에너지 KE₀ | {KE_init:.1f} |
    | 최고점 위치에너지 PE | {PE_max:.1f} |
    | 올라갈 때 마찰 손실 | {E_fric_up:.1f} |
    | 내려올 때 마찰 손실 | {E_fric_down:.1f} |
    | 최종 운동에너지 KE_f | {KE_final:.1f} |
    | **오차 (에너지 보존 검증)** | **{abs(KE_init - PE_max - E_fric_up - E_fric_down - KE_final):.3f}** |
    """)

st.caption(
    f"μ = {mu} | 경사도 = {grade}% | θ = {np.degrees(theta):.2f}° | g = 9.8 m/s²"
)
