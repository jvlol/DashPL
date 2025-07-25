import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression
import openai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide")
st.title("💡 Análise Inteligente e Recomendações")
st.markdown("Use esta página para encontrar problemas automaticamente ou para fazer uma análise profunda de uma categoria específica.")

if 'df' not in st.session_state:
    st.error("Por favor, faça o upload de um arquivo na página principal primeiro.")
    st.stop()

# --- FUNÇÃO PARA CHAMAR A API DA OPENAI ---
@st.cache_data
def get_ia_tips(categoria, tipo_problema, grupo, valor_delta_str):
    try:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        prompt_text = (
            f"Você é um consultor financeiro especialista em restaurantes e varejo. "
            f"A categoria '{categoria}' do grupo '{grupo}' de uma empresa apresentou o seguinte diagnóstico: '{tipo_problema}', "
            f"com uma variação de {valor_delta_str}.\n\n"
            f"Com base em conhecimento geral de mercado e boas práticas de gestão, forneça 3 dicas práticas, curtas e acionáveis "
            f"para o gestor resolver ou mitigar este problema específico. Não use introduções ou despedidas.\n"
            f"Formate a resposta usando markdown com bullet points (usando '-')."
        )
        response = openai.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt_text}], temperature=0.5, max_tokens=250)
        return response.choices[0].message.content
    except Exception:
        fallback_tips = {'Pior Tendência (Crescimento)': "- **Investigue a Causa Raiz.**\n- **Crie um Plano de Ação.**", 'Pior Desempenho Recente': "- **Análise Comparativa.**\n- **Lições Aprendidas.**", 'Maior Volatilidade': "- **Crie um Orçamento Base.**\n- **Provisão de Contigência.**"}
        return f"**Sugestões Padrão (Falha na conexão com IA):**\n" + fallback_tips.get(tipo_problema, "Analise a categoria em detalhes.")

# --- CARREGAMENTO DE DADOS E FILTROS ---
df, months, grupos = st.session_state.df, st.session_state.months, st.session_state.grupos
with st.sidebar:
    st.header("Filtros de Análise")
    grupo_analise = st.selectbox("1. Selecione um Grupo", list(grupos.keys()), index=3)
    start_month, end_month = st.select_slider("2. Selecione o Período", options=months, value=(months[0], months[-1]), key="analise_periodo_slider")

start_idx, end_idx = months.index(start_month), months.index(end_month)
df_periodo = df.iloc[:, start_idx:end_idx + 1]
start_g, end_g = grupos[grupo_analise]
df_grupo = df_periodo.iloc[start_g:min(end_g + 1, len(df))]

if df_grupo.shape[1] < 2:
    st.warning("Selecione um período com pelo menos 2 meses para realizar as análises.")
    st.stop()

# --- CÁLCULO DAS MÉTRICAS DE ANÁLISE ---
# Este bloco agora é executado antes do if/else para que ambos os modos o utilizem
def calcular_tendencia(row):
    # CORREÇÃO CRÍTICA: Lida com células vazias (NaN) que quebram o modelo
    valid_data = row.dropna()
    if len(valid_data) < 2: return 0.0
    X = np.arange(len(valid_data)).reshape(-1, 1)
    y = valid_data.values
    model = LinearRegression().fit(X, y)
    return model.coef_[0]

analise_df = pd.DataFrame(index=df_grupo.index)
analise_df['ultimo_valor'] = df_grupo.iloc[:, -1]
analise_df['media_historica'] = df_grupo.iloc[:, :-1].mean(axis=1)
analise_df['desempenho_recente'] = analise_df['ultimo_valor'] - analise_df['media_historica']
analise_df['volatilidade'] = df_grupo.std(axis=1)
analise_df['tendencia_linear'] = df_grupo.apply(calcular_tendencia, axis=1)
analise_df.fillna(0, inplace=True) # Garante que não haja NaNs nos resultados

