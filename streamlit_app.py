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

.section-title {
    color: #e2e8f0; font-size: 14px; font-weight: 600;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(99,179,237,0.15);
    margin-bottom: 14px; margin-top: 4px;
}

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

hr { border-color: rgba(99,179,237,0.1) !important; }
[data-testid="stDataFrame"] { background: rgba(13,21,37,0.5); border-radius: 12px; }
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
        f"?sslmode=require"
    )
    return create_engine(url, pool_pre_ping=True)


@st.cache_data(ttl=3600, show_spinner=False)
def run_query(sql: str) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


# ─── Number Formatter ─────────────────────────────────────────────────────────
def fmt(v, dec: int = 0) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    if dec == 0:
        return f"{int(v):,}".replace(",", ".")
    formatted = f"{float(v):,.{dec}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


# ─── Load Filter Options ──────────────────────────────────────────────────────
with st.spinner("Carregando filtros..."):
    anos_all = run_query(
        "SELECT DISTINCT EXTRACT(YEAR FROM data_notificacao::date)::int AS ano "
        "FROM stg.notificacao_raw "
        "WHERE data_notificacao IS NOT NULL AND data_notificacao ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' "
        "ORDER BY ano"
    )["ano"].tolist()

    munic_all = run_query(
        "SELECT DISTINCT municipio FROM stg.notificacao_raw "
        "WHERE municipio IS NOT NULL AND municipio != '' ORDER BY municipio"
    )["municipio"].tolist()


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

    st.markdown('<div class="sidebar-section">📅 Ano</div>', unsafe_allow_html=True)
    anos_sel = st.multiselect("Ano(s)", options=anos_all, default=anos_all, label_visibility="collapsed")

    st.divider()
    st.markdown(
        "<span style='color:#2d3748;font-size:10px;'>Fonte: SESA-ES · DW COVID-19<br>"
        "Hospedado em: Supabase + Streamlit Cloud</span>",
        unsafe_allow_html=True
    )

if not anos_sel:
    anos_sel = anos_all

# Build year filter
anos_str = ", ".join(str(a) for a in anos_sel)
yf = f"AND EXTRACT(YEAR FROM data_notificacao::date)::int IN ({anos_str})" if anos_sel else ""
date_guard = "data_notificacao IS NOT NULL AND data_notificacao ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'"


# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊  Visão Geral",
    "🗺️  Geografia",
    "👥  Perfil do Paciente",
    "🏥  Clínico",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Visão Geral
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:

    kpi_sql = f"""
        SELECT
            COUNT(*)                                                           AS total_notif,
            COUNT(CASE WHEN classificacao = 'Confirmados' THEN 1 END)          AS total_confirm,
            COUNT(CASE WHEN evolucao ILIKE '%bito%' THEN 1 END)                AS total_obitos,
            COUNT(CASE WHEN evolucao ILIKE 'Cura' THEN 1 END)                  AS total_curados,
            COUNT(CASE WHEN ficou_internado = 'Sim' THEN 1 END)                AS total_internados,
            ROUND(AVG(CASE WHEN classificacao='Confirmados'
                      THEN NULLIF(TRIM(idade_na_notificacao),'')::numeric END),1) AS media_idade,
            ROUND(
                COUNT(CASE WHEN evolucao ILIKE '%bito%' THEN 1 END)::numeric
                / NULLIF(COUNT(CASE WHEN classificacao='Confirmados' THEN 1 END),0) * 100
            , 2) AS taxa_letalidade
        FROM stg.notificacao_raw
        WHERE {date_guard} {yf}
    """
    kpi = run_query(kpi_sql).iloc[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "🔔", "Total Notificações",  fmt(kpi.total_notif),     "",                                           "metric-info"),
        (c2, "✅", "Casos Confirmados",   fmt(kpi.total_confirm),   "",                                           "metric-info"),
        (c3, "💀", "Óbitos COVID",        fmt(kpi.total_obitos),    f"Letalidade: {fmt(kpi.taxa_letalidade,2)}%", "metric-danger"),
        (c4, "💚", "Curados",            fmt(kpi.total_curados),   "",                                           "metric-success"),
        (c5, "🏥", "Internações",         fmt(kpi.total_internados), f"Idade média: {fmt(kpi.media_idade,1)} anos","metric-warning"),
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

    # Time Series
    ts_sql = f"""
        SELECT
            TO_CHAR(data_notificacao::date, 'YYYY-MM') AS ano_mes,
            EXTRACT(YEAR FROM data_notificacao::date)::int AS ano,
            EXTRACT(MONTH FROM data_notificacao::date)::int AS mes,
            COUNT(*)                                               AS notificacoes,
            COUNT(CASE WHEN classificacao='Confirmados' THEN 1 END) AS confirmados,
            COUNT(CASE WHEN evolucao ILIKE '%bito%' THEN 1 END)     AS obitos,
            COUNT(CASE WHEN evolucao ILIKE 'Cura' THEN 1 END)       AS curados
        FROM stg.notificacao_raw
        WHERE {date_guard} {yf}
        GROUP BY 1, 2, 3
        ORDER BY 2, 3
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
        st.markdown('<div class="section-title">📅 Por Classificação</div>', unsafe_allow_html=True)
        cls_sql = f"""
            SELECT classificacao, COUNT(*) AS total
            FROM stg.notificacao_raw
            WHERE {date_guard} {yf} AND classificacao IS NOT NULL AND classificacao != ''
            GROUP BY classificacao ORDER BY total DESC
        """
        cls_df = run_query(cls_sql)
        fig_cls = px.bar(
            cls_df, x="total", y="classificacao", orientation="h",
            color="total", color_continuous_scale="Blues"
        )
        fig_cls.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False,
            xaxis_title="Total", yaxis_title="",
            height=360, margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_cls, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Geografia
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:

    geo_sql = f"""
        SELECT
            municipio,
            COUNT(*)                                                AS notificacoes,
            COUNT(CASE WHEN classificacao='Confirmados' THEN 1 END) AS confirmados,
            COUNT(CASE WHEN evolucao ILIKE '%bito%' THEN 1 END)     AS obitos,
            COUNT(CASE WHEN evolucao ILIKE 'Cura' THEN 1 END)       AS curados,
            COUNT(CASE WHEN ficou_internado='Sim' THEN 1 END)        AS internados,
            ROUND(
                COUNT(CASE WHEN evolucao ILIKE '%bito%' THEN 1 END)::numeric
                / NULLIF(COUNT(CASE WHEN classificacao='Confirmados' THEN 1 END),0)*100
            ,2) AS letalidade
        FROM stg.notificacao_raw
        WHERE {date_guard} {yf}
          AND municipio IS NOT NULL AND municipio != ''
        GROUP BY municipio
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
        st.markdown('<div class="section-title">📊 Ranking por Município</div>', unsafe_allow_html=True)
        st.dataframe(
            geo_df.head(15).rename(columns={
                "municipio": "Município",
                "notificacoes": "Notificações",
                "confirmados": "Confirmados",
                "obitos": "Óbitos",
                "curados": "Curados",
                "internados": "Internados",
                "letalidade": "Letalidade (%)"
            }).reset_index(drop=True),
            use_container_width=True, hide_index=True
        )

    with st.expander("📋 Tabela completa de municípios"):
        st.dataframe(
            geo_df.rename(columns={
                "municipio": "Município",
                "notificacoes": "Notificações",
                "confirmados": "Confirmados",
                "obitos": "Óbitos",
                "curados": "Curados",
                "internados": "Internados",
                "letalidade": "Letalidade (%)"
            }),
            use_container_width=True, hide_index=True
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Perfil do Paciente
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:

    base = f"""
        FROM stg.notificacao_raw
        WHERE {date_guard} {yf}
          AND classificacao = 'Confirmados'
    """

    sexo_df = run_query(f"""
        SELECT sexo,
               COUNT(*) AS confirmados,
               COUNT(CASE WHEN evolucao ILIKE '%bito%' THEN 1 END) AS obitos,
               COUNT(CASE WHEN ficou_internado='Sim' THEN 1 END) AS internados
        {base}
        AND sexo IS NOT NULL AND sexo != ''
        GROUP BY sexo ORDER BY confirmados DESC
    """)

    idade_df = run_query(f"""
        SELECT faixa_etaria,
               COUNT(*) AS confirmados,
               COUNT(CASE WHEN evolucao ILIKE '%bito%' THEN 1 END) AS obitos
        {base}
        AND faixa_etaria IS NOT NULL AND faixa_etaria != ''
        GROUP BY faixa_etaria ORDER BY confirmados DESC NULLS LAST
    """)

    raca_df = run_query(f"""
        SELECT raca_cor,
               COUNT(*) AS confirmados,
               COUNT(CASE WHEN evolucao ILIKE '%bito%' THEN 1 END) AS obitos
        {base}
        AND raca_cor IS NOT NULL AND raca_cor != ''
        GROUP BY raca_cor ORDER BY confirmados DESC NULLS LAST
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

    # Populações especiais
    st.markdown('<div class="section-title">🔍 Populações Especiais (% dos Confirmados)</div>', unsafe_allow_html=True)
    esp_sql = f"""
        SELECT
            ROUND(COUNT(CASE WHEN profissional_saude='Sim' THEN 1 END)::numeric
                  / NULLIF(COUNT(*),0)*100,1) AS pct_prof_saude,
            ROUND(COUNT(CASE WHEN gestante NOT IN ('Não se aplica','Ignorado','','-')
                             AND gestante IS NOT NULL THEN 1 END)::numeric
                  / NULLIF(COUNT(*),0)*100,1) AS pct_gestante,
            ROUND(COUNT(CASE WHEN morador_rua='Sim' THEN 1 END)::numeric
                  / NULLIF(COUNT(*),0)*100,1) AS pct_morador_rua,
            ROUND(COUNT(CASE WHEN possui_deficiencia='Sim' THEN 1 END)::numeric
                  / NULLIF(COUNT(*),0)*100,1) AS pct_deficiencia
        {base}
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


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Clínico
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:

    clin_base = f"""
        FROM stg.notificacao_raw
        WHERE {date_guard} {yf}
          AND classificacao = 'Confirmados'
    """

    sint_sql = f"""
        SELECT
            COUNT(CASE WHEN febre='Sim' THEN 1 END)           AS febre,
            COUNT(CASE WHEN tosse='Sim' THEN 1 END)           AS tosse,
            COUNT(CASE WHEN dif_respiratoria='Sim' THEN 1 END) AS dif_respiratoria,
            COUNT(CASE WHEN cefaleia='Sim' THEN 1 END)         AS cefaleia,
            COUNT(CASE WHEN coriza='Sim' THEN 1 END)           AS coriza,
            COUNT(CASE WHEN dor_garganta='Sim' THEN 1 END)     AS dor_garganta,
            COUNT(CASE WHEN diarreia='Sim' THEN 1 END)         AS diarreia
        {clin_base}
    """
    sint = run_query(sint_sql).iloc[0]
    sint_data = pd.DataFrame({
        "Sintoma": ["Febre", "Tosse", "Dif. Respiratória", "Cefaleia", "Coriza", "Dor de Garganta", "Diarreia"],
        "Casos":   [sint.febre, sint.tosse, sint.dif_respiratoria,
                    sint.cefaleia, sint.coriza, sint.dor_garganta, sint.diarreia]
    }).sort_values("Casos", ascending=True)

    como_sql = f"""
        SELECT
            COUNT(CASE WHEN com_diabetes='Sim' THEN 1 END)  AS diabetes,
            COUNT(CASE WHEN com_cardio='Sim' THEN 1 END)    AS cardiovascular,
            COUNT(CASE WHEN com_pulmao='Sim' THEN 1 END)    AS pulmao,
            COUNT(CASE WHEN com_renal='Sim' THEN 1 END)     AS renal,
            COUNT(CASE WHEN com_obesidade='Sim' THEN 1 END) AS obesidade,
            COUNT(CASE WHEN com_tabagismo='Sim' THEN 1 END) AS tabagismo
        {clin_base}
    """
    como = run_query(como_sql).iloc[0]
    como_data = pd.DataFrame({
        "Comorbidade": ["Diabetes", "Cardiovascular", "Pulmão", "Renal", "Obesidade", "Tabagismo"],
        "Casos":       [como.diabetes, como.cardiovascular, como.pulmao,
                        como.renal, como.obesidade, como.tabagismo]
    }).sort_values("Casos", ascending=True)

    evol_sql = f"""
        SELECT evolucao, COUNT(*) AS total
        FROM stg.notificacao_raw
        WHERE {date_guard} {yf}
          AND classificacao = 'Confirmados'
          AND evolucao IS NOT NULL AND evolucao NOT IN ('', '-', 'Ignorado')
        GROUP BY evolucao ORDER BY total DESC
    """
    evol_df = run_query(evol_sql)

    teste_sql = f"""
        SELECT
            COUNT(CASE WHEN resultado_rt_pcr='Detectável' THEN 1 END)     AS pcr_pos,
            COUNT(CASE WHEN resultado_rt_pcr='Não Detectável' THEN 1 END) AS pcr_neg,
            COUNT(CASE WHEN resultado_teste_rap='Positivo' THEN 1 END)    AS rap_pos,
            COUNT(CASE WHEN resultado_teste_rap='Negativo' THEN 1 END)    AS rap_neg,
            COUNT(CASE WHEN resultado_sorologia='Reagente' THEN 1 END)    AS sorol_pos,
            COUNT(CASE WHEN resultado_sorol_igg='Reagente' THEN 1 END)    AS igg_pos
        {clin_base}
    """
    teste = run_query(teste_sql).iloc[0]

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
        st.markdown('<div class="section-title">📋 Evolução dos Casos Confirmados</div>', unsafe_allow_html=True)
        fig_evol = px.pie(
            evol_df, values="total", names="evolucao", hole=0.45,
            color_discrete_sequence=["#68d391", "#fc8181", "#f6ad55", "#63b3ed", "#b794f4"]
        )
        fig_evol.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True, legend=dict(font=dict(size=11)),
            height=280, margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_evol, use_container_width=True)

        st.markdown('<div class="section-title">🧪 Resultados de Testes</div>', unsafe_allow_html=True)
        test_data = pd.DataFrame({
            "Teste":  ["RT-PCR+", "RT-PCR−", "Rápido+", "Rápido−", "Sorol.+", "IgG+"],
            "Casos":  [teste.pcr_pos, teste.pcr_neg, teste.rap_pos,
                       teste.rap_neg, teste.sorol_pos, teste.igg_pos],
            "Tipo":   ["RT-PCR", "RT-PCR", "Rápido", "Rápido", "Sorologia", "Sorologia"]
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
