# pages/1_📊_Análise_Geral.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Análise Geral e Comparativa")

if 'df' not in st.session_state:
    st.error("Por favor, faça o upload de um arquivo na página principal primeiro.")
    st.stop()

df = st.session_state.df
months = st.session_state.months
grupos = st.session_state.grupos

with st.sidebar:
    st.header("Filtros de Período")
    start_month, end_month = st.select_slider(
        "Selecione o intervalo de meses",
        options=months,
        value=(months[0], months[-1])
    )
start_month_idx = months.index(start_month)
end_month_idx = months.index(end_month)

selected_months = months[start_month_idx:end_month_idx+1]
df_filtered = df[selected_months]

st.header(f"Análise do Período: {start_month} a {end_month}")

# 1. Ranking de Categorias (já existia e é bom, vamos manter)
st.markdown("---")
st.subheader("🏆 Ranking de Categorias por Média no Período")
col_rank1, col_rank2 = st.columns([1,2])
with col_rank1:
    grupo_rank = st.selectbox("Selecione um Grupo para ranquear", options=list(grupos.keys()))
    n_top = st.slider("Top N categorias", 3, 15, 5, key="rank_slider")
    start_idx, end_idx = grupos[grupo_rank]
    df_grupo = df_filtered.iloc[start_idx:end_idx+1]

with col_rank2:
    df_grupo_mean = df_grupo.mean(axis=1).sort_values(ascending=False)
    df_top_n = df_grupo_mean.head(n_top)
    fig_bar_rank = px.bar(df_top_n, x=df_top_n.values, y=df_top_n.index,
                        orientation='h',
                        title=f"Top {n_top} Categorias do Grupo '{grupo_rank}'",
                        labels={'y': 'Categoria', 'x': 'Média no Período'})
    fig_bar_rank.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar_rank, use_container_width=True)


# 2. NOVA ANÁLISE: Volatilidade das Contas
st.markdown("---")
st.subheader("📉 Análise de Volatilidade (Desvio Padrão)")
st.markdown("Esta análise ajuda a identificar as contas com maior variação e imprevisibilidade no período.")

col_vol1, col_vol2 = st.columns([1, 2])
with col_vol1:
    grupo_vol = st.selectbox("Selecione um Grupo para analisar a volatilidade", options=list(grupos.keys()), index=3) # Default 'Despesas Gerais'
    start_idx, end_idx = grupos[grupo_vol]
    df_grupo_vol = df_filtered.iloc[start_idx:end_idx+1]

with col_vol2:
    volatilidade = df_grupo_vol.std(axis=1).sort_values(ascending=False)
    fig_vol = px.bar(volatilidade.head(10),
                     title=f"Top 10 Contas Mais Voláteis em '{grupo_vol}'",
                     labels={'value': 'Desvio Padrão', 'index': 'Categoria'})
    st.plotly_chart(fig_vol, use_container_width=True)

# 3. NOVA ANÁLISE: Mapa de Calor
st.markdown("---")
st.subheader("🔥 Mapa de Calor Financeiro")
st.markdown("Visão geral do desempenho de cada categoria ao longo dos meses. Verde significa valores mais baixos (bom para despesas), vermelho significa valores mais altos.")

grupo_heatmap = st.selectbox("Selecione um Grupo para o Mapa de Calor", options=list(grupos.keys()), index=3) # Default 'Despesas Gerais'
start_idx, end_idx = grupos[grupo_heatmap]
df_grupo_heatmap = df_filtered.iloc[start_idx:end_idx+1].copy()

# Remove linhas com soma 0 para não poluir o gráfico
df_grupo_heatmap = df_grupo_heatmap.loc[(df_grupo_heatmap.sum(axis=1) != 0)]

fig_heatmap = px.imshow(df_grupo_heatmap,
                        labels=dict(x="Mês", y="Categoria", color="Valor"),
                        x=df_grupo_heatmap.columns,
                        y=df_grupo_heatmap.index,
                        color_continuous_scale=px.colors.diverging.RdYlGn_r, # Vermelho(Alto) -> Amarelo -> Verde(Baixo)
                        aspect="auto"
                       )
fig_heatmap.update_layout(title=f"Desempenho das Categorias em '{grupo_heatmap}'")
st.plotly_chart(fig_heatmap, use_container_width=True)