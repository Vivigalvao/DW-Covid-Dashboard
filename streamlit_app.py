import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import urllib.parse

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="COVID-19 ES · Dashboard",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #07090f 0%, #0c1020 50%, #080d1c 100%);
}
[data-testid="stHeader"] { background: transparent; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1020 0%, #0d1830 100%);
    border-right: 1px solid rgba(99,179,237,0.12);
}
[data-testid="stSidebar"] * { color: #cbd5e0; }

/* Metric Cards */
.metric-card {
    background: linear-gradient(135deg, rgba(13,21,37,0.95), rgba(17,28,53,0.9));
    border: 1px solid rgba(99,179,237,0.18);
    border-radius: 16px;
    padding: 20px 20px 16px 20px;
    margin-bottom: 8px;
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}
.metric-card:hover {
    transform: translateY(-3px);
    border-color: rgba(99,179,237,0.45);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.metric-icon  { font-size: 26px; margin-bottom: 8px; }
.metric-label { color: #718096; font-size: 10px; font-weight: 700;
                text-transform: uppercase; letter-spacing: 1.4px; margin-bottom: 4px; }
.metric-value { font-size: 26px; font-weight: 800; line-height: 1; margin-bottom: 4px; }
.metric-sub   { font-size: 11px; color: #4a5568; }

.metric-info    .metric-value { color: #63b3ed; }
.metric-danger  .metric-value { color: #fc8181; }
.metric-success .metric-value { color: #68d391; }
.metric-warning .metric-value { color: #f6ad55; }
.metric-purple  .metric-value { color: #b794f4; }

/* Section title */
.section-title {
    color: #e2e8f0; font-size: 14px; font-weight: 600;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(99,179,237,0.15);
    margin-bottom: 14px; margin-top: 4px;
}

/* Tabs */
[data-testid="stTabs"] [role="tablist"] {
    background: rgba(13,21,37,0.8);
    border-radius: 12px; padding: 4px; gap: 4px;
}
[data-testid="stTabs"] [role="tab"] {
    border-radius: 8px; color: #718096; font-weight: 500;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: rgba(99,179,237,0.2); color: #63b3ed;
}

/* Divider */
hr { border-color: rgba(99,179,237,0.1) !important; }

/* Dataframe */
[data-testid="stDataFrame"] { background: rgba(13,21,37,0.5); border-radius: 12px; }

/* Sidebar filter labels */
.sidebar-section { font-size: 11px; font-weight: 700; text-transform: uppercase;
                   letter-spacing: 1.2px; color: #4a5568; margin: 16px 0 8px 0; }
</style>
""", unsafe_allow_html=True)


# ─── DB Connection ────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Conectando ao banco de dados...")
def get_engine():
    db = st.secrets["postgres"]
    url = (
        f"postgresql+psycopg2://{urllib.parse.quote_plus(db['user'])}"
        f":{urllib.parse.quote_plus(db['password'])}"
        f"@{db['host']}:{db['port']}/{db['dbname']}"
    )
    return create_engine(url, pool_pre_ping=True)


@st.cache_data(ttl=3600, show_spinner=False)
def run_query(sql: str) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


# ─── Filter Helpers ───────────────────────────────────────────────────────────
def _safe_str(values: list) -> str:
    return "', '".join(str(v).replace("'", "''") for v in values)


def year_clause(anos: list, alias: str = "t") -> str:
    if not anos:
        return ""
    if len(anos) == 1:
        return f"AND {alias}.ano = {int(anos[0])}"
    return f"AND {alias}.ano IN ({', '.join(str(int(a)) for a in anos)})"


def macro_clause(macros: list, alias: str = "l") -> str:
    if not macros:
        return ""
    return f"AND {alias}.macrorregiao IN ('{_safe_str(macros)}')"


# ─── Load Filter Options ──────────────────────────────────────────────────────
with st.spinner("Carregando filtros..."):
    anos_all = run_query(
        "SELECT DISTINCT ano FROM dw.dim_tempo WHERE ano IS NOT NULL ORDER BY ano"
    )["ano"].tolist()

    macros_all = run_query(
        "SELECT DISTINCT macrorregiao FROM dw.dim_localidade "
        "WHERE macrorregiao IS NOT NULL ORDER BY macrorregiao"
    )["macrorregiao"].tolist()


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:8px 0 4px 0;'>
        <span style='font-size:40px'>🦠</span><br>
        <span style='font-size:18px;font-weight:800;color:#e2e8f0;'>COVID-19 ES</span><br>
        <span style='font-size:11px;color:#4a5568;letter-spacing:1px;'>DASHBOARD DE NOTIFICAÇÕES</span>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="sidebar-section">📅 Período</div>', unsafe_allow_html=True)
    anos_sel = st.multiselect(
        "Ano(s)", options=anos_all, default=anos_all, label_visibility="collapsed"
    )

    st.markdown('<div class="sidebar-section">🗺️ Macrorregião</div>', unsafe_allow_html=True)
    macros_sel = st.multiselect(
        "Macrorregião", options=macros_all, default=macros_all, label_visibility="collapsed"
    )

    st.divider()
    st.markdown(
        "<span style='color:#2d3748;font-size:10px;'>Fonte: SESA-ES · DW COVID-19<br>"
        "Hospedado em: Supabase + Streamlit Cloud</span>",
        unsafe_allow_html=True
    )

# Fall back to "all" if nothing selected
if not anos_sel:
    anos_sel = anos_all
if not macros_sel:
    macros_sel = macros_all

yf = year_clause(anos_sel)
mf = macro_clause(macros_sel)


# ─── Number Formatter ─────────────────────────────────────────────────────────
def fmt(v, dec: int = 0) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    if dec == 0:
        return f"{int(v):,}".replace(",", ".")
    # Brazilian decimal style
    formatted = f"{float(v):,.{dec}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊  Visão Geral",
    "🗺️  Geografia",
    "👥  Perfil do Paciente",
    "🏥  Clínico",
])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — Visão Geral
# ═════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── KPIs ──────────────────────────────────────────────────────────────────
    kpi_sql = f"""
        SELECT
            SUM(f.qtd_notificacao)                                              AS total_notif,
            SUM(f.flag_confirmado)                                              AS total_confirm,
            SUM(f.flag_obito_covid)                                             AS total_obitos,
            SUM(f.flag_cura)                                                    AS total_curados,
            SUM(f.flag_internado)                                               AS total_internados,
            ROUND(AVG(CASE WHEN f.flag_confirmado = 1
                      THEN f.idade_anos END)::numeric, 1)                       AS media_idade,
            ROUND(SUM(f.flag_obito_covid)::numeric
                  / NULLIF(SUM(f.flag_confirmado), 0) * 100, 2)                AS taxa_letalidade
        FROM dw.fato_notificacao_covid f
        JOIN dw.dim_tempo      t ON f.sk_data_notificacao = t.sk_tempo
        JOIN dw.dim_localidade l ON f.sk_local            = l.sk_local
        WHERE 1=1 {yf} {mf}
    """
    kpi = run_query(kpi_sql).iloc[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "🔔", "Total Notificações",  fmt(kpi.total_notif),    "",                                          "metric-info"),
        (c2, "✅", "Casos Confirmados",   fmt(kpi.total_confirm),  "",                                          "metric-info"),
        (c3, "💀", "Óbitos COVID",        fmt(kpi.total_obitos),   f"Letalidade: {fmt(kpi.taxa_letalidade,2)}%","metric-danger"),
        (c4, "💚", "Curados",            fmt(kpi.total_curados),  "",                                          "metric-success"),
        (c5, "🏥", "Internações",         fmt(kpi.total_internados),f"Idade média: {fmt(kpi.media_idade,1)} anos","metric-warning"),
    ]
    for col, icon, label, value, sub, cls in cards:
        col.markdown(f"""
        <div class="metric-card {cls}">
            <div class="metric-icon">{icon}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}&nbsp;</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Time Series ────────────────────────────────────────────────────────────
    ts_sql = f"""
        SELECT
            TRIM(t.ano_mes)         AS ano_mes,
            t.ano, t.mes,
            SUM(f.qtd_notificacao)  AS notificacoes,
            SUM(f.flag_confirmado)  AS confirmados,
            SUM(f.flag_obito_covid) AS obitos,
            SUM(f.flag_cura)        AS curados
        FROM dw.fato_notificacao_covid f
        JOIN dw.dim_tempo      t ON f.sk_data_notificacao = t.sk_tempo
        JOIN dw.dim_localidade l ON f.sk_local            = l.sk_local
        WHERE 1=1 {yf} {mf}
        GROUP BY TRIM(t.ano_mes), t.ano, t.mes
        ORDER BY t.ano, t.mes
    """
    ts_df = run_query(ts_sql)

    col_l, col_r = st.columns([3, 1])

    with col_l:
        st.markdown('<div class="section-title">📈 Evolução Mensal — Notificações COVID-19</div>', unsafe_allow_html=True)
        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(
            x=ts_df["ano_mes"], y=ts_df["notificacoes"],
            name="Notificações", fill="tozeroy",
            line=dict(color="#63b3ed", width=2),
            fillcolor="rgba(99,179,237,0.08)"
        ))
        fig_ts.add_trace(go.Scatter(
            x=ts_df["ano_mes"], y=ts_df["confirmados"],
            name="Confirmados", line=dict(color="#f6ad55", width=2)
        ))
        fig_ts.add_trace(go.Scatter(
            x=ts_df["ano_mes"], y=ts_df["obitos"],
            name="Óbitos", line=dict(color="#fc8181", width=2.5)
        ))
        fig_ts.add_trace(go.Scatter(
            x=ts_df["ano_mes"], y=ts_df["curados"],
            name="Curados", line=dict(color="#68d391", width=2)
        ))
        fig_ts.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            height=360, margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_ts, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">📅 Por Semana Epidemiológica</div>', unsafe_allow_html=True)
        se_sql = f"""
            SELECT
                t.semana_epidemiologica AS se,
                SUM(f.flag_confirmado)  AS confirmados
            FROM dw.fato_notificacao_covid f
            JOIN dw.dim_tempo      t ON f.sk_data_notificacao = t.sk_tempo
            JOIN dw.dim_localidade l ON f.sk_local            = l.sk_local
            WHERE 1=1 {yf} {mf}
            GROUP BY t.semana_epidemiologica
            ORDER BY t.semana_epidemiologica
        """
        se_df = run_query(se_sql)
        fig_se = px.bar(
            se_df, x="se", y="confirmados",
            labels={"se": "SE", "confirmados": "Confirmados"},
            color="confirmados", color_continuous_scale="Blues"
        )
        fig_se.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,
            xaxis_title="Semana Epidemiológica", yaxis_title="",
            height=360, margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_se, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — Geografia
# ═════════════════════════════════════════════════════════════════════════════
with tab2:

    geo_sql = f"""
        SELECT
            l.macrorregiao,
            l.municipio,
            SUM(f.qtd_notificacao)  AS notificacoes,
            SUM(f.flag_confirmado)  AS confirmados,
            SUM(f.flag_obito_covid) AS obitos,
            SUM(f.flag_cura)        AS curados,
            SUM(f.flag_internado)   AS internados,
            ROUND(SUM(f.flag_obito_covid)::numeric
                  / NULLIF(SUM(f.flag_confirmado), 0) * 100, 2) AS letalidade
        FROM dw.fato_notificacao_covid f
        JOIN dw.dim_localidade l ON f.sk_local            = l.sk_local
        JOIN dw.dim_tempo      t ON f.sk_data_notificacao = t.sk_tempo
        WHERE 1=1 {yf} {mf}
        GROUP BY l.macrorregiao, l.municipio
        ORDER BY confirmados DESC NULLS LAST
    """
    geo_df = run_query(geo_sql)

    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown('<div class="section-title">🏙️ Top 20 Municípios — Casos Confirmados</div>', unsafe_allow_html=True)
        top20 = geo_df.head(20)
        fig_mun = px.bar(
            top20, x="confirmados", y="municipio", orientation="h",
            color="confirmados", color_continuous_scale="Blues",
            hover_data={"obitos": True, "curados": True, "letalidade": True,
                        "confirmados": False, "municipio": False}
        )
        fig_mun.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(autorange="reversed"), coloraxis_showscale=False,
            xaxis_title="Confirmados", yaxis_title="",
            height=520, margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_mun, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">🗺️ Distribuição por Macrorregião</div>', unsafe_allow_html=True)
        macro_agg = (
            geo_df.groupby("macrorregiao", dropna=False)
            .agg(confirmados=("confirmados","sum"), obitos=("obitos","sum"), curados=("curados","sum"))
            .reset_index()
            .sort_values("confirmados", ascending=False)
        )
        fig_macro = px.pie(
            macro_agg, values="confirmados", names="macrorregiao",
            hole=0.5,
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig_macro.update_traces(textposition="outside", textinfo="percent+label")
        fig_macro.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            height=300, margin=dict(l=0, r=20, t=10, b=0)
        )
        st.plotly_chart(fig_macro, use_container_width=True)

        st.markdown('<div class="section-title">📊 Ranking por Macrorregião</div>', unsafe_allow_html=True)
        st.dataframe(
            macro_agg.rename(columns={
                "macrorregiao": "Macrorregião",
                "confirmados": "Confirmados",
                "obitos": "Óbitos",
                "curados": "Curados"
            }).reset_index(drop=True),
            use_container_width=True, hide_index=True
        )

    with st.expander("📋 Tabela completa de municípios"):
        st.dataframe(
            geo_df.rename(columns={
                "macrorregiao": "Macrorregião", "municipio": "Município",
                "notificacoes": "Notificações", "confirmados": "Confirmados",
                "obitos": "Óbitos", "curados": "Curados",
                "internados": "Internados", "letalidade": "Letalidade (%)"
            }),
            use_container_width=True, hide_index=True
        )


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — Perfil do Paciente
# ═════════════════════════════════════════════════════════════════════════════
with tab3:

    base_join = f"""
        FROM dw.fato_notificacao_covid f
        JOIN dw.dim_perfil_paciente p ON f.sk_perfil = p.sk_perfil
        JOIN dw.dim_tempo            t ON f.sk_data_notificacao = t.sk_tempo
        JOIN dw.dim_localidade       l ON f.sk_local            = l.sk_local
        WHERE 1=1 {yf} {mf}
    """

    sexo_df = run_query(f"""
        SELECT p.sexo,
               SUM(f.flag_confirmado)  AS confirmados,
               SUM(f.flag_obito_covid) AS obitos,
               SUM(f.flag_internado)   AS internados
        {base_join}
        GROUP BY p.sexo ORDER BY confirmados DESC
    """)

    idade_df = run_query(f"""
        SELECT p.faixa_etaria,
               SUM(f.flag_confirmado)  AS confirmados,
               SUM(f.flag_obito_covid) AS obitos
        {base_join}
        GROUP BY p.faixa_etaria ORDER BY confirmados DESC NULLS LAST
    """)

    raca_df = run_query(f"""
        SELECT p.raca_cor,
               SUM(f.flag_confirmado)  AS confirmados,
               SUM(f.flag_obito_covid) AS obitos
        {base_join}
        GROUP BY p.raca_cor ORDER BY confirmados DESC NULLS LAST
    """)

    col_l, col_m, col_r = st.columns(3)

    with col_l:
        st.markdown('<div class="section-title">⚤ Por Sexo</div>', unsafe_allow_html=True)
        fig_sexo = px.pie(
            sexo_df, values="confirmados", names="sexo", hole=0.45,
            color_discrete_sequence=["#63b3ed", "#f687b3", "#a3bffa", "#e9d8fd"]
        )
        fig_sexo.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            height=240, margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_sexo, use_container_width=True)
        st.dataframe(
            sexo_df.rename(columns={
                "sexo": "Sexo", "confirmados": "Confirmados",
                "obitos": "Óbitos", "internados": "Internados"
            }), hide_index=True, use_container_width=True
        )

    with col_m:
        st.markdown('<div class="section-title">🎂 Por Faixa Etária</div>', unsafe_allow_html=True)
        fig_idade = px.bar(
            idade_df, x="faixa_etaria", y=["confirmados", "obitos"],
            barmode="group",
            labels={"faixa_etaria": "Faixa Etária", "value": "Total", "variable": ""},
            color_discrete_map={"confirmados": "#63b3ed", "obitos": "#fc8181"}
        )
        fig_idade.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=-40), legend=dict(orientation="h", y=1.08),
            height=360, margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_idade, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">🎭 Por Raça / Cor</div>', unsafe_allow_html=True)
        fig_raca = px.bar(
            raca_df.head(8), x="confirmados", y="raca_cor", orientation="h",
            color="confirmados", color_continuous_scale="Purples"
        )
        fig_raca.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(autorange="reversed"), coloraxis_showscale=False,
            xaxis_title="Confirmados", yaxis_title="",
            height=360, margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_raca, use_container_width=True)

    # Special populations
    st.markdown('<div class="section-title">🔍 Populações Especiais (% dos Confirmados)</div>', unsafe_allow_html=True)
    esp_sql = f"""
        SELECT
            ROUND(SUM(CASE WHEN p.profissional_saude = 'Sim'
                      THEN f.flag_confirmado ELSE 0 END)::numeric
                  / NULLIF(SUM(f.flag_confirmado), 0) * 100, 1) AS pct_prof_saude,
            ROUND(SUM(CASE WHEN p.gestante NOT IN ('Não se aplica','Ignorado')
                           AND p.gestante IS NOT NULL
                      THEN f.flag_confirmado ELSE 0 END)::numeric
                  / NULLIF(SUM(f.flag_confirmado), 0) * 100, 1) AS pct_gestante,
            ROUND(SUM(CASE WHEN p.morador_rua = 'Sim'
                      THEN f.flag_confirmado ELSE 0 END)::numeric
                  / NULLIF(SUM(f.flag_confirmado), 0) * 100, 1) AS pct_morador_rua,
            ROUND(SUM(CASE WHEN p.possui_deficiencia = 'Sim'
                      THEN f.flag_confirmado ELSE 0 END)::numeric
                  / NULLIF(SUM(f.flag_confirmado), 0) * 100, 1) AS pct_deficiencia
        {base_join}
    """
    esp = run_query(esp_sql).iloc[0]
    ec1, ec2, ec3, ec4 = st.columns(4)
    specials = [
        (ec1, "🩺", "Profissional de Saúde", esp.pct_prof_saude,  "metric-info"),
        (ec2, "🤱", "Gestante",              esp.pct_gestante,    "metric-purple"),
        (ec3, "🏚️", "Morador de Rua",        esp.pct_morador_rua, "metric-warning"),
        (ec4, "♿", "Possui Deficiência",    esp.pct_deficiencia, "metric-info"),
    ]
    for col, icon, label, pct, cls in specials:
        val = f"{fmt(pct, 1)}%" if pct is not None else "–"
        col.markdown(f"""
        <div class="metric-card {cls}">
            <div class="metric-icon">{icon}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{val}</div>
            <div class="metric-sub">dos confirmados</div>
        </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — Clínico
# ═════════════════════════════════════════════════════════════════════════════
with tab4:

    clin_join = f"""
        FROM dw.fato_notificacao_covid f
        JOIN dw.dim_tempo            t  ON f.sk_data_notificacao = t.sk_tempo
        JOIN dw.dim_localidade       l  ON f.sk_local            = l.sk_local
        WHERE 1=1 {yf} {mf}
    """

    # Symptoms
    sint_sql = f"""
        SELECT
            SUM(CASE WHEN s.febre           = 'Sim' THEN f.flag_confirmado ELSE 0 END) AS febre,
            SUM(CASE WHEN s.tosse           = 'Sim' THEN f.flag_confirmado ELSE 0 END) AS tosse,
            SUM(CASE WHEN s.dif_respiratoria= 'Sim' THEN f.flag_confirmado ELSE 0 END) AS dif_respiratoria,
            SUM(CASE WHEN s.cefaleia        = 'Sim' THEN f.flag_confirmado ELSE 0 END) AS cefaleia,
            SUM(CASE WHEN s.coriza          = 'Sim' THEN f.flag_confirmado ELSE 0 END) AS coriza,
            SUM(CASE WHEN s.dor_garganta    = 'Sim' THEN f.flag_confirmado ELSE 0 END) AS dor_garganta,
            SUM(CASE WHEN s.diarreia        = 'Sim' THEN f.flag_confirmado ELSE 0 END) AS diarreia
        FROM dw.fato_notificacao_covid f
        JOIN dw.dim_sintomas          s  ON f.sk_sint             = s.sk_sint
        JOIN dw.dim_tempo             t  ON f.sk_data_notificacao = t.sk_tempo
        JOIN dw.dim_localidade        l  ON f.sk_local            = l.sk_local
        WHERE 1=1 {yf} {mf}
    """
    sint = run_query(sint_sql).iloc[0]
    sint_data = pd.DataFrame({
        "Sintoma": ["Febre", "Tosse", "Dif. Respiratória", "Cefaleia", "Coriza", "Dor de Garganta", "Diarreia"],
        "Casos":   [sint.febre, sint.tosse, sint.dif_respiratoria,
                    sint.cefaleia, sint.coriza, sint.dor_garganta, sint.diarreia]
    }).sort_values("Casos", ascending=True)

    # Comorbidities
    como_sql = f"""
        SELECT
            SUM(CASE WHEN c.com_diabetes  = 'Sim' THEN f.flag_confirmado ELSE 0 END) AS diabetes,
            SUM(CASE WHEN c.com_cardio    = 'Sim' THEN f.flag_confirmado ELSE 0 END) AS cardiovascular,
            SUM(CASE WHEN c.com_pulmao    = 'Sim' THEN f.flag_confirmado ELSE 0 END) AS pulmao,
            SUM(CASE WHEN c.com_renal     = 'Sim' THEN f.flag_confirmado ELSE 0 END) AS renal,
            SUM(CASE WHEN c.com_obesidade = 'Sim' THEN f.flag_confirmado ELSE 0 END) AS obesidade,
            SUM(CASE WHEN c.com_tabagismo = 'Sim' THEN f.flag_confirmado ELSE 0 END) AS tabagismo
        FROM dw.fato_notificacao_covid f
        JOIN dw.dim_comorbidade       c  ON f.sk_como             = c.sk_como
        JOIN dw.dim_tempo             t  ON f.sk_data_notificacao = t.sk_tempo
        JOIN dw.dim_localidade        l  ON f.sk_local            = l.sk_local
        WHERE 1=1 {yf} {mf}
    """
    como = run_query(como_sql).iloc[0]
    como_data = pd.DataFrame({
        "Comorbidade": ["Diabetes", "Cardiovascular", "Pulmão", "Renal", "Obesidade", "Tabagismo"],
        "Casos":       [como.diabetes, como.cardiovascular, como.pulmao,
                        como.renal, como.obesidade, como.tabagismo]
    }).sort_values("Casos", ascending=True)

    # Classification + Evolution
    class_sql = f"""
        SELECT
            c.classificacao, c.evolucao,
            SUM(f.flag_confirmado)  AS confirmados,
            SUM(f.flag_obito_covid) AS obitos
        FROM dw.fato_notificacao_covid f
        JOIN dw.dim_classificacao     c  ON f.sk_class            = c.sk_class
        JOIN dw.dim_tempo             t  ON f.sk_data_notificacao = t.sk_tempo
        JOIN dw.dim_localidade        l  ON f.sk_local            = l.sk_local
        WHERE 1=1 {yf} {mf}
        GROUP BY c.classificacao, c.evolucao
        ORDER BY confirmados DESC
    """
    class_df = run_query(class_sql)

    # Tests
    teste_sql = f"""
        SELECT
            SUM(CASE WHEN te.resultado_rt_pcr   = 'Detectável'  THEN f.flag_confirmado ELSE 0 END) AS pcr_pos,
            SUM(CASE WHEN te.resultado_rt_pcr   = 'Não Detectável' THEN f.flag_confirmado ELSE 0 END) AS pcr_neg,
            SUM(CASE WHEN te.resultado_teste_rap= 'Positivo'    THEN f.flag_confirmado ELSE 0 END) AS rap_pos,
            SUM(CASE WHEN te.resultado_teste_rap= 'Negativo'    THEN f.flag_confirmado ELSE 0 END) AS rap_neg,
            SUM(CASE WHEN te.resultado_sorologia= 'Reagente'    THEN f.flag_confirmado ELSE 0 END) AS sorol_pos,
            SUM(CASE WHEN te.resultado_sorol_igg= 'Reagente'    THEN f.flag_confirmado ELSE 0 END) AS igg_pos
        FROM dw.fato_notificacao_covid f
        JOIN dw.dim_teste             te ON f.sk_teste            = te.sk_teste
        JOIN dw.dim_tempo             t  ON f.sk_data_notificacao = t.sk_tempo
        JOIN dw.dim_localidade        l  ON f.sk_local            = l.sk_local
        WHERE 1=1 {yf} {mf}
    """
    teste = run_query(teste_sql).iloc[0]

    # Layout
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-title">🤒 Sintomas Relatados (casos confirmados)</div>', unsafe_allow_html=True)
        fig_sint = px.bar(
            sint_data, x="Casos", y="Sintoma", orientation="h",
            color="Casos", color_continuous_scale="Blues"
        )
        fig_sint.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False, yaxis_title="",
            height=310, margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_sint, use_container_width=True)

        st.markdown('<div class="section-title">⚕️ Comorbidades (casos confirmados)</div>', unsafe_allow_html=True)
        fig_como = px.bar(
            como_data, x="Casos", y="Comorbidade", orientation="h",
            color="Casos", color_continuous_scale="Reds"
        )
        fig_como.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False, yaxis_title="",
            height=290, margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_como, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">📋 Classificação & Evolução dos Casos</div>', unsafe_allow_html=True)
        cc1, cc2 = st.columns(2)

        class_agg = (class_df.groupby("classificacao")["confirmados"].sum()
                     .reset_index().sort_values("confirmados", ascending=False))
        with cc1:
            fig_class = px.pie(
                class_agg, values="confirmados", names="classificacao", hole=0.45,
                color_discrete_sequence=["#63b3ed","#f6ad55","#fc8181","#68d391","#b794f4"]
            )
            fig_class.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                title=dict(text="Classificação", font=dict(size=12, color="#718096")),
                showlegend=True, legend=dict(font=dict(size=9)),
                height=260, margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig_class, use_container_width=True)

        evol_agg = (class_df.groupby("evolucao")["confirmados"].sum()
                    .reset_index().sort_values("confirmados", ascending=False))
        with cc2:
            fig_evol = px.pie(
                evol_agg, values="confirmados", names="evolucao", hole=0.45,
                color_discrete_sequence=["#68d391","#fc8181","#f6ad55","#63b3ed","#b794f4"]
            )
            fig_evol.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                title=dict(text="Evolução", font=dict(size=12, color="#718096")),
                showlegend=True, legend=dict(font=dict(size=9)),
                height=260, margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig_evol, use_container_width=True)

        st.markdown('<div class="section-title">🧪 Resultados de Testes</div>', unsafe_allow_html=True)
        test_data = pd.DataFrame({
            "Teste":  ["RT-PCR+", "RT-PCR−", "Rápido+", "Rápido−", "Sorol.+", "IgG+"],
            "Casos":  [teste.pcr_pos, teste.pcr_neg, teste.rap_pos,
                       teste.rap_neg, teste.sorol_pos, teste.igg_pos],
            "Tipo":   ["RT-PCR","RT-PCR","Rápido","Rápido","Sorologia","Sorologia"]
        })
        fig_teste = px.bar(
            test_data, x="Teste", y="Casos", color="Tipo",
            color_discrete_map={"RT-PCR": "#63b3ed", "Rápido": "#f6ad55", "Sorologia": "#b794f4"},
            barmode="group"
        )
        fig_teste.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.05),
            height=270, margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_teste, use_container_width=True)

        st.markdown('<div class="section-title">⏱️ Tempos Médios (dias)</div>', unsafe_allow_html=True)
        tempo_sql = f"""
            SELECT
                ROUND(AVG(CASE WHEN f.dias_notif_encerramento > 0
                          THEN f.dias_notif_encerramento END)::numeric, 1) AS media_encerramento,
                ROUND(AVG(CASE WHEN f.dias_notif_obito > 0
                          THEN f.dias_notif_obito END)::numeric, 1)        AS media_obito
            {clin_join}
        """
        tempo = run_query(tempo_sql).iloc[0]
        tc1, tc2 = st.columns(2)
        tc1.markdown(f"""
        <div class="metric-card metric-info">
            <div class="metric-icon">📅</div>
            <div class="metric-label">Notif. → Encerramento</div>
            <div class="metric-value">{fmt(tempo.media_encerramento, 1)} d</div>
            <div class="metric-sub">tempo médio</div>
        </div>""", unsafe_allow_html=True)
        tc2.markdown(f"""
        <div class="metric-card metric-danger">
            <div class="metric-icon">💀</div>
            <div class="metric-label">Notif. → Óbito</div>
            <div class="metric-value">{fmt(tempo.media_obito, 1)} d</div>
            <div class="metric-sub">tempo médio</div>
        </div>""", unsafe_allow_html=True)