# --- SELETOR DE MODO ---
st.markdown("---")
modo_analise = st.radio("**Escolha o modo de análise:**", ["Diagnóstico Automático", "Análise Individual"], horizontal=True, label_visibility="collapsed")

# ================================
# MODO 1: DIAGNÓSTICO AUTOMÁTICO
# ================================
if modo_analise == "Diagnóstico Automático":
    st.header(f"Diagnóstico Automático: {grupo_analise}")
    criterio = st.selectbox("Identificar pontos de atenção por:", ["Pior Tendência (Crescimento)", "Pior Desempenho Recente", "Maior Volatilidade"])
    top_n = st.slider("Analisar o Top N", 3, 10, 5)

    mapa = {"Pior Tendência (Crescimento)": "tendencia_linear", "Pior Desempenho Recente": "desempenho_recente", "Maior Volatilidade": "volatilidade"}
    categorias_problema = analise_df.sort_values(by=mapa[criterio], ascending=False).head(top_n)

    for categoria, dados in categorias_problema.iterrows():
        with st.container(border=True):
            col_diag, col_chart = st.columns([0.6, 0.4])
            with col_diag:
                st.subheader(f"🚨 {categoria}")
                if criterio == "Pior Tendência (Crescimento)": valor_delta_str = f"{dados['tendencia_linear']:.2f}/mês"
                elif criterio == "Pior Desempenho Recente": valor_delta_str = f"{dados['desempenho_recente']:,.2f}"
                else: valor_delta_str = f"{dados['volatilidade']:,.2f}"
                st.metric(label=criterio, value=valor_delta_str, delta_color="off")
                with st.expander("**Obter Sugestões com IA**"):
                    if st.button(f"Gerar dicas de IA para {categoria}", key=f"btn_auto_{categoria}"):
                        with st.spinner("Consultando especialista virtual..."):
                            st.markdown(get_ia_tips(categoria, criterio, grupo_analise, valor_delta_str))
            with col_chart:
                 st.markdown("##### Tendência e Projeção")
                 st.line_chart(df_grupo.loc[categoria])

# ================================
# MODO 2: ANÁLISE INDIVIDUAL
# ================================
else:
    st.header(f"Análise Individual: {grupo_analise}")
    categoria_selecionada = st.selectbox("Selecione uma Categoria para um mergulho profundo:", options=df_grupo.index)

    if categoria_selecionada:
        st.markdown("---")
        # Pega os dados já calculados para a categoria
        dados_cat = analise_df.loc[categoria_selecionada]
        with st.container(border=True):
            col_info, col_chart = st.columns([0.6, 0.4])
            with col_info:
                st.subheader(f"🔍 Análise Profunda de: {categoria_selecionada}")
                kpi1, kpi2 = st.columns(2)
                kpi1.metric("Último Valor", f"{dados_cat['ultimo_valor']:,.2f}")
                kpi2.metric("Média Histórica", f"{dados_cat['media_historica']:,.2f}")
                st.metric("Variação (Último vs. Média)", f"{dados_cat['desempenho_recente']:,.2f}", delta_color="inverse")
                st.metric("Tendência (Crescimento/Mês)", f"{dados_cat['tendencia_linear']:.2f}", help="Positivo significa crescimento.")
                with st.expander("**Obter Sugestões com IA**"):
                    problema = st.radio("Focar dicas em:", ["Tendência de Crescimento", "Volatilidade/Picos"], horizontal=True, key=f"dica_{categoria_selecionada}")
                    if st.button("Gerar dicas de IA", key=f"btn_indiv_{categoria_selecionada}"):
                        with st.spinner("Consultando especialista virtual..."):
                            valor = f"{dados_cat['tendencia_linear']:.2f}/mês" if problema == "Tendência de Crescimento" else f"{dados_cat['volatilidade']:.2f} de desv. padrão"
                            st.markdown(get_ia_tips(categoria_selecionada, problema, grupo_analise, valor))
            with col_chart:
                st.subheader("📈 Gráfico de Evolução")
                st.line_chart(df_grupo.loc[categoria_selecionada])