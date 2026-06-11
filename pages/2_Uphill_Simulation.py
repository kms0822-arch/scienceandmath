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
    grade = st.slider("⛰️ 경사도 (%)", 5, 45, 20, step=1)

mu    = ROAD_CONDITIONS[road]
v0    = speed_kmh / 3.6
theta = np.arctan(grade / 100)
cos_t = np.cos(theta)
sin_t = np.sin(theta)

# ─────────────────────────────────────────────
# 물리 계산
# ─────────────────────────────────────────────
a_up   = g * (sin_t + mu * cos_t)
a_down = g * (sin_t - mu * cos_t)
can_slide = a_down > 0

t_up  = v0 / a_up
s_max = v0 ** 2 / (2 * a_up)
h_max = s_max * sin_t

if can_slide:
    t_down  = np.sqrt(2 * s_max / a_down)
    v_final = np.sqrt(2 * a_down * s_max)
else:
    t_down  = None
    v_final = 0.0

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
        f"tan θ = {np.tan(theta):.3f} < μ = {mu}  →  정적 마찰이 차를 붙잡습니다."
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
t_arr  = np.linspace(0, T_total, N)
s_arr, v_arr, h_arr = [], [], []
KE_arr, PE_arr, Eth_arr = [], [], []

for t in t_arr:
    if t <= t_up:
        s = v0*t - 0.5*a_up*t**2
        v = v0 - a_up*t
    else:
        tp = t - t_up
        s  = max(0.0, s_max - 0.5*a_down*tp**2) if can_slide else s_max
        v  = (-a_down*tp) if can_slide else 0.0
    h   = s * sin_t
    KE  = 0.5 * v**2
    PE  = g * h
    Eth = max(0.0, KE_init - KE - PE)
    s_arr.append(s); v_arr.append(v); h_arr.append(h)
    KE_arr.append(KE); PE_arr.append(PE); Eth_arr.append(Eth)

s_arr  = np.array(s_arr);  v_arr  = np.array(v_arr)
h_arr  = np.array(h_arr);  KE_arr = np.array(KE_arr)
PE_arr = np.array(PE_arr); Eth_arr = np.array(Eth_arr)

mask_up   = t_arr <= t_up
mask_down = t_arr >  t_up

def blayout(title, xt, yt, h=280):
    return dict(
        title=dict(text=title, font=dict(size=13)),
        xaxis_title=xt, yaxis_title=yt,
        height=h, margin=dict(l=0,r=0,t=36,b=0),
        legend=dict(orientation="h", y=1.15, font=dict(size=10)),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
    )

# ─────────────────────────────────────────────
# 그래프 3개 (시간 기반)
# ─────────────────────────────────────────────
ch1, ch2, ch3 = st.columns(3)

with ch1:
    fig_s = go.Figure()
    fig_s.add_trace(go.Scatter(
        x=t_arr[mask_up], y=s_arr[mask_up], name="올라가는 구간",
        line=dict(color="#16A34A", width=2.5),
        fill="tozeroy", fillcolor="rgba(22,163,74,0.08)",
        hovertemplate="t=%{x:.2f}s<br>거리=%{y:.1f}m<extra></extra>",
    ))
    if can_slide and mask_down.any():
        fig_s.add_trace(go.Scatter(
            x=t_arr[mask_down], y=s_arr[mask_down], name="내려오는 구간",
            line=dict(color="#DC2626", width=2.5),
            fill="tozeroy", fillcolor="rgba(220,38,38,0.08)",
            hovertemplate="t=%{x:.2f}s<br>거리=%{y:.1f}m<extra></extra>",
        ))
    fig_s.add_trace(go.Scatter(
        x=[t_up], y=[s_max], mode="markers",
        marker=dict(size=12, color="#7C3AED", symbol="star"),
        name="최고점",
    ))
    fig_s.add_shape(type="line", x0=t_up, x1=t_up, y0=0, y1=1, yref="paper",
                    line=dict(dash="dot", color="#7C3AED", width=1))
    fig_s.update_layout(**blayout("📍 거리 – 시간", "시간 (s)", "경사면 거리 (m)"))
    st.plotly_chart(fig_s, use_container_width=True)

with ch2:
    fig_v = go.Figure()
    v_kmh = v_arr * 3.6
    fig_v.add_trace(go.Scatter(
        x=t_arr[mask_up], y=v_kmh[mask_up], name="올라가는 구간",
        line=dict(color="#16A34A", width=2.5),
        fill="tozeroy", fillcolor="rgba(22,163,74,0.08)",
        hovertemplate="t=%{x:.2f}s<br>속도=%{y:.1f}km/h<extra></extra>",
    ))
    if can_slide and mask_down.any():
        fig_v.add_trace(go.Scatter(
            x=t_arr[mask_down], y=v_kmh[mask_down], name="내려오는 구간",
            line=dict(color="#DC2626", width=2.5),
            fill="tozeroy", fillcolor="rgba(220,38,38,0.08)",
            hovertemplate="t=%{x:.2f}s<br>속도=%{y:.1f}km/h<extra></extra>",
        ))
    fig_v.add_shape(type="line", x0=t_up, x1=t_up, y0=0, y1=1, yref="paper",
                    line=dict(dash="dot", color="#7C3AED", width=1))
    fig_v.add_shape(type="line", x0=0, x1=1, xref="paper", y0=0, y1=0,
                    line=dict(dash="dash", color="#6B7280", width=1))
    fig_v.update_layout(**blayout("💨 속도 – 시간", "시간 (s)", "속도 (km/h)"))
    st.plotly_chart(fig_v, use_container_width=True)

with ch3:
    fig_e = go.Figure()
    fig_e.add_trace(go.Scatter(
        x=t_arr, y=KE_arr, name="운동에너지 KE",
        stackgroup="e", line=dict(color="#2563EB", width=0),
        fillcolor="rgba(37,99,235,0.55)",
        hovertemplate="t=%{x:.2f}s<br>KE=%{y:.1f}J/kg<extra></extra>",
    ))
    fig_e.add_trace(go.Scatter(
        x=t_arr, y=PE_arr, name="위치에너지 PE",
        stackgroup="e", line=dict(color="#16A34A", width=0),
        fillcolor="rgba(22,163,74,0.55)",
        hovertemplate="t=%{x:.2f}s<br>PE=%{y:.1f}J/kg<extra></extra>",
    ))
    fig_e.add_trace(go.Scatter(
        x=t_arr, y=Eth_arr, name="마찰 열에너지",
        stackgroup="e", line=dict(color="#DC2626", width=0),
        fillcolor="rgba(220,38,38,0.45)",
        hovertemplate="t=%{x:.2f}s<br>열=%{y:.1f}J/kg<extra></extra>",
    ))
    fig_e.add_shape(type="line", x0=0, x1=1, xref="paper",
                    y0=KE_init, y1=KE_init,
                    line=dict(dash="dot", color="#6B7280", width=1.2))
    fig_e.add_annotation(x=1, xref="paper", y=KE_init,
                         text=f"  초기 KE ({KE_init:.0f} J/kg)",
                         showarrow=False, font=dict(size=9, color="#6B7280"),
                         xanchor="left")
    fig_e.add_shape(type="line", x0=t_up, x1=t_up, y0=0, y1=1, yref="paper",
                    line=dict(dash="dot", color="#7C3AED", width=1))
    fig_e.update_layout(**blayout("⚡ 에너지 – 시간", "시간 (s)", "에너지 (J/kg)"))
    st.plotly_chart(fig_e, use_container_width=True)

st.caption("🟣 점선 = 최고점 도달 시각  ·  에너지 합계(KE+PE+열)는 항상 일정 (에너지 보존)")

st.divider()

# ─────────────────────────────────────────────
# 위치-속력 이차함수 그래프
# ─────────────────────────────────────────────
st.markdown("### 📐 위치 – 속력 관계 그래프 (이차함수)")
st.caption(
    "속력을 x축, 위치를 y축으로 놓으면 **꼭짓점이 최고점인 이차함수(포물선)** 모양이 나타납니다."
)

# 공식 안내
st.markdown(
    f"""
    **올라갈 때:** $s = s_{{max}} - \\dfrac{{v^2}}{{2a_{{up}}}}$
    &nbsp;&nbsp;→&nbsp;&nbsp;
    $s = {s_max:.2f} - \\dfrac{{v^2}}{{{2*a_up:.2f}}}$
    &emsp;|&emsp;
    **내려올 때:** $s = s_{{max}} - \\dfrac{{v^2}}{{2a_{{down}}}}$
    {"&nbsp;&nbsp;→&nbsp;&nbsp; $s = "+f"{s_max:.2f} - \\dfrac{{v^2}}{{{2*a_down:.2f}}}$" if can_slide else "  *(정지)*"}
    """
)

