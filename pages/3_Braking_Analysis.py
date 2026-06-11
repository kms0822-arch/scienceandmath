import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="🔬 제동 변수 탐구",
    page_icon="🔬",
    layout="wide",
)

g = 9.8

ROAD_INFO = {
    "🌞 건조한 아스팔트": {"mu": 0.70, "color": "#2563EB"},   # 자전거 타이어 건식
    "🌧️ 젖은 아스팔트":  {"mu": 0.40, "color": "#10B981"},   # 자전거 타이어 습식
    "🌨️ 눈길":           {"mu": 0.20, "color": "#F59E0B"},   # 압설 위 자전거
    "🧊 빙판":           {"mu": 0.06, "color": "#EF4444"},   # 결빙 노면
    "🚵 자갈/흙길":      {"mu": 0.45, "color": "#7C3AED"},   # 비포장 MTB 노면
}

def blayout(title, xt, yt, h=360):
    return dict(
        title=dict(text=title, font=dict(size=13)),
        xaxis_title=xt, yaxis_title=yt,
        height=h, margin=dict(l=0, r=0, t=36, b=30),
        legend=dict(
            x=0.01, y=0.99,
            xanchor="left", yanchor="top",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#E5E7EB", borderwidth=1,
            font=dict(size=9),
        ),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
    )

# ─────────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────────
st.title("🚲 제동 변수 탐구 — 자전거 기준")
st.caption("자전거(탑승자 포함) 기준 | 질량 · 반응시간 · 노면 상태 · 속도가 제동거리에 미치는 영향을 분석합니다")

# ─────────────────────────────────────────────
# 입력
# ─────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    speed_kmh = st.slider("🚲 초기 속도 (km/h)", 5, 80, 25, step=1)
with c2:
    t_react   = st.slider("⏱️ 반응 시간 (s)",    0.5, 3.0, 1.2, step=0.1)
with c3:
    mass      = st.slider("⚖️ 총 질량 (kg)  탑승자+자전거", 40, 150, 75, step=5,
                          help="자전거(7~15kg) + 탑승자 체중 합산 | 제동거리 공식 d=v²/(2μg)에 질량이 없어요. 직접 바꿔보세요!")
with c4:
    road      = st.selectbox("🛣️ 기준 노면", list(ROAD_INFO.keys()))

mu    = ROAD_INFO[road]["mu"]
v0    = speed_kmh / 3.6
decel = mu * g
t_br  = v0 / decel
t_tot = t_react + t_br
d_r   = v0 * t_react
d_b   = v0**2 / (2 * decel)
d_tot = d_r + d_b
F_fric = mu * mass * g   # 마찰력 (N)

# ─────────────────────────────────────────────
# KPI
# ─────────────────────────────────────────────
k1,k2,k3,k4,k5,k6 = st.columns(6)
k1.metric("🟢 반응거리",  f"{d_r:.1f} m")
k2.metric("🔴 제동거리",  f"{d_b:.1f} m")
k3.metric("📏 정지거리",  f"{d_tot:.1f} m")
k4.metric("📉 감속도",    f"{decel:.2f} m/s²")
k5.metric("🔧 마찰력",    f"{F_fric/1000:.1f} kN",
          delta=f"= μ×(탑승자+자전거)×g = {mu}×{mass}×9.8")
k6.metric("⚖️ 질량 영향", "없음 ✗",
          help="F=μmg, a=F/m=μg → 질량 소거됨")

st.divider()

# ─────────────────────────────────────────────
# 시뮬레이션 애니메이션
# ─────────────────────────────────────────────
st.markdown("### 🎬 제동 시뮬레이션")
st.caption(f"반응 구간(🟢) {d_r:.1f}m  +  제동 구간(🔴) {d_b:.1f}m  =  정지거리 {d_tot:.1f}m")

# 노면별 배경색
ROAD_BG = {
    "🌞 건조한 아스팔트": "rgba(241,245,249,0.95)",
    "🌧️ 젖은 아스팔트":  "rgba(186,230,253,0.55)",
    "🌨️ 눈길":           "rgba(240,253,255,0.95)",
    "🧊 빙판":           "rgba(207,250,254,0.90)",
    "🚵 자갈/흙길":      "rgba(245,230,210,0.70)",
}
anim_bg = ROAD_BG.get(road, "rgba(241,245,249,0.95)")

