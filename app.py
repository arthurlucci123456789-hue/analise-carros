import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Análise de Dados - Carros", page_icon="🚗", layout="wide", initial_sidebar_state="collapsed")

FAIXAS = ["0-15", "16-30", "31-60", "61-120", "120+"]
PALETA = ["#E4572E", "#29B6C5", "#F3A712", "#6C8EAD", "#A8C686", "#B565A7"]
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = PALETA
px.defaults.color_continuous_scale = "Tealrose"
st.markdown("""<style>
[data-testid="stMetric"]{background:#FFF7F2;border:1px solid #F3D9CC;border-top:5px solid #E4572E;border-radius:12px;padding:14px 16px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
[data-testid="stMetricLabel"],[data-testid="stMetricLabel"] *{color:#5b6b7a !important}
[data-testid="stMetricValue"],[data-testid="stMetricValue"] *{font-size:1.5rem;color:#12202e !important;font-weight:700}
.stTabs [data-baseweb="tab"]{background:#E9F6F8;border-radius:8px 8px 0 0;padding:8px 18px;margin-right:6px}
.stTabs [aria-selected="true"]{background:#E4572E;color:white}
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{display:none}
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div > [data-testid="stMarkdownContainer"] strong){background:#E9F6F8;border:2px solid #29B6C5;border-radius:12px}
h2,h3{border-bottom:2px solid #29B6C5;padding-bottom:4px}
</style>""", unsafe_allow_html=True)


@st.cache_data
def carregar():
    df = pd.read_excel("base_vendas_carros.xlsx")
    df["Desconto_RS"] = df["Preco_Ofertado"] - df["Preco_Vendido"]
    df["Desconto_Pct"] = df["Desconto_RS"] / df["Preco_Ofertado"] * 100
    df["Faixa_Estoque"] = pd.cut(
        df["Dias_Em_Estoque"], [-1, 15, 30, 60, 120, np.inf], labels=FAIXAS
    )
    df["Periodo_Mes"] = np.where(df["Semana_Mes_Venda"] >= 4, "Semanas 4-5 (fim do mês)", "Semanas 1-3")
    df["Mes"] = df["Data_Venda"].dt.to_period("M").dt.to_timestamp()
    return df


def brl(v):
    return "R$ " + f"{v:,.0f}".replace(",", ".")


df = carregar()

st.markdown("<h1 style='margin-bottom:0'>🚗 Análise de Dados <span style='color:#E4572E'>- Carros</span></h1>", unsafe_allow_html=True)
dmin, dmax = df["Data_Venda"].min().date(), df["Data_Venda"].max().date()
with st.container(border=True):
    st.markdown("**🔎 Filtros**")
    c = st.columns([1.3, 1, 1, 1, 1, 1])
    periodo = c[0].date_input("Período", (dmin, dmax), min_value=dmin, max_value=dmax)
    tipo = c[1].multiselect("Tipo de venda", sorted(df["Tipo_Venda"].unique()))
    categoria = c[2].multiselect("Categoria", sorted(df["Categoria"].unique()))
    marca = c[3].multiselect("Marca", sorted(df["Marca"].unique()))
    combustivel = c[4].multiselect("Combustível", sorted(df["Combustivel"].unique()))
    estado = c[5].multiselect("Estado", sorted(df["Estado"].unique()))
f = df
if isinstance(periodo, (tuple, list)) and len(periodo) == 2:
    f = f[(f["Data_Venda"].dt.date >= periodo[0]) & (f["Data_Venda"].dt.date <= periodo[1])]
for col, sel in [("Tipo_Venda", tipo), ("Categoria", categoria), ("Marca", marca),
                 ("Combustivel", combustivel), ("Estado", estado)]:
    if sel:
        f = f[f[col].isin(sel)]

st.caption(f"Exibindo **{len(f):,}** de **{len(df):,}** registros ({dmin:%d/%m/%Y} a {dmax:%d/%m/%Y})".replace(",", "."))

if f.empty:
    st.warning("Nenhum registro com os filtros escolhidos.")
    st.stop()

k = st.columns(6)
k[0].metric("💰 Faturamento", brl(f["Preco_Vendido"].sum()))
k[1].metric("🚘 Vendas", f"{len(f):,}".replace(",", "."))
k[2].metric("🎫 Ticket Médio", brl(f["Preco_Vendido"].mean()))
k[3].metric("🏷️ Desconto Médio", f"{f['Desconto_Pct'].mean():.2f}%")
k[4].metric("💸 Desconto Total", brl(f["Desconto_RS"].sum()))
k[5].metric("📦 Dias em Estoque", f"{f['Dias_Em_Estoque'].mean():.0f}")
st.divider()

tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "⚠️ Problemas", "🔎 Detalhes"])

with tab1:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Evolução do Faturamento (Mensal)")
        m = f.groupby("Mes", as_index=False)["Preco_Vendido"].sum()
        fig = px.area(m, x="Mes", y="Preco_Vendido", labels={"Preco_Vendido": "Faturamento (R$)", "Mes": ""})
        fig.update_traces(line_color="#29B6C5", fillcolor="rgba(41,182,197,0.35)")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Faturamento por Categoria")
        c = f.groupby("Categoria", as_index=False)["Preco_Vendido"].sum()
        fig = px.pie(c, names="Categoria", values="Preco_Vendido", hole=0.55)
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Faturamento por Combustível")
        d = f.groupby("Combustivel", as_index=False)["Preco_Vendido"].sum().sort_values("Preco_Vendido", ascending=False)
        st.plotly_chart(px.bar(d, x="Combustivel", y="Preco_Vendido", labels={"Preco_Vendido": "R$"}), use_container_width=True)
    with c4:
        st.subheader("Ticket Médio por Combustível")
        d = f.groupby("Combustivel", as_index=False)["Preco_Vendido"].mean().sort_values("Preco_Vendido", ascending=False)
        st.plotly_chart(px.bar(d, x="Combustivel", y="Preco_Vendido", labels={"Preco_Vendido": "R$"}), use_container_width=True)

    c5, c6 = st.columns(2)
    with c5:
        st.subheader("Top 10 Marcas por Faturamento")
        d = f.groupby("Marca", as_index=False)["Preco_Vendido"].sum().nlargest(10, "Preco_Vendido").sort_values("Preco_Vendido")
        st.plotly_chart(px.bar(d, x="Preco_Vendido", y="Marca", orientation="h", labels={"Preco_Vendido": "R$"}), use_container_width=True)
    with c6:
        st.subheader("Vendas por Estado")
        d = f.groupby("Estado", as_index=False).size().sort_values("size", ascending=False)
        st.plotly_chart(px.bar(d, x="Estado", y="size", labels={"size": "Vendas"}), use_container_width=True)

with tab2:
    st.subheader("Problema 1: o desconto de fim de mês é o dobro, em qualquer idade de estoque")
    a, b = st.columns(2)
    with a:
        s = f.groupby("Semana_Mes_Venda", as_index=False).agg(desc=("Desconto_Pct", "mean"), n=("ID_Venda", "count"))
        fig = px.bar(s, x="Semana_Mes_Venda", y="desc", text=s["desc"].round(2).astype(str) + "%",
                     labels={"desc": "Desconto médio (%)", "Semana_Mes_Venda": "Semana do mês"},
                     title="Desconto médio por semana do mês")
        st.plotly_chart(fig, use_container_width=True)
    with b:
        g = f.groupby(["Faixa_Estoque", "Periodo_Mes"], observed=True, as_index=False)["Desconto_Pct"].mean()
        fig = px.bar(g, x="Faixa_Estoque", y="Desconto_Pct", color="Periodo_Mes", barmode="group",
                     category_orders={"Faixa_Estoque": FAIXAS},
                     labels={"Desconto_Pct": "Desconto médio (%)", "Faixa_Estoque": "Dias em estoque", "Periodo_Mes": ""},
                     title="Desconto por faixa de estoque: semanas 1-3 vs 4-5")
        st.plotly_chart(fig, use_container_width=True)

    base = f[f["Periodo_Mes"] == "Semanas 1-3"].groupby("Faixa_Estoque", observed=True).apply(
        lambda s: s["Desconto_RS"].sum() / s["Preco_Ofertado"].sum(), include_groups=False)
    fim = f[f["Periodo_Mes"] != "Semanas 1-3"].copy()
    fim["esperado"] = fim["Preco_Ofertado"] * fim["Faixa_Estoque"].map(base).astype(float)
    extra = (fim["Desconto_RS"] - fim["esperado"]).sum()
    share = fim["Desconto_RS"].sum() / f["Desconto_RS"].sum() * 100
    m1, m2, m3 = st.columns(3)
    m1.metric("Desconto EXTRA do fim de mês", brl(extra), help="Desconto real menos o que a idade do estoque explicaria, usando a taxa das semanas 1-3.")
    m2.metric("Parcela do desconto total nas semanas 4-5", f"{share:.1f}%")
    m3.metric("Parcela das vendas nas semanas 4-5", f"{len(fim) / len(f) * 100:.1f}%")

    st.divider()
    st.subheader("Problema 2: só carro usado passa de 30 dias parado")
    a, b = st.columns(2)
    with a:
        g = f.groupby(["Faixa_Estoque", "Tipo_Venda"], observed=True, as_index=False).size()
        fig = px.bar(g, x="Faixa_Estoque", y="size", color="Tipo_Venda", barmode="group",
                     category_orders={"Faixa_Estoque": FAIXAS}, labels={"size": "Vendas", "Faixa_Estoque": "Dias em estoque"},
                     title="Vendas por faixa de estoque")
        st.plotly_chart(fig, use_container_width=True)
    with b:
        g = f.groupby("Tipo_Venda", as_index=False)["Dias_Em_Estoque"].mean()
        fig = px.bar(g, x="Tipo_Venda", y="Dias_Em_Estoque", text=g["Dias_Em_Estoque"].round(0).astype(int),
                     labels={"Dias_Em_Estoque": "Dias médios"}, title="Dias médios em estoque")
        st.plotly_chart(fig, use_container_width=True)
    u = f[f["Tipo_Venda"] == "Usado"]
    if len(u):
        n120 = (f["Dias_Em_Estoque"] > 120).sum()
        p120 = f.loc[f["Dias_Em_Estoque"] > 120, "Desconto_RS"].sum() / f["Desconto_RS"].sum() * 100
        z1, z2 = st.columns(2)
        z1.metric("Vendas com mais de 120 dias em estoque", f"{n120:,}".replace(",", "."), f"{n120 / len(f) * 100:.1f}% das vendas", delta_color="off")
        z2.metric("Desconto absorvido por esse estoque parado", f"{p120:.1f}%")

with tab3:
    st.subheader("Carros que mais ficam parados em estoque")
    t = (f.groupby(["Marca", "Modelo", "Categoria"], as_index=False)
         .agg(dias_estoque_medio=("Dias_Em_Estoque", "mean"), qtd_vendas=("ID_Venda", "count"),
              desconto_medio_pct=("Desconto_Pct", "mean"))
         .sort_values("dias_estoque_medio", ascending=False).round(2))
    st.dataframe(t, use_container_width=True, hide_index=True)
    st.subheader("Vendas e faturamento por estado e categoria")
    t2 = (f.groupby(["Estado", "Categoria"], as_index=False)
          .agg(qtd_vendas=("ID_Venda", "count"), faturamento=("Preco_Vendido", "sum"))
          .sort_values("faturamento", ascending=False))
    st.dataframe(t2, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Baixar dados filtrados (CSV)", f.to_csv(index=False).encode("utf-8"), "vendas_filtradas.csv", "text/csv")