# 부드러운 곡선 데이터
v_up_line   = np.linspace(0, v0, 300)
s_up_line   = s_max - v_up_line**2 / (2 * a_up)   # 이차함수!

if can_slide:
    v_dn_line = np.linspace(0, v_final, 300)
    s_dn_line = s_max - v_dn_line**2 / (2 * a_down)
else:
    v_dn_line = np.array([0])
    s_dn_line = np.array([s_max])

gl, gr = st.columns(2)

# ── 왼쪽: 속력(x) vs 위치(y) — 이차함수 포물선 ──────────
with gl:
    fig_sv = go.Figure()

    # 올라가는 곡선 (왼쪽 포물선)
    fig_sv.add_trace(go.Scatter(
        x=v_up_line * 3.6,
        y=s_up_line,
        name="올라가는 구간",
        line=dict(color="#16A34A", width=3),
        fill="tozerox",
        fillcolor="rgba(22,163,74,0.08)",
        hovertemplate="속력: %{x:.1f} km/h<br>위치: %{y:.2f} m<extra></extra>",
    ))

    # 내려오는 곡선 (오른쪽 포물선)
    if can_slide:
        fig_sv.add_trace(go.Scatter(
            x=v_dn_line * 3.6,
            y=s_dn_line,
            name="내려오는 구간",
            line=dict(color="#DC2626", width=3),
            fill="tozerox",
            fillcolor="rgba(220,38,38,0.08)",
            hovertemplate="속력: %{x:.1f} km/h<br>위치: %{y:.2f} m<extra></extra>",
        ))

    # 꼭짓점 (최고점)
    fig_sv.add_trace(go.Scatter(
        x=[0], y=[s_max],
        mode="markers+text",
        marker=dict(size=14, color="#7C3AED", symbol="star"),
        text=[f"  꼭짓점 (최고점)\n  s={s_max:.1f}m"],
        textposition="middle right",
        textfont=dict(size=10, color="#7C3AED"),
        name="꼭짓점 (최고점)",
        hovertemplate=f"최고점<br>속력=0<br>위치={s_max:.1f}m<extra></extra>",
    ))

    # 출발점
    fig_sv.add_trace(go.Scatter(
        x=[speed_kmh], y=[0],
        mode="markers+text",
        marker=dict(size=11, color="#16A34A", symbol="circle"),
        text=[f"  출발 ({speed_kmh}km/h)"],
        textposition="middle right",
        textfont=dict(size=10, color="#16A34A"),
        name="출발점",
    ))

    # 도착점
    if can_slide:
        fig_sv.add_trace(go.Scatter(
            x=[v_final*3.6], y=[0],
            mode="markers+text",
            marker=dict(size=11, color="#DC2626", symbol="circle"),
            text=[f"  도착 ({v_final*3.6:.1f}km/h)"],
            textposition="middle right",
            textfont=dict(size=10, color="#DC2626"),
            name="도착점",
        ))

    v_xmax = max(speed_kmh, v_final*3.6 if can_slide else 0) * 1.2
    fig_sv.update_layout(
        **blayout("속력 (x) – 위치 (y) : 이차함수 포물선", "속력 v (km/h)", "위치 s (m)", h=380),
    )
    fig_sv.update_xaxes(range=[0, v_xmax])
    fig_sv.update_yaxes(range=[-s_max*0.1, s_max*1.3])
    st.plotly_chart(fig_sv, use_container_width=True)
    st.caption(
        f"꼭짓점 (0, {s_max:.1f}m) 에서 시작하는 **아래로 볼록 포물선**  "
        f"·  기울기 = -1/(2a)"
    )