# ★ 전체 구간을 균등 시간 간격으로 나눠 실제 속도와 동일하게
N_total = 200
t_all = np.linspace(0, t_tot, N_total)
all_x = np.where(
    t_all <= t_react,
    v0 * t_all,
    np.maximum(0, d_r + v0*(t_all - t_react) - 0.5*decel*(t_all - t_react)**2),
)
phases = ["r" if t <= t_react else "b" for t in t_all]
all_v  = np.where(
    t_all <= t_react,
    float(speed_kmh),
    np.maximum(0.0, (v0 - decel*(t_all - t_react)) * 3.6),
)
pad = d_tot * 0.1

frames = []
for i,(x,ph,spd) in enumerate(zip(all_x, phases, all_v)):
    col = "#16A34A" if ph=="r" else "#DC2626"
    frames.append(go.Frame(
        data=[
            go.Scatter(x=[-pad,d_tot+pad], y=[0,0], mode="lines",
                       line=dict(color="#94A3B8",width=6), showlegend=False),
            go.Scatter(x=[0,d_r,d_r,0], y=[-0.3,-0.3,0.3,0.3],
                       fill="toself", fillcolor="rgba(22,163,74,0.07)",
                       line=dict(width=0), showlegend=False),
            go.Scatter(x=[d_r,d_tot,d_tot,d_r], y=[-0.3,-0.3,0.3,0.3],
                       fill="toself", fillcolor="rgba(220,38,38,0.07)",
                       line=dict(width=0), showlegend=False),
            go.Scatter(x=[d_r,d_r], y=[-0.45,0.45], mode="lines",
                       line=dict(color="#F59E0B",width=2,dash="dash"), showlegend=False),
            go.Scatter(x=[d_tot,d_tot], y=[-0.45,0.45], mode="lines",
                       line=dict(color="#DC2626",width=2.5), showlegend=False),
            go.Scatter(x=[x], y=[0], mode="markers",
                       marker=dict(size=26,color=col,symbol="square",
                                   line=dict(width=2,color="white")), showlegend=False),
            go.Scatter(x=[x], y=[0.6], mode="text",
                       text=[f"{spd:.1f} km/h"],
                       textfont=dict(size=12,color=col), showlegend=False),
            go.Scatter(x=[x], y=[-0.6], mode="text",
                       text=[f"{mass} kg"],
                       textfont=dict(size=10,color="#94A3B8"), showlegend=False),
        ], name=str(i)
    ))

fig_anim = go.Figure(
    data=[
        go.Scatter(x=[-pad,d_tot+pad],y=[0,0],mode="lines",
                   line=dict(color="#94A3B8",width=6),showlegend=False),
        go.Scatter(x=[0,d_r,d_r,0],y=[-0.3,-0.3,0.3,0.3],fill="toself",
                   fillcolor="rgba(22,163,74,0.07)",line=dict(width=0),showlegend=False),
        go.Scatter(x=[d_r,d_tot,d_tot,d_r],y=[-0.3,-0.3,0.3,0.3],fill="toself",
                   fillcolor="rgba(220,38,38,0.07)",line=dict(width=0),showlegend=False),
        go.Scatter(x=[d_r,d_r],y=[-0.45,0.45],mode="lines",
                   line=dict(color="#F59E0B",width=2,dash="dash"),name="반응 끝"),
        go.Scatter(x=[d_tot,d_tot],y=[-0.45,0.45],mode="lines",
                   line=dict(color="#DC2626",width=2.5),name="정지선"),
        go.Scatter(x=[0],y=[0],mode="markers",
                   marker=dict(size=26,color="#16A34A",symbol="square",
                               line=dict(width=2,color="white")),showlegend=False),
        go.Scatter(x=[0],y=[0.6],mode="text",text=[f"{speed_kmh} km/h"],
                   textfont=dict(size=12,color="#16A34A"),showlegend=False),
        go.Scatter(x=[0],y=[-0.6],mode="text",text=[f"{mass} kg"],
                   textfont=dict(size=10,color="#94A3B8"),showlegend=False),
    ],
    frames=frames,
)
fig_anim.update_layout(
    height=220, margin=dict(l=10,r=10,t=10,b=70),
    xaxis=dict(range=[-pad, d_tot+pad*2], title="거리 (m)", showgrid=False),
    yaxis=dict(range=[-1,1], showticklabels=False, showgrid=False, zeroline=False),
    legend=dict(orientation="h", y=1.1, font=dict(size=11)),
    plot_bgcolor=anim_bg, paper_bgcolor="rgba(0,0,0,0)",
    updatemenus=[dict(
        type="buttons", showactive=False, y=-0.3, x=0.5, xanchor="center",
        buttons=[
            dict(label="▶ 재생", method="animate",
                 args=[None,{"frame":{"duration": max(10, round(t_tot*1000/N_total)),
                                      "redraw":True},
                             "fromcurrent":True,"transition":{"duration":0}}]),
            dict(label="⏹ 정지", method="animate",
                 args=[[None],{"frame":{"duration":0},"mode":"immediate"}]),
        ],
    )],
)
st.plotly_chart(fig_anim, use_container_width=True)

st.divider()

# ─────────────────────────────────────────────
# 탭 분석
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📉 제동거리-속력 그래프 (음수 포함)",
    "🛣️ 마찰계수 비교",
    "⏱️ 반응시간 비교",
    "⚖️ 질량 무관성",
])

# ══════════════════════════════════════════════
# Tab 1 — 제동거리-속력 그래프 & 반응시간 영향
# ══════════════════════════════════════════════
with tab1:
    st.markdown("#### 제동거리 – 속력 그래프와 반응시간에 따른 정지거리 변화")
    st.caption(
        "왼쪽: 제동거리(파란)는 v²에 비례하는 이차함수 · 반응거리(초록)는 v에 비례하는 일차함수 · 합이 정지거리  "
        "오른쪽: 반응시간이 길어질수록 곡선 전체가 위로 평행 이동"
    )

    tl, tr = st.columns(2)
    v_plot  = np.linspace(0, 80, 400)   # km/h
    v_ms_p  = v_plot / 3.6
    col_cur = ROAD_INFO[road]["color"]

    # ── 왼쪽: d_brake + d_react 분해 ──────────────────
    with tl:
        d_b_curve = v_ms_p**2 / (2*decel)          # 제동거리 (이차)
        d_r_curve = v_ms_p * t_react                # 반응거리 (일차)
        d_t_curve = d_b_curve + d_r_curve           # 정지거리 합

        fig_dv = go.Figure()

        # 제동거리 (이차함수)
        fig_dv.add_trace(go.Scatter(
            x=v_plot, y=d_b_curve,
            name="제동거리  d = v²/(2μg)",
            line=dict(color=col_cur, width=3),
            fill="tozeroy", fillcolor="rgba(37,99,235,0.08)",
            hovertemplate="v=%{x:.1f}km/h<br>제동=%{y:.1f}m<extra></extra>",
        ))

        # 반응거리 (일차함수) — 제동거리 위에 쌓임
        fig_dv.add_trace(go.Scatter(
            x=v_plot, y=d_t_curve,
            name=f"정지거리  d = v·{t_react}s + v²/(2μg)",
            line=dict(color="#F59E0B", width=2.5),
            fill="tonexty", fillcolor="rgba(245,158,11,0.12)",
            hovertemplate="v=%{x:.1f}km/h<br>정지=%{y:.1f}m<extra></extra>",
        ))

        # 현재 속도 마커
        fig_dv.add_trace(go.Scatter(
            x=[speed_kmh], y=[d_b],
            mode="markers", marker=dict(size=12, color=col_cur, symbol="star",
                                        line=dict(width=2, color="white")),
            name=f"현재 제동 {d_b:.1f}m", showlegend=True,
        ))
        fig_dv.add_trace(go.Scatter(
            x=[speed_kmh], y=[d_b + d_r],
            mode="markers", marker=dict(size=12, color="#F59E0B", symbol="star",
                                        line=dict(width=2, color="white")),
            name=f"현재 정지 {d_tot:.1f}m", showlegend=True,
        ))

        # 현재 속도 수직선
        fig_dv.add_shape(type="line", x0=speed_kmh, x1=speed_kmh,
                         y0=0, y1=1, yref="paper",
                         line=dict(dash="dash", color="#6B7280", width=1.2))

        # 공식 주석
        mid_v = 50
        mid_vm = mid_v / 3.6
        fig_dv.add_annotation(
            x=mid_v, y=mid_vm**2/(2*decel)*0.6,
            text=f"d = v²/{2*decel:.1f}<br>(이차함수)",
            showarrow=False, font=dict(size=10, color=col_cur),
            bgcolor="rgba(255,255,255,0.8)",
        )

        fig_dv.update_layout(
            **blayout("제동거리·정지거리 – 속력", "속력 v (km/h)", "거리 d (m)")
        )
        st.plotly_chart(fig_dv, use_container_width=True)
        st.caption(
            f"🔵 제동거리 = v²/(2μg) [이차함수]  "
            f"🟡 반응거리 = v × {t_react}s [일차함수]  "
            f"→ 정지거리 = 두 합"
        )

    # ── 오른쪽: 반응시간별 정지거리 곡선 비교 ──────────
    with tr:
        T_LIST   = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        T_COLORS = ["#CBD5E1","#93C5FD","#60A5FA","#3B82F6",
                    "#F59E0B","#EF4444","#7C3AED"]

        fig_tr = go.Figure()

        # 순수 제동거리 기준선
        fig_tr.add_trace(go.Scatter(
            x=v_plot, y=d_b_curve,
            name="반응 0s (제동거리만)",
            line=dict(color="#CBD5E1", width=2, dash="dot"),
            hovertemplate="반응0s<br>v=%{x:.1f}km/h<br>d=%{y:.1f}m<extra></extra>",
        ))

        for t_val, col in zip(T_LIST[1:], T_COLORS[1:]):
            d_stop = v_ms_p * t_val + d_b_curve
            lw  = 3.5 if abs(t_val - t_react) < 0.05 else 1.8
            fig_tr.add_trace(go.Scatter(
                x=v_plot, y=d_stop,
                name=f"반응 {t_val}s",
                line=dict(color=col, width=lw),
                hovertemplate=f"반응{t_val}s<br>v=%{{x:.1f}}km/h<br>d=%{{y:.1f}}m<extra></extra>",
            ))

        # 현재 반응시간 강조 마커
        d_cur_stop = v_ms_p * t_react + d_b_curve
        # (마커는 선 두께로 강조)

        # 현재 속도 수직선
        fig_tr.add_shape(type="line", x0=speed_kmh, x1=speed_kmh,
                         y0=0, y1=1, yref="paper",
                         line=dict(dash="dash", color="#6B7280", width=1.2))
        fig_tr.add_annotation(
            x=speed_kmh, y=1, yref="paper",
            text=f"  현재 {speed_kmh}km/h",
            showarrow=False, font=dict(size=10), xanchor="left",
        )

        # 반응거리 차이 표시 (두 특정 곡선 사이 간격)
        v_mark = speed_kmh / 3.6
        d_br_mark = v_mark**2 / (2*decel)
        d_tot_mark = v_mark * t_react + d_br_mark
        fig_tr.add_shape(type="line",
                         x0=speed_kmh, x1=speed_kmh,
                         y0=d_br_mark, y1=d_tot_mark,
                         line=dict(color="#16A34A", width=3))
        fig_tr.add_annotation(
            x=speed_kmh + 3, y=(d_br_mark + d_tot_mark)/2,
            text=f"+{d_r:.1f}m<br>(반응거리)",
            showarrow=False, font=dict(size=10, color="#16A34A"),
            xanchor="left",
        )

        fig_tr.update_layout(
            **blayout(f"반응시간별 정지거리 비교 (현재 {t_react}s 굵게)",
                      "속력 v (km/h)", "정지거리 (m)")
        )
        st.plotly_chart(fig_tr, use_container_width=True)
        st.caption(
            "반응시간이 클수록 곡선이 위로 이동 (간격 = v × Δt, 속력에 비례)  "
            f"·  현재 {speed_kmh}km/h에서 반응거리 = **{d_r:.1f}m**"
        )