# ── 오른쪽: v² vs s — 직선 확인 ──────────────────────────
with gr:
    s_range = np.linspace(0, s_max, 300)
    v2_up   = np.maximum(0, v0**2 - 2*a_up*s_range)
    v2_dn   = np.maximum(0, 2*a_down*(s_max - s_range)) if can_slide else None

    fig_v2s = go.Figure()

    fig_v2s.add_trace(go.Scatter(
        x=s_range, y=v2_up,
        name="올라가는 구간 (v²)",
        line=dict(color="#16A34A", width=2.5),
        fill="tozeroy", fillcolor="rgba(22,163,74,0.08)",
        hovertemplate="위치: %{x:.1f}m<br>v²=%{y:.1f}m²/s²<extra></extra>",
    ))

    if can_slide:
        fig_v2s.add_trace(go.Scatter(
            x=s_range, y=v2_dn,
            name="내려오는 구간 (v²)",
            line=dict(color="#DC2626", width=2.5),
            fill="tozeroy", fillcolor="rgba(220,38,38,0.08)",
            hovertemplate="위치: %{x:.1f}m<br>v²=%{y:.1f}m²/s²<extra></extra>",
        ))

    # 기울기 레이블
    fig_v2s.add_annotation(
        x=s_max*0.5, y=v0**2 - 2*a_up*s_max*0.5,
        text=f"기울기 = -2a_up<br>= -{2*a_up:.2f} m/s²",
        showarrow=True, arrowhead=2, arrowcolor="#16A34A",
        font=dict(size=10, color="#16A34A"), ax=40, ay=-30,
    )

    fig_v2s.update_layout(
        **blayout("위치 (x) – v² (y) : 직선 확인", "위치 s (m)", "속력² v² (m²/s²)", h=380),
    )
    st.plotly_chart(fig_v2s, use_container_width=True)
    st.caption(
        f"v² = v₀² − 2a·s  →  v²와 s는 **선형 관계**  "
        f"·  기울기 = −2a_up = {-2*a_up:.2f}"
    )

# 핵심 인사이트
ins1, ins2 = st.columns(2)
with ins1:
    st.markdown(
        f"""<div style="background:#F5F3FF;border-left:4px solid #7C3AED;
            padding:12px;border-radius:8px;font-size:13px;">
            <b>📌 이차함수 공식 (올라갈 때)</b><br>
            s = −v²/(2×{a_up:.2f}) + {s_max:.2f}<br>
            <span style="color:#6B7280;font-size:11px;">
            a = −{1/(2*a_up):.4f}, b = 0, c = {s_max:.2f}
            </span>
        </div>""", unsafe_allow_html=True,
    )
with ins2:
    if can_slide:
        st.markdown(
            f"""<div style="background:#FEF2F2;border-left:4px solid #DC2626;
                padding:12px;border-radius:8px;font-size:13px;">
                <b>📌 이차함수 공식 (내려올 때)</b><br>
                s = −v²/(2×{a_down:.2f}) + {s_max:.2f}<br>
                <span style="color:#6B7280;font-size:11px;">
                a_up ≠ a_down → 두 포물선의 폭이 다름
                </span>
            </div>""", unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """<div style="background:#F1F5F9;border-left:4px solid #94A3B8;
                padding:12px;border-radius:8px;font-size:13px;">
                🛑 마찰이 커서 내려오지 않으므로<br>내려가는 포물선이 없습니다.
            </div>""", unsafe_allow_html=True,
        )

st.divider()

# ─────────────────────────────────────────────
# 애니메이션
# ─────────────────────────────────────────────
st.markdown("### 🎬 오르막 운동 애니메이션")
st.caption("🟢 올라가는 중  ·  🟣 최고점  ·  🔴 내려오는 중  ·  파란 선 = 높이  ·  노란 선 = 수평 거리")

N_UP  = 55
N_MID = 16
N_DN  = 55 if can_slide else 0

t_up_f  = np.linspace(0, t_up, N_UP)
s_up_f  = v0*t_up_f - 0.5*a_up*t_up_f**2
v_up_f  = (v0 - a_up*t_up_f) * 3.6

s_mid_f = np.full(N_MID, s_max)
v_mid_f = np.zeros(N_MID)

if can_slide:
    t_dn_f = np.linspace(0, t_down, N_DN)
    s_dn_f = np.maximum(0, s_max - 0.5*a_down*t_dn_f**2)
    v_dn_f = a_down * t_dn_f * 3.6
else:
    s_dn_f = np.array([])
    v_dn_f = np.array([])

all_s = np.concatenate([s_up_f, s_mid_f, s_dn_f])
all_v = np.concatenate([v_up_f, v_mid_f, v_dn_f])
phases = (["up"]*N_UP + ["top"]*N_MID +
          (["down"]*N_DN if can_slide else []))

PCOL = {"up": "#16A34A", "top": "#7C3AED", "down": "#DC2626"}
PLBL = {"up": "⬆️ 올라가는 중", "top": "🏔️ 최고점!", "down": "⬇️ 내려오는 중"}

slope_len  = s_max * 1.25
top_x, top_y = s_max*cos_t, s_max*sin_t
xr = [-s_max*cos_t*0.12, slope_len*cos_t*1.08]
yr = [-top_y*0.3, top_y*1.5]

# 경사면 좌표
sx0, sy0 = 0, 0
sx1, sy1 = slope_len*cos_t, slope_len*sin_t

# 지나온 궤적용 누적 좌표
trail_x_up = [s*cos_t for s in s_up_f]
trail_y_up = [s*sin_t for s in s_up_f]

frames = []
for i, (s, spd, ph) in enumerate(zip(all_s, all_v, phases)):
    cx, cy = s*cos_t, s*sin_t
    col = PCOL[ph]

    # 궤적 표시
    if ph == "up":
        tr_x = trail_x_up[:i+1]
        tr_y = trail_y_up[:i+1]
        tr_col = "#86EFAC"
    elif ph == "top":
        tr_x = trail_x_up
        tr_y = trail_y_up
        tr_col = "#86EFAC"
    else:  # down
        dn_idx = i - N_UP - N_MID
        dn_x = [s_dn_f[j]*cos_t for j in range(dn_idx+1)]
        dn_y = [s_dn_f[j]*sin_t for j in range(dn_idx+1)]
        tr_x = trail_x_up + dn_x
        tr_y = trail_y_up + dn_y
        tr_col = "#86EFAC"

    frames.append(go.Frame(
        data=[
            # 지면
            go.Scatter(x=[xr[0], xr[1]], y=[0, 0], mode="lines",
                       line=dict(color="#CBD5E1", width=2), showlegend=False),
            # 경사면
            go.Scatter(x=[sx0, sx1], y=[sy0, sy1], mode="lines",
                       line=dict(color="#64748B", width=8), showlegend=False),
            # 궤적 (trail)
            go.Scatter(x=tr_x, y=tr_y, mode="lines",
                       line=dict(color=tr_col, width=3, dash="dot"),
                       showlegend=False),
            # 높이 지시선
            go.Scatter(x=[cx, cx], y=[0, cy], mode="lines",
                       line=dict(color="#93C5FD", width=2, dash="dash"),
                       showlegend=False),
            # 수평 거리 지시선
            go.Scatter(x=[0, cx], y=[cy, cy], mode="lines",
                       line=dict(color="#FCD34D", width=1.5, dash="dot"),
                       showlegend=False),
            # 최고점 별
            go.Scatter(x=[top_x], y=[top_y], mode="markers",
                       marker=dict(size=15, color="#7C3AED", symbol="star"),
                       showlegend=False),
            # 차량
            go.Scatter(x=[cx], y=[cy], mode="markers",
                       marker=dict(size=28, color=col, symbol="square",
                                   line=dict(width=2, color="white")),
                       showlegend=False),
            # 속력 텍스트
            go.Scatter(x=[cx + abs(xr[1]-xr[0])*0.06],
                       y=[cy + (yr[1]-yr[0])*0.1],
                       mode="text",
                       text=[f"{spd:.1f} km/h"],
                       textfont=dict(size=13, color=col),
                       showlegend=False),
            # 높이 텍스트
            go.Scatter(x=[cx + abs(xr[1]-xr[0])*0.02],
                       y=[cy * 0.5],
                       mode="text",
                       text=[f"h={cy:.1f}m"],
                       textfont=dict(size=11, color="#3B82F6"),
                       showlegend=False),
            # 상태 레이블
            go.Scatter(x=[(xr[0]+xr[1])*0.5], y=[yr[1]*0.88],
                       mode="text",
                       text=[PLBL[ph]],
                       textfont=dict(size=14, color=col),
                       showlegend=False),
        ],
        name=str(i),
    ))

# 초기 프레임
init_data = [
    go.Scatter(x=[xr[0], xr[1]], y=[0, 0], mode="lines",
               line=dict(color="#CBD5E1", width=2), showlegend=False),
    go.Scatter(x=[sx0, sx1], y=[sy0, sy1], mode="lines",
               line=dict(color="#64748B", width=8), showlegend=False),
    go.Scatter(x=[], y=[], mode="lines",
               line=dict(color="#86EFAC", width=3, dash="dot"), showlegend=False),
    go.Scatter(x=[0, 0], y=[0, 0], mode="lines",
               line=dict(color="#93C5FD", width=2, dash="dash"), showlegend=False),
    go.Scatter(x=[0, 0], y=[0, 0], mode="lines",
               line=dict(color="#FCD34D", width=1.5, dash="dot"), showlegend=False),
    go.Scatter(x=[top_x], y=[top_y], mode="markers",
               marker=dict(size=15, color="#7C3AED", symbol="star"), showlegend=False),
    go.Scatter(x=[0], y=[0], mode="markers",
               marker=dict(size=28, color="#16A34A", symbol="square",
                           line=dict(width=2, color="white")), showlegend=False),
    go.Scatter(x=[abs(xr[1]-xr[0])*0.06], y=[(yr[1]-yr[0])*0.1],
               mode="text", text=[f"{speed_kmh} km/h"],
               textfont=dict(size=13, color="#16A34A"), showlegend=False),
    go.Scatter(x=[abs(xr[1]-xr[0])*0.02], y=[0],
               mode="text", text=["h=0.0m"],
               textfont=dict(size=11, color="#3B82F6"), showlegend=False),
    go.Scatter(x=[(xr[0]+xr[1])*0.5], y=[yr[1]*0.88],
               mode="text", text=["⬆️ 올라가는 중"],
               textfont=dict(size=14, color="#16A34A"), showlegend=False),
]

fig_anim = go.Figure(data=init_data, frames=frames)
fig_anim.update_layout(
    height=380,
    margin=dict(l=10, r=10, t=10, b=80),
    xaxis=dict(range=xr, title="수평 거리 (m)", showgrid=False,
               tickfont=dict(size=10)),
    yaxis=dict(range=yr, title="높이 (m)", showgrid=False,
               tickfont=dict(size=10),
               scaleanchor="x", scaleratio=1),
    plot_bgcolor="rgba(241,245,249,0.5)",
    paper_bgcolor="rgba(0,0,0,0)",
    updatemenus=[dict(
        type="buttons", showactive=False,
        y=-0.20, x=0.5, xanchor="center",
        buttons=[
            dict(label="▶ 재생", method="animate",
                 args=[None, {"frame": {"duration": 55, "redraw": True},
                              "fromcurrent": True,
                              "transition": {"duration": 0}}]),
            dict(label="⏹ 정지", method="animate",
                 args=[[None], {"frame": {"duration": 0}, "mode": "immediate"}]),
        ],
    )],
)
st.plotly_chart(fig_anim, use_container_width=True)

# ─────────────────────────────────────────────
# 공식 요약
# ─────────────────────────────────────────────
with st.expander("📐 물리 공식 & 계산 보기"):
    st.markdown(f"""
    **올라갈 때 감속도**
    $$a_{{up}} = g(\\sin\\theta + \\mu\\cos\\theta)
    = 9.8 \\times ({sin_t:.3f} + {mu}\\times{cos_t:.3f})
    = {a_up:.3f}\\text{{ m/s²}}$$

    **최고점 거리**
    $$s_{{max}} = \\frac{{v_0^2}}{{2a_{{up}}}}
    = \\frac{{{v0:.2f}^2}}{{2\\times{a_up:.3f}}}
    = {s_max:.2f}\\text{{ m}}$$

    **위치-속력 이차함수 (올라갈 때)**
    $$s = -\\frac{{1}}{{2a_{{up}}}}v^2 + s_{{max}}
    = -{1/(2*a_up):.4f}\\,v^2 + {s_max:.2f}$$

    {"**내려갈 때 가속도**" if can_slide else ""}
    {"$$a_{down} = g(\\sin\\theta - \\mu\\cos\\theta) = " + f"9.8\\times({sin_t:.3f}-{mu}\\times{cos_t:.3f}) = {a_down:.3f}" + "\\text{ m/s²}$$" if can_slide else ""}

    | 항목 | 값 (J/kg) |
    |------|----------|
    | 초기 운동에너지 | {KE_init:.1f} |
    | 최고점 위치에너지 | {PE_max:.1f} |
    | 올라갈 때 마찰 손실 | {E_fric_up:.1f} |
    | 내려올 때 마찰 손실 | {E_fric_down:.1f} |
    | 최종 운동에너지 | {KE_final:.1f} |
    """)

st.caption(
    f"μ = {mu} | 경사도 = {grade}% | θ = {np.degrees(theta):.2f}° | g = 9.8 m/s²"
)