# ══════════════════════════════════════════════
# Tab 2 — 마찰계수 비교
# ══════════════════════════════════════════════
with tab2:
    st.markdown("#### 마찰계수(노면 상태)별 제동거리-속력 그래프 비교")
    st.caption("조건을 선택해 같은 그래프에서 비교하세요 · 색이 다른 곡선이 각 노면 상태를 나타냅니다")

    selected = st.multiselect(
        "비교할 노면 조건 선택",
        options=list(ROAD_INFO.keys()),
        default=list(ROAD_INFO.keys()),
        key="mu_compare",
    )

    v_range = np.linspace(0, 80, 400)    # km/h (자전거 범위)
    v_ms    = v_range / 3.6

    m2l, m2r = st.columns(2)

    # ── 왼쪽: 제동거리만 ──────────────────────────
    with m2l:
        fig_mu1 = go.Figure()
        for cond in selected:
            info  = ROAD_INFO[cond]
            d_cur = v_ms**2 / (2 * info["mu"] * g)
            label = cond.split(" ",1)[-1]
            fig_mu1.add_trace(go.Scatter(
                x=v_range, y=d_cur,
                name=f"{label} (μ={info['mu']})",
                line=dict(color=info["color"], width=2.5),
                hovertemplate=f"μ={info['mu']}<br>v=%{{x}}km/h<br>d=%{{y:.1f}}m<extra></extra>",
            ))
            # 현재 속도 마커
            d_mark = (speed_kmh/3.6)**2 / (2*info["mu"]*g)
            fig_mu1.add_trace(go.Scatter(
                x=[speed_kmh], y=[d_mark], mode="markers",
                marker=dict(size=10, color=info["color"],
                            symbol="circle-open", line=dict(width=2)),
                showlegend=False,
                hovertemplate=f"{label}: {d_mark:.1f}m<extra></extra>",
            ))

        # 현재 속도 수직선
        fig_mu1.add_shape(type="line", x0=speed_kmh, x1=speed_kmh,
                          y0=0, y1=1, yref="paper",
                          line=dict(dash="dash", color="#374151", width=1.5))
        fig_mu1.add_annotation(x=speed_kmh, y=1, yref="paper",
                               text=f"  현재 {speed_kmh}km/h",
                               showarrow=False, font=dict(size=10), xanchor="left")

        fig_mu1.update_layout(
            **blayout("제동거리 비교 (반응시간 제외)", "속력 v (km/h)", "제동거리 d (m)")
        )
        st.plotly_chart(fig_mu1, use_container_width=True)

    # ── 오른쪽: 전체 정지거리 ────────────────────────
    with m2r:
        fig_mu2 = go.Figure()
        for cond in selected:
            info  = ROAD_INFO[cond]
            d_tot_cur = v_ms*t_react + v_ms**2/(2*info["mu"]*g)
            label = cond.split(" ",1)[-1]
            fig_mu2.add_trace(go.Scatter(
                x=v_range, y=d_tot_cur,
                name=f"{label} (μ={info['mu']})",
                line=dict(color=info["color"], width=2.5),
                hovertemplate=f"μ={info['mu']}<br>v=%{{x}}km/h<br>정지거리=%{{y:.1f}}m<extra></extra>",
            ))
            d_mark = (speed_kmh/3.6)*t_react + (speed_kmh/3.6)**2/(2*info["mu"]*g)
            fig_mu2.add_trace(go.Scatter(
                x=[speed_kmh], y=[d_mark], mode="markers",
                marker=dict(size=10, color=info["color"],
                            symbol="circle-open", line=dict(width=2)),
                showlegend=False,
            ))

        fig_mu2.add_shape(type="line", x0=speed_kmh, x1=speed_kmh,
                          y0=0, y1=1, yref="paper",
                          line=dict(dash="dash", color="#374151", width=1.5))
        fig_mu2.add_annotation(x=speed_kmh, y=1, yref="paper",
                               text=f"  현재 {speed_kmh}km/h",
                               showarrow=False, font=dict(size=10), xanchor="left")

        fig_mu2.update_layout(
            **blayout(f"전체 정지거리 비교 (반응시간 {t_react}s 포함)",
                      "속력 v (km/h)", "정지거리 (m)")
        )
        st.plotly_chart(fig_mu2, use_container_width=True)

    # 현재 속도에서 노면별 비교 표
    st.markdown(f"**현재 속도 {speed_kmh} km/h 에서 노면별 거리 비교**")
    rows = []
    for cond in list(ROAD_INFO.keys()):
        info = ROAD_INFO[cond]
        dr   = (speed_kmh/3.6)*t_react
        db   = (speed_kmh/3.6)**2 / (2*info["mu"]*g)
        rows.append({
            "노면": cond.split(" ",1)[-1],
            "μ": info["mu"],
            "반응거리(m)": round(dr,1),
            "제동거리(m)": round(db,1),
            "정지거리(m)": round(dr+db,1),
            "감속도(m/s²)": round(info["mu"]*g,2),
        })
    import pandas as pd
    df_mu = pd.DataFrame(rows)
    st.dataframe(df_mu, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════
# Tab 3 — 반응시간 비교
# ══════════════════════════════════════════════
with tab3:
    st.markdown("#### 반응시간에 따른 정지거리 변화 비교")
    st.caption("반응시간이 길어질수록 곡선 전체가 위로 평행 이동합니다 (제동거리는 그대로, 반응거리만 증가)")

    t_react_list = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    T_COLORS     = ["#7C3AED","#2563EB","#10B981","#F59E0B","#EA580C","#DC2626"]

    v_range2 = np.linspace(0, 80, 400)
    v_ms2    = v_range2 / 3.6
    d_brake2 = v_ms2**2 / (2*decel)   # 제동거리 (반응시간 무관)

    rt1, rt2 = st.columns(2)

    # ── 왼쪽: 전체 정지거리 비교 ──────────────────────
    with rt1:
        fig_rt1 = go.Figure()

        # 제동거리만 (기준선)
        fig_rt1.add_trace(go.Scatter(
            x=v_range2, y=d_brake2,
            name="제동거리만 (공통)",
            line=dict(color="#CBD5E1", width=2, dash="dot"),
            hovertemplate="v=%{x}km/h<br>제동거리=%{y:.1f}m<extra></extra>",
        ))

        for tr_val, col in zip(t_react_list, T_COLORS):
            d_stop = v_ms2*tr_val + d_brake2
            lw = 3 if abs(tr_val - t_react) < 0.05 else 1.8
            dash = "solid" if abs(tr_val - t_react) < 0.05 else "solid"
            fig_rt1.add_trace(go.Scatter(
                x=v_range2, y=d_stop,
                name=f"반응 {tr_val}s",
                line=dict(color=col, width=lw, dash=dash),
                hovertemplate=f"반응{tr_val}s<br>v=%{{x}}km/h<br>정지=%{{y:.1f}}m<extra></extra>",
            ))

        # 현재 속도 마커
        for tr_val, col in zip(t_react_list, T_COLORS):
            d_mark = (speed_kmh/3.6)*tr_val + (speed_kmh/3.6)**2/(2*decel)
            fig_rt1.add_trace(go.Scatter(
                x=[speed_kmh], y=[d_mark], mode="markers",
                marker=dict(size=8, color=col, symbol="circle-open",
                            line=dict(width=2)),
                showlegend=False,
            ))

        fig_rt1.add_shape(type="line", x0=speed_kmh, x1=speed_kmh,
                          y0=0, y1=1, yref="paper",
                          line=dict(dash="dash", color="#374151", width=1.5))

        fig_rt1.update_layout(
            **blayout(f"반응시간별 정지거리 ({road.split(' ',1)[-1]})",
                      "속력 v (km/h)", "정지거리 (m)")
        )
        st.plotly_chart(fig_rt1, use_container_width=True)
        st.caption("점선 = 제동거리만 (공통 기준선) · 반응시간이 커질수록 곡선이 위로 이동")

    # ── 오른쪽: 현재 속도에서 반응시간별 막대 ────────────
    with rt2:
        d_brakes_bar = [(speed_kmh/3.6)**2/(2*decel)] * len(t_react_list)
        d_reacts_bar = [(speed_kmh/3.6)*tr for tr in t_react_list]

        fig_rt2 = go.Figure()
        fig_rt2.add_trace(go.Bar(
            x=[f"{tr}s" for tr in t_react_list],
            y=d_reacts_bar, name="반응거리",
            marker_color=T_COLORS,
            opacity=0.75,
            hovertemplate="반응거리: %{y:.1f}m<extra></extra>",
        ))
        fig_rt2.add_trace(go.Bar(
            x=[f"{tr}s" for tr in t_react_list],
            y=d_brakes_bar, name="제동거리 (공통)",
            marker_color="#CBD5E1",
            hovertemplate="제동거리: %{y:.1f}m<extra></extra>",
        ))

        # 현재 반응시간 강조
        cur_idx = min(range(len(t_react_list)),
                      key=lambda i: abs(t_react_list[i]-t_react))
        fig_rt2.add_shape(
            type="rect",
            x0=cur_idx-0.5, x1=cur_idx+0.5, y0=0, y1=1, yref="paper",
            fillcolor="rgba(124,58,237,0.08)", line=dict(color="#7C3AED",width=1.5),
        )

        fig_rt2.update_layout(
            **blayout(f"현재 속도 {speed_kmh}km/h 에서 반응시간별 거리",
                      "반응시간", "거리 (m)", h=360),
            barmode="stack",
        )
        st.plotly_chart(fig_rt2, use_container_width=True)
        st.caption("🟣 강조 = 현재 설정 반응시간  ·  제동거리는 동일하고 반응거리만 늘어남")

    # 반응시간별 수치 표
    st.markdown(f"**속도 {speed_kmh} km/h · {road.split(' ',1)[-1]} 조건에서 반응시간별 정지거리**")
    rows_rt = []
    for tr_val in t_react_list:
        dr = round((speed_kmh/3.6)*tr_val, 1)
        db = round((speed_kmh/3.6)**2/(2*decel), 1)
        rows_rt.append({
            "반응시간(s)": tr_val,
            "반응거리(m)": dr,
            "제동거리(m)": db,
            "정지거리(m)": round(dr+db,1),
            "반응거리 비율(%)": round(dr/(dr+db)*100,1),
        })
    st.dataframe(pd.DataFrame(rows_rt), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════
# Tab 4 — 질량 무관성
# ══════════════════════════════════════════════
with tab4:
    st.markdown("#### 질량은 제동거리에 영향을 주지 않는다")
    st.caption("F = μmg, a = F/m = μg  →  질량 m이 소거됩니다!")

    # 공식 유도
    st.markdown("""
    $$F_{마찰} = \\mu m g \\qquad a = \\frac{F}{m} = \\frac{\\mu m g}{m} = \\mu g$$

    $$d = \\frac{v^2}{2a} = \\frac{v^2}{2\\mu g} \\quad \\leftarrow \\textbf{질량 없음!}$$
    """)

    masses_test = [40, 55, 70, 90, 110, 150]
    d_test = [(speed_kmh/3.6)**2 / (2*mu*g)] * len(masses_test)   # 모두 동일!
    F_tests = [mu * m * g / 1000 for m in masses_test]             # 마찰력은 다름

    ma1, ma2 = st.columns(2)

    with ma1:
        fig_m1 = go.Figure()
        bar_cols = ["#7C3AED" if m == mass else "#CBD5E1" for m in masses_test]
        fig_m1.add_trace(go.Bar(
            x=[f"{m}kg" for m in masses_test],
            y=d_test,
            marker_color=bar_cols,
            hovertemplate="질량: %{x}<br>제동거리: %{y:.2f}m<extra></extra>",
            showlegend=False,
        ))
        fig_m1.update_layout(
            **blayout(f"질량별 제동거리 ({speed_kmh}km/h, μ={mu})",
                      "질량 (kg)", "제동거리 (m)", h=320),
        )
        fig_m1.update_yaxes(range=[0, d_test[0]*1.5])
        st.plotly_chart(fig_m1, use_container_width=True)
        st.caption(f"모든 질량에서 제동거리 = **{d_test[0]:.2f} m** (완전히 동일)")

    with ma2:
        fig_m2 = go.Figure()
        fig_m2.add_trace(go.Bar(
            x=[f"{m}kg" for m in masses_test],
            y=F_tests,
            marker_color=["#7C3AED" if m == mass else "#A78BFA" for m in masses_test],
            hovertemplate="질량: %{x}<br>마찰력: %{y:.1f}kN<extra></extra>",
            showlegend=False,
        ))
        fig_m2.update_layout(
            **blayout("질량별 마찰력 (마찰력은 질량에 비례)",
                      "질량 (kg)", "마찰력 F (kN)", h=320),
        )
        st.plotly_chart(fig_m2, use_container_width=True)
        st.caption("마찰력은 질량에 비례해 커지지만, 가속도(=F/m)는 항상 μg로 일정!")

    st.info(
        f"💡 **핵심**: 무거운 차일수록 마찰력은 크지만, "
        f"질량도 커서 가속도가 같아집니다. "
        f"현재 감속도 = μg = {mu} × 9.8 = **{mu*9.8:.2f} m/s²** (질량과 무관)"
    )

st.divider()
st.caption(
    f"μ = {mu} | 반응시간 = {t_react}s | 질량 = {mass}kg | g = 9.8 m/s²"
)
