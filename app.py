import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from optimizer import PortfolioOptimizer

# Configuração da página
st.set_page_config(
    page_title="Otimizador de Portfólio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para o botão de ajuda
st.markdown("""
<style>
    .help-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state para controle da ajuda
if 'show_help' not in st.session_state:
    st.session_state.show_help = False

# Função para alternar ajuda
def toggle_help():
    st.session_state.show_help = not st.session_state.show_help

# Título
st.title("📊 Otimizador de Portfólio")
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("*Baseado na metodologia de Markowitz*")
with col2:
    if st.button("📖 Ajuda", use_container_width=True, help="Clique para ver a documentação"):
        toggle_help()

# Mostrar documentação se solicitado
if st.session_state.show_help:
    with st.container():
        st.markdown("---")
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚀 Início Rápido", "📊 Preparar Dados", "⚙️ Configurações", "📈 Resultados", "❓ FAQ"])
        
        with tab1:
            st.markdown("""
            ## 🚀 Guia de Início Rápido
            
            ### 3 Passos Simples:
            
            1. **📁 Carregue seus dados**
               - Use o upload ou escolha um exemplo
               - Formato: Excel com retornos diários
            
            2. **🎯 Configure a otimização**
               - Selecione os ativos (mínimo 2)
               - Escolha o objetivo (Sharpe, Sortino, etc.)
               - Ajuste os limites de peso
            
            3. **🚀 Otimize!**
               - Clique no botão "OTIMIZAR PORTFÓLIO"
               - Analise os resultados
               - Exporte ou ajuste conforme necessário
            
            ### 💡 Dica Rápida:
            Para primeira vez, use os dados de exemplo e objetivo "Maximizar Sharpe Ratio"!
            """)
        
        with tab2:
            st.markdown("""
            ## 📊 Como Preparar seus Dados
            
            ### Formato da Planilha Excel:
            
            | Data | Taxa Ref (opcional) | Ativo 1 | Ativo 2 | ... |
            |------|---------------------|---------|---------|-----|
            | 01/01/2023 | 0.0005 | 0.0120 | -0.0050 | ... |
            | 02/01/2023 | 0.0005 | -0.0030 | 0.0100 | ... |
            
            ### ⚠️ Importante:
            - **Coluna A**: Datas (formato data)
            - **Coluna B**: Taxa referência - CDI, IBOV, etc. (opcional)
            - **Outras colunas**: Retornos diários em decimal
            - **Exemplo**: 1.2% = 0.012 (não use 1.2)
            
            ### 📁 Dados de Exemplo Disponíveis:
            - **Ações Brasileiras**: IBOV, blue chips
            - **Fundos Imobiliários**: FIIs principais
            - **ETFs**: Renda fixa e variável
            - **Criptomoedas**: Bitcoin, Ethereum, etc.
            
            ### 🔍 Dica de Qualidade:
            - Mínimo 1 ano de dados (252 dias úteis)
            - Evite períodos com muitos feriados
            - Verifique dados faltantes ou zerados
            """)
        
        with tab3:
            st.markdown("""
            ## ⚙️ Configurações Detalhadas
            
            ### 🎯 Objetivos de Otimização:
            
            | Objetivo | Quando Usar | Característica |
            |----------|-------------|----------------|
            | **Sharpe Ratio** | Carteiras tradicionais | Retorno/Risco total |
            | **Sortino Ratio** | Aversão a perdas | Penaliza só volatilidade negativa |
            | **Minimizar Risco** | Perfil conservador | Menor volatilidade possível |
            | **Maximizar Inclinação** | Tendência de alta | Crescimento mais consistente |
            | **Inclinação/[(1-R²)×Vol]** | Crescimento estável | Combina tendência e previsibilidade |
            
            ### 📊 Limites de Peso:
            
            - **Peso Mínimo Global (0-20%)**
              - 0% = Permite excluir ativos
              - 5% = Garante diversificação mínima
              - 10%+ = Força distribuição equilibrada
            
            - **Peso Máximo Global (5-100%)**
              - 20% = Máxima diversificação
              - 30% = Balanceado (recomendado)
              - 50%+ = Permite concentração
            
            ### 🎯 Restrições Individuais:
            
            Use para casos específicos:
            - **Travar posição**: Min = Max (ex: 15% = 15%)
            - **Core holding**: Min alto (ex: Min 20%)
            - **Limitar risco**: Max baixo (ex: Max 5%)
            
            ### 🔄 Posições Short/Hedge:
            
            - Permite vender ativos a descoberto
            - Útil para hedge ou arbitragem
            - Pesos negativos até -100%
            - Não entram na soma de 100%
            """)
        
        with tab4:
            st.markdown("""
            ## 📈 Interpretando os Resultados
            
            ### 📊 Métricas Principais:
            
            | Métrica | O que significa | Valores de Referência |
            |---------|-----------------|----------------------|
            | **Retorno Total** | Ganho acumulado | Depende do período |
            | **Retorno Anual** | Ganho anualizado | CDI + 2-5% = bom |
            | **Volatilidade** | Risco anualizado | <10% = baixo, >20% = alto |
            | **Sharpe Ratio** | Retorno/Risco | >1 = bom, >2 = ótimo |
            | **Sortino Ratio** | Retorno/Risco negativo | Geralmente > Sharpe |
            
            ### 📉 Métricas de Risco:
            
            - **R²**: Previsibilidade (0-1)
              - >0.8 = Alta linearidade
              - <0.5 = Baixa previsibilidade
            
            - **VaR 95%**: Perda máxima diária
              - -2% = Em 95% dos dias, não perde mais que 2%
              
            - **Downside Deviation**: Volatilidade das perdas
              - Sempre ≤ Volatilidade total
            
            ### 📊 Composição Final:
            
            - Pesos otimizados somam 100%
            - Ativos com peso <0.1% são omitidos
            - Gráfico de pizza mostra distribuição visual
            
            ### 📈 Gráfico de Performance:
            
            - **Linha Azul**: Portfólio otimizado
            - **Linha Laranja**: Taxa de referência (se houver)
            - **Linha Verde**: Excesso de retorno
            
            ### 📅 Tabela Mensal:
            
            - Verde = Retorno positivo
            - Vermelho = Retorno negativo
            - Total Anual = Performance do ano
            """)
        
        with tab5:
            st.markdown("""
            ## ❓ Perguntas Frequentes
            
            ### Por que meu ativo favorito ficou com 0%?
            O otimizador busca a melhor combinação matemática. Ativos podem receber 0% se:
            - Têm baixo retorno ajustado ao risco
            - São muito correlacionados com outros
            - Têm volatilidade muito alta
            
            **Solução**: Use restrições individuais para garantir alocação mínima.
            
            ### Sharpe ou Sortino - qual usar?
            - **Sharpe**: Tradicional, penaliza toda volatilidade
            - **Sortino**: Moderno, penaliza só volatilidade negativa
            
            **Recomendação**: Sortino é geralmente melhor para investidores reais.
            
            ### Quantos ativos incluir?
            - **Mínimo**: 2 ativos (obrigatório)
            - **Ideal**: 5-15 ativos
            - **Máximo prático**: 20-30 ativos
            
            ### Como usar posições short?
            1. Selecione ativos para otimização normal
            2. Ative "Posições Short/Hedge"
            3. Escolha ativos para vender
            4. Defina pesos negativos
            
            ### A otimização é garantida?
            **NÃO!** A otimização é baseada em dados históricos. Use como guia, considerando:
            - Mudanças de cenário
            - Custos de transação
            - Liquidez dos ativos
            - Seu perfil de risco
            
            ### Como exportar os resultados?
            - Screenshot da tela
            - Copie os valores da tabela
            - Print do gráfico (botão de câmera no Plotly)
            
            ### Posso confiar 100% nos resultados?
            Não. Esta é uma ferramenta de apoio à decisão. Sempre:
            - Revise os resultados criticamente
            - Considere fatores não quantitativos
            - Consulte um profissional se necessário
            
            ### 📞 Suporte:
            - GitHub: [github.com/psrs2000/Portfolio_Optimizer](https://github.com/psrs2000/Portfolio_Optimizer)
            - Documentação completa no README.md
            """)
        
        # Botão para fechar ajuda
        st.markdown("---")
        if st.button("❌ Fechar Ajuda", use_container_width=False):
            toggle_help()
            st.rerun()

# Configuração dos dados de exemplo no GitHub
# IMPORTANTE: Substitua pelos seus valores reais!
GITHUB_USER = "psrs2000"  # ← Coloque seu usuário aqui
GITHUB_REPO = "Portfolio_Optimizer"     # ← Coloque o nome do seu repositório aqui
GITHUB_BRANCH = "main"

# Arquivos de exemplo disponíveis
SAMPLE_DATA = {
    "🏢 Ações Brasileiras": {
        "filename": "acoes_brasileiras.xlsx",
        "description": "Principais ações do Ibovespa"
    },
    "🏠 Fundos Imobiliários": {
        "filename": "fundos_imobiliarios.xlsx",
        "description": "FIIs negociados na B3"
    },
    "💰 Fundos de Investimento": {
        "filename": "fundos_de_investimento.xlsx",
        "description": "Exemplo com fundos de investimento cadastrados na CVM"
    },
    "🌍 ETFs Nacionais": {
        "filename": "etfs_nacionais.xlsx",
        "description": "ETFs de mercados Nacionais"
    },
    "🪙 Criptomoedas": {
        "filename": "criptomoedas.xlsx",
        "description": "Bitcoin, Ethereum e principais"
    }
}

def load_from_github(filename):
    """
    Carrega arquivo Excel diretamente do GitHub
    """
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/sample_data/{filename}"
    
    try:
        df = pd.read_excel(url)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo do GitHub: {str(e)}")
        st.info("Verifique se o arquivo existe e o repositório é público")
        return None

def create_monthly_returns_table(returns_data, weights, dates=None, risk_free_returns=None):
    """
    Cria tabela de retornos mensais do portfólio otimizado
    """
    # Calcular retornos diários do portfólio
    portfolio_returns_daily = np.dot(returns_data.values, weights)
    
    # Criar DataFrame com retornos diários
    portfolio_df = pd.DataFrame({
        'returns': portfolio_returns_daily
    }, index=range(len(portfolio_returns_daily)))
    
    # Adicionar taxa livre se disponível
    if risk_free_returns is not None:
        portfolio_df['risk_free'] = risk_free_returns.values
    
    # Usar datas reais se disponíveis, senão simular
    if dates is not None:
        portfolio_df.index = dates
    else:
        # Simular datas (assumindo dados diários consecutivos)
        start_date = pd.Timestamp('2020-01-01')
        dates = pd.date_range(start=start_date, periods=len(portfolio_returns_daily), freq='D')
        portfolio_df.index = dates
    
    # Calcular retornos mensais
    # Converter retornos diários para retornos compostos mensais
    portfolio_df['returns_factor'] = 1 + portfolio_df['returns']
    monthly_returns = portfolio_df['returns_factor'].resample('M').prod() - 1
    
    # Calcular retornos mensais da taxa livre se disponível
    if risk_free_returns is not None:
        portfolio_df['risk_free_factor'] = 1 + portfolio_df['risk_free']
        monthly_risk_free = portfolio_df['risk_free_factor'].resample('M').prod() - 1
    
    # Criar tabela pivotada (anos x meses)
    monthly_df = pd.DataFrame({
        'Year': monthly_returns.index.year,
        'Month': monthly_returns.index.month,
        'Return': monthly_returns.values
    })
    
    # Pivotar para ter anos nas linhas e meses nas colunas
    pivot_table = monthly_df.pivot(index='Year', columns='Month', values='Return')
    
    # Renomear colunas para nomes dos meses
    month_names = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }
    pivot_table.columns = [month_names.get(col, f'M{col}') for col in pivot_table.columns]
    
    # Calcular total anual (soma dos retornos mensais compostos)
    yearly_returns = []
    for year in pivot_table.index:
        year_data = pivot_table.loc[year].dropna()
        if len(year_data) > 0:
            # Retorno anual composto
            annual_return = (1 + year_data).prod() - 1
            yearly_returns.append(annual_return)
        else:
            yearly_returns.append(np.nan)
    
    pivot_table['Total Anual'] = yearly_returns
    
    # Se temos taxa livre, criar tabela comparativa
    comparison_table = None
    if risk_free_returns is not None:
        # Criar tabela similar para taxa livre
        rf_monthly_df = pd.DataFrame({
            'Year': monthly_risk_free.index.year,
            'Month': monthly_risk_free.index.month,
            'Return': monthly_risk_free.values
        })
        
        rf_pivot = rf_monthly_df.pivot(index='Year', columns='Month', values='Return')
        rf_pivot.columns = [month_names.get(col, f'M{col}') for col in rf_pivot.columns]
        
        # Calcular total anual da taxa livre
        rf_yearly = []
        for year in rf_pivot.index:
            year_data = rf_pivot.loc[year].dropna()
            if len(year_data) > 0:
                annual_return = (1 + year_data).prod() - 1
                rf_yearly.append(annual_return)
            else:
                rf_yearly.append(np.nan)
        
        rf_pivot['Total Anual'] = rf_yearly
        
        # Criar tabela de comparação (excesso de retorno)
        comparison_table = pivot_table - rf_pivot
    
    return pivot_table, comparison_table

# Sidebar para carregamento de dados
with st.sidebar:
    st.header("📁 Carregar Dados")
    
    # Tabs para organizar opções
    tab_exemplo, tab_upload = st.tabs(["📊 Exemplos", "📤 Upload"])
    
    with tab_exemplo:
        st.markdown("### Dados de Exemplo")
        
        # Verificar se GitHub está configurado
        if GITHUB_USER == "SEU_USUARIO_GITHUB":
            st.warning(
                "⚠️ Configure o GitHub primeiro!\n\n"
                "1. Edite o arquivo app.py\n"
                "2. Substitua GITHUB_USER e GITHUB_REPO\n"
                "3. Faça upload dos arquivos Excel em /sample_data/"
            )
        else:
            st.info("Clique para carregar:")
            
            # Botões para cada dataset
            for name, info in SAMPLE_DATA.items():
                if st.button(
                    f"{name}",
                    use_container_width=True,
                    help=info['description']
                ):
                    with st.spinner(f"Carregando {name}..."):
                        df_temp = load_from_github(info['filename'])
                        if df_temp is not None:
                            st.session_state['df'] = df_temp
                            st.session_state['data_source'] = name
                            st.success("✅ Dados carregados!")
                            st.rerun()
    
    with tab_upload:
        st.markdown("### Upload Manual")
        uploaded_file = st.file_uploader(
            "Escolha sua planilha Excel",
            type=['xlsx', 'xls'],
            help="Planilha com dados históricos dos ativos"
        )
        
        if uploaded_file is not None:
            try:
                df_temp = pd.read_excel(uploaded_file)
                st.session_state['df'] = df_temp
                st.session_state['data_source'] = "Upload Manual"
                st.success("✅ Arquivo carregado!")
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {str(e)}")
    
    # Link para Google Drive
    st.markdown("---")
    st.markdown(
        "📂 **Baixar mais dados:**\n\n"
        "[Pasta no Google Drive]"
        "(https://drive.google.com/drive/folders/1t8EcZZqGqPIH3pzZ-DdBytrr3Rb1TuwV?usp=sharing)"
    )

# Verificar se há dados carregados
df = st.session_state.get('df', None)

# Área principal
if df is not None:
    try:
        # Mostrar origem dos dados
        data_source = st.session_state.get('data_source', 'Desconhecida')
        st.success(f"✅ Dados carregados: **{data_source}**")
        
        # Mostrar preview dos dados
        with st.expander("📋 Ver dados carregados"):
            st.write(f"Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
            st.dataframe(df.head(10))
        
        # Verificar se há taxa de referência na coluna B
        has_risk_free = False
        risk_free_column_name = None
        if len(df.columns) > 2 and isinstance(df.columns[1], str):
            col_name = df.columns[1].lower()
            if any(term in col_name for term in ['taxa', 'livre', 'risco', 'ibov', 'ref', 'cdi', 'selic']):
                has_risk_free = True
                risk_free_column_name = df.columns[1]
                st.info(f"📊 Taxa de referência detectada: '{risk_free_column_name}'")
        
        # Seleção de ativos
        st.header("🛒 Seleção de Ativos")
        
        # Identificar colunas de ativos
        if isinstance(df.columns[0], str) and 'data' in df.columns[0].lower():
            if has_risk_free:
                asset_columns = df.columns[2:].tolist()  # Ativos começam na coluna C
            else:
                asset_columns = df.columns[1:].tolist()  # Ativos começam na coluna B
        else:
            asset_columns = df.columns.tolist()
        
        st.markdown("Selecione os ativos que deseja incluir na otimização:")
        
        # Opção com multiselect - NENHUM selecionado por padrão
        selected_assets = st.multiselect(
            "🔍 Digite para buscar ou clique para selecionar:",
            options=asset_columns,
            default=[],
            help="Você pode digitar parte do nome para filtrar os ativos",
            placeholder="Escolha os ativos..."
        )
        
        # Verificar se pelo menos 2 ativos foram selecionados
        if len(selected_assets) < 2:
            st.warning("⚠️ Selecione pelo menos 2 ativos para otimização")
        else:
            st.success(f"✅ {len(selected_assets)} ativos selecionados de {len(asset_columns)} disponíveis")
            
        # Mostrar resumo dos selecionados (opcional)
        if st.checkbox("📋 Ver lista de ativos selecionados", value=False):
            for i, asset in enumerate(selected_assets, 1):
                st.text(f"{i}. {asset}")
        
        # NOVA SEÇÃO: Short Selling / Hedge
        st.header("🔄 Posições Short / Hedge (Opcional)")
        
        use_short = st.checkbox("Habilitar posições short/hedge", help="Permite incluir ativos com pesos negativos (venda a descoberto)")
        
        short_assets = []
        short_weights = {}
        
        if use_short:
            # Identificar ativos não selecionados
            available_for_short = [asset for asset in asset_columns if asset not in selected_assets]
            
            if len(available_for_short) > 0:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    short_assets = st.multiselect(
                        "Selecione ativos para posição short:",
                        options=available_for_short,
                        help="Estes ativos terão pesos negativos (venda a descoberto)"
                    )
                
                if len(short_assets) > 0:
                    st.markdown("**Defina os pesos negativos:**")
                    
                    # Criar sliders para cada ativo short
                    cols = st.columns(min(3, len(short_assets)))
                    for idx, asset in enumerate(short_assets):
                        with cols[idx % 3]:
                            weight = st.slider(
                                f"{asset}",
                                min_value=-100,
                                max_value=0,
                                value=-10,
                                step=1,
                                help=f"Peso negativo para {asset} (%). -100% = venda total do ativo"
                            )
                            short_weights[asset] = weight / 100
                    
                    # Mostrar resumo
                    total_short = sum(short_weights.values())
                    st.info(f"📊 Total short: {total_short*100:.1f}% (não entra na soma dos 100% do portfólio)")
            else:
                st.warning("⚠️ Selecione menos ativos na otimização para liberar opções de short")
        
        # Configurações de otimização
        st.header("⚙️ Configurações da Otimização")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Lista de objetivos com condicional
            objectives_list = [
                "Maximizar Sharpe Ratio", 
                "Maximizar Sortino Ratio",
                "Minimizar Risco", 
                "Maximizar Inclinação", 
                "Maximizar Inclinação/[(1-R²)×Vol]"
            ]
            
            # Adicionar objetivo de excesso apenas se taxa livre foi detectada
            if has_risk_free:
                objectives_list.append("Maximizar Qualidade da Linearidade")
                objectives_list.append("Maximizar Linearidade do Excesso")
                
            objective = st.selectbox(
                "🎯 Objetivo da Otimização",
                objectives_list,
                help="Escolha o que você quer otimizar. NOVO: Sortino Ratio considera apenas volatilidade negativa!"
            )
        
        with col2:
            min_weight = st.slider(
                "📊 Peso mínimo por ativo (%)",
                min_value=0,
                max_value=20,
                value=0,
                step=1,
                help="Limite mínimo para cada ativo no portfólio (0% = sem mínimo)"
            ) / 100
        
        with col3:
            max_weight = st.slider(
                "📊 Peso máximo por ativo (%)",
                min_value=5,
                max_value=100,
                value=30,
                step=1,
                help="Limite máximo para cada ativo no portfólio"
            ) / 100
        
        with col4:
            # Inicializar otimizador para verificar taxa livre
            temp_optimizer = PortfolioOptimizer(df, [])
            
            if has_risk_free and hasattr(temp_optimizer, 'risk_free_rate_total'):
                # Mostrar taxa livre detectada como informação
                detected_rate = temp_optimizer.risk_free_rate_total
                st.metric(
                    "🏛️ Taxa de referência",
                    f"{detected_rate:.2%}",
                    help="Taxa detectada automaticamente da coluna B (acumulada do período)"
                )
                used_risk_free_rate = detected_rate
            else:
                # Campo manual se não detectou
                used_risk_free_rate = st.number_input(
                    "🏛️ Taxa de referência (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=0.1,
                    help="Taxa de referência ACUMULADA do período"
                ) / 100
                
        # NOVA SEÇÃO: Restrições Individuais (APÓS definir min_weight e max_weight)
        use_individual_constraints = False
        individual_constraints = {}
        
        if len(selected_assets) >= 2:
            st.header("🚫 Restrições Individuais por Ativo (Opcional)")
            
            use_individual_constraints = st.checkbox(
                "Definir limites específicos para alguns ativos",
                help="Permite definir pesos mínimos e máximos diferentes para ativos específicos"
            )
            
            if use_individual_constraints:
                # Selecionar quais ativos terão restrições individuais
                constrained_assets = st.multiselect(
                    "Selecione os ativos com restrições específicas:",
                    options=selected_assets,
                    help="Escolha apenas os ativos que precisam de limites diferentes dos globais"
                )
                
                if len(constrained_assets) > 0:
                    st.markdown("**Configure os limites para cada ativo selecionado:**")
                    
                    # Criar colunas para organizar melhor
                    num_cols = min(2, len(constrained_assets))
                    if num_cols > 0:
                        cols = st.columns(num_cols)
                    
                    for idx, asset in enumerate(constrained_assets):
                        with cols[idx % num_cols] if num_cols > 0 else st.container():
                            st.markdown(f"**{asset}**")
                            
                            # Valores padrão baseados nos limites globais
                            default_min = min_weight * 100
                            default_max = max_weight * 100
                            
                            # Criar duas colunas para min e max lado a lado
                            col_min, col_max = st.columns(2)
                            
                            with col_min:
                                asset_min = st.number_input(
                                    "Mín %",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=default_min,
                                    step=0.5,
                                    key=f"min_{asset}",
                                    help=f"Peso mínimo para {asset}"
                                )
                            
                            with col_max:
                                asset_max = st.number_input(
                                    "Máx %",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=default_max,
                                    step=0.5,
                                    key=f"max_{asset}",
                                    help=f"Peso máximo para {asset}"
                                )
                            
                            # Validar que min <= max
                            if asset_min > asset_max:
                                st.error(f"⚠️ Mínimo deve ser ≤ Máximo")
                                asset_min = asset_max
                            
                            # Guardar apenas os ativos com restrições
                            individual_constraints[asset] = {
                                'min': asset_min / 100,
                                'max': asset_max / 100
                            }
                            
                            # Mostrar range visualmente
                            if asset_min == asset_max:
                                st.info(f"🔒 Travado em {asset_min:.1f}%")
                            else:
                                st.caption(f"📊 Range: {asset_min:.1f}% - {asset_max:.1f}%")
                            st.markdown("---")
                    
                    # Validar se a soma dos mínimos não excede 100%
                    # Considerar TODOS os ativos: com restrições individuais + sem restrições (usando min global)
                    total_min = 0
                    for asset in selected_assets:
                        if asset in individual_constraints:
                            total_min += individual_constraints[asset]['min']
                        else:
                            total_min += min_weight
                    
                    if total_min > 1.0:
                        st.error(f"❌ Soma dos mínimos ({total_min*100:.1f}%) excede 100%!")
                        st.caption("Isso inclui os ativos sem restrições individuais usando o mínimo global")
                    else:
                        st.success(f"✅ Soma total dos mínimos: {total_min*100:.1f}%")
                else:
                    st.info("👆 Selecione os ativos que precisam de limites específicos")
# Botão de otimização
        if st.button("🚀 OTIMIZAR PORTFÓLIO", type="primary", use_container_width=True):
            
            # Verificar novamente se há ativos suficientes
            if len(selected_assets) < 2:
                st.error("❌ Selecione pelo menos 2 ativos para otimização")
            else:
                with st.spinner("🔄 Otimizando... Aguarde alguns segundos"):
                    try:
                        # Preparar lista completa de ativos (selected + short)
                        all_assets = selected_assets.copy()
                        if use_short and len(short_assets) > 0:
                            all_assets.extend(short_assets)
                        
                        # Inicializar otimizador com TODOS os ativos
                        optimizer = PortfolioOptimizer(df, all_assets)
                        
                        # Usar taxa livre detectada ou manual
                        if has_risk_free and hasattr(optimizer, 'risk_free_rate_total'):
                            final_risk_free_rate = optimizer.risk_free_rate_total
                        else:
                            final_risk_free_rate = used_risk_free_rate
                        
                        # Definir tipo de objetivo
                        if objective == "Maximizar Sharpe Ratio":
                            obj_type = 'sharpe'
                        elif objective == "Maximizar Sortino Ratio":
                            obj_type = 'sortino'
                        elif objective == "Minimizar Risco":
                            obj_type = 'volatility'
                        elif objective == "Maximizar Inclinação":
                            obj_type = 'slope'
                        elif objective == "Maximizar Inclinação/[(1-R²)×Vol]":
                            obj_type = 'hc10'
                        elif objective == "Maximizar Qualidade da Linearidade":
                            obj_type = 'quality_linear'
                        elif objective == "Maximizar Linearidade do Excesso":
                            obj_type = 'excess_hc10'    
                        
                        # Preparar restrições individuais se habilitadas
                        constraints_to_use = individual_constraints if use_individual_constraints else None
                        
                        # Executar otimização
                        if use_short and len(short_assets) > 0:
                            # Otimização com shorts
                            result = optimizer.optimize_portfolio_with_shorts(
                                selected_assets=selected_assets,
                                short_assets=short_assets,
                                short_weights=short_weights,
                                objective_type=obj_type,
                                max_weight=max_weight,
                                min_weight=min_weight,
                                risk_free_rate=final_risk_free_rate,
                                individual_constraints=constraints_to_use
                            )
                        else:
                            # Otimização normal
                            result = optimizer.optimize_portfolio(
                                objective_type=obj_type,
                                target_return=None,
                                max_weight=max_weight,
                                min_weight=min_weight,
                                risk_free_rate=final_risk_free_rate,
                                individual_constraints=constraints_to_use
                            )
                        
                        if result['success']:
                            st.success("🎉 Otimização concluída com sucesso!")
                            
                            # Métricas principais
                            metrics = result['metrics']
                            
                            # Primeira linha de métricas
                            col1, col2, col3, col4, col5 = st.columns(5)
                            
                            with col1:
                                st.metric(
                                    "📈 Retorno Total", 
                                    f"{metrics['gv_final']:.2%}",
                                    help="Retorno acumulado total"
                                )
                            
                            with col2:
                                st.metric(
                                    "📅 Ganho Anual", 
                                    f"{metrics['annual_return']:.2%}",
                                    help="Retorno anualizado do portfólio"
                                )
                            
                            with col3:
                                st.metric(
                                    "📊 Volatilidade", 
                                    f"{metrics['volatility']:.2%}",
                                    help="Risco anualizado (DESVPAD.P × √252)"
                                )
                            
                            with col4:
                                st.metric(
                                    "⚡ Sharpe Ratio", 
                                    f"{metrics['sharpe_ratio']:.3f}",
                                    help=f" (Retorno Total - Taxa de referência) / Volatilidade\nTaxa de referência usada: {metrics['risk_free_rate']:.2%}"
                                )
                            
                            with col5:
                                st.metric(
                                    "🔥 Sortino Ratio", 
                                    f"{metrics['sortino_ratio']:.3f}",
                                    help="Similar ao Sharpe, mas considera apenas volatilidade negativa (downside risk)"
                                )
                            
                            
                            # Segunda linha - Métricas de risco e taxa de referência
                            st.subheader("📊 Métricas de Risco e Taxa de referência")
                            col1, col2, col3, col4, col5, col6 = st.columns(6)
                            
                            with col1:
                                st.metric(
                                    "📈 R²", 
                                    f"{metrics['r_squared']:.3f}",
                                    help="Qualidade da linearidade da tendência"
                                )
                            
                            with col2:
                                st.metric(
                                    "⚠️ VaR 95% (Diário)", 
                                    f"{metrics['var_95_daily']:.2%}",
                                    help="Perda máxima esperada em 95% dos dias"
                                )
                            
                            with col3:
                                st.metric(
                                    "📉 CVaR 95% (Diário)", 
                                    f"{metrics['cvar_95_daily']:.2%}",
                                    help="Perda média nos 5% piores dias"
                                )
                            
                            with col4:
                                st.metric(
                                    "📉 Downside Deviation", 
                                    f"{metrics['downside_deviation']:.2%}",
                                    help="Volatilidade anualizada apenas dos retornos negativos"
                                )
                            
                            with col5:
                                st.metric(
                                    "🏛️ Taxa de referência", 
                                    f"{metrics['risk_free_rate']:.2%}",
                                    help="Taxa de referência acumulada do período usada no cálculo"
                                )
                            
                            with col6:
                                st.metric(
                                    "📈 Retorno do Excesso", 
                                    f"{metrics['excess_return']:.2%}",
                                    help="Retorno Total - Taxa de referência (numerador do Sharpe Ratio)"
                                )
                            
                            # NOVO: Se otimizou excesso, mostrar métricas específicas
                            if objective == "Maximizar Linearidade do Excesso" and metrics.get('excess_r_squared') is not None:
                                st.subheader("🆕 Métricas de Linearidade do Excesso")
                                col1, col2, col3, col4 = st.columns(4)  # Era 3, agora é 4
                                
                                # Calcular métricas do excesso
                                if hasattr(optimizer, 'risk_free_returns') and optimizer.risk_free_returns is not None:
                                    excess_returns_daily = metrics['portfolio_returns_daily'] - optimizer.risk_free_returns.values
                                    excess_vol = np.std(excess_returns_daily, ddof=0) * np.sqrt(252)
                                    
                                    # NOVO: VaR 95% do Excesso
                                    mean_excess_daily = np.mean(excess_returns_daily)
                                    std_excess_daily = np.std(excess_returns_daily, ddof=0)
                                    var_95_excess_daily = mean_excess_daily - 1.65 * std_excess_daily
                                    
                                    # NOVO: Retorno anual do excesso
                                    excess_total = metrics['gv_final'] - metrics['risk_free_rate']
                                    annual_excess_return = (1 + excess_total) ** (252 / len(excess_returns_daily)) - 1
                                else:
                                    excess_vol = 0
                                    var_95_excess_daily = 0
                                    annual_excess_return = 0
                                
                                with col1:
                                    st.metric(
                                        "📊 R² do Excesso", 
                                        f"{metrics['excess_r_squared']:.3f}",
                                        help="Qualidade da linearidade do excesso (quanto mais próximo de 1, mais linear)"
                                    )
                                
                                with col2:
                                    st.metric(
                                        "📊 Volatilidade do Excesso", 
                                        f"{excess_vol:.2%}",
                                        help="Volatilidade anualizada do excesso de retorno (desvio padrão do excesso × √252)"
                                    )
                                
                                with col3:
                                    st.metric(
                                        "⚠️ VaR 95% (Diário) do Excesso", 
                                        f"{var_95_excess_daily:.2%}",
                                        help="VaR 95% calculado sobre os retornos do excesso diário"
                                    )
                                
                                with col4:
                                    st.metric(
                                        "📅 Retorno Anual do Excesso", 
                                        f"{annual_excess_return:.2%}",
                                        help="Retorno anualizado do excesso de retorno"
                                    )
                            
                            # Explicação sobre VaR e Taxa Livre de Risco
                            st.info(
                                "💡 **VaR vs CVaR**: \n"
                                f"• VaR 95% = {metrics['var_95_daily']:.2%}: Em 95% dos dias você não perderá mais que {abs(metrics['var_95_daily']):.2%}\n"
                                f"• CVaR 95% = {metrics['cvar_95_daily']:.2%}: Nos 5% piores dias, perderá em média {abs(metrics['cvar_95_daily']):.2%}\n\n"
                                "🏛️ **Taxa Livre de Risco**: Representa o retorno de um investimento sem risco (ex: CDI, Tesouro). "
                                "O Sharpe Ratio mede quanto retorno extra você obtém por unidade de risco adicional.\n\n"
                                "🔥 **Sortino Ratio**: Similar ao Sharpe, mas considera apenas a volatilidade dos retornos negativos. "
                                "É mais apropriado pois investidores se preocupam mais com perdas do que com ganhos voláteis."
                            )
                            
                            # Composição do portfólio
                            st.header("📊 Composição do Portfólio Otimizado")
                            
                            portfolio_df = optimizer.get_portfolio_summary(result['weights'])
                            
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.subheader("📋 Tabela de Pesos")
                                # Formatar tabela
                                portfolio_display = portfolio_df.copy()
                                portfolio_display['Peso (%)'] = portfolio_display['Peso (%)'].apply(lambda x: f"{x:.2f}%")
                                st.dataframe(portfolio_display, use_container_width=True, hide_index=True)
                                
                                # Total para verificação
                                total_weight = portfolio_df['Peso (%)'].sum()
                                st.info(f"✅ Total alocado: {total_weight:.1f}%")
                            
                            with col2:
                                st.subheader("🥧 Distribuição Visual")
                                if len(portfolio_df) > 0:
                                    fig = px.pie(
                                        portfolio_df,
                                        values='Peso (%)',
                                        names='Ativo',
                                        hole=0.4,
                                        color_discrete_sequence=px.colors.qualitative.Set3
                                    )
                                    fig.update_traces(
                                        textposition='inside', 
                                        textinfo='percent+label',
                                        textfont_size=12
                                    )
                                    fig.update_layout(
                                        showlegend=True,
                                        height=400
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning("Nenhum ativo selecionado na otimização")
                            
                            # Gráfico de evolução do portfólio COM TAXA LIVRE
                            st.header("📈 Evolução do Portfólio Otimizado")
                            
                            # Criar DataFrame para o gráfico
                            periods = range(1, len(metrics['portfolio_cumulative']) + 1)
                            
                            # Criar figura com múltiplas linhas
                            fig_line = go.Figure()
                            
                            # Linha do portfólio
                            fig_line.add_trace(go.Scatter(
                                x=list(periods),
                                y=metrics['portfolio_cumulative'] * 100,
                                mode='lines',
                                name='Portfólio Otimizado',
                                line=dict(color='#1f77b4', width=2.5)
                            ))
                            
                            # Se temos taxa livre, adicionar linha
                            if hasattr(optimizer, 'risk_free_cumulative') and optimizer.risk_free_cumulative is not None:
                                fig_line.add_trace(go.Scatter(
                                    x=list(periods),
                                    y=optimizer.risk_free_cumulative * 100,
                                    mode='lines',
                                    name='Taxa de Referência',
                                    line=dict(color='#ff7f0e', width=2, dash='dash')
                                ))
                                
                                # Adicionar linha de excesso de retorno
                                excess_cumulative = metrics['portfolio_cumulative'] - optimizer.risk_free_cumulative.values
                                fig_line.add_trace(go.Scatter(
                                    x=list(periods),
                                    y=excess_cumulative * 100,
                                    mode='lines',
                                    name='Excesso de Retorno',
                                    line=dict(color='#2ca02c', width=2, dash='dot')
                                ))
                            
                            # Personalizar layout
                            fig_line.update_layout(
                                title='Evolução do Retorno Acumulado',
                                xaxis_title='Dias de Negociação',
                                yaxis_title='Retorno Acumulado (%)',
                                hovermode='x unified',
                                height=500,
                                showlegend=True,
                                legend=dict(
                                    yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01
                                ),
                                xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)'),
                                yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
                            )
                            
                            # Adicionar anotação com retorno final
                            fig_line.add_annotation(
                                x=len(periods),
                                y=metrics['gv_final'] * 100,
                                text=f"Retorno Final: {metrics['gv_final']:.2%}",
                                showarrow=True,
                                arrowhead=2,
                                arrowsize=1,
                                arrowwidth=2,
                                arrowcolor="#1f77b4",
                                ax=-50,
                                ay=-30,
                                bordercolor="#1f77b4",
                                borderwidth=2,
                                borderpad=4,
                                bgcolor="white",
                                opacity=0.9
                            )
                            
                            st.plotly_chart(fig_line, use_container_width=True)
                            
                            # NOVA SEÇÃO: Tabela de Retornos Mensais
                            st.header("📅 Performance Mensal do Portfólio")
                            
                            try:
                                # Criar tabela de retornos mensais
                                dates = getattr(optimizer, 'dates', None)
                                risk_free_returns = getattr(optimizer, 'risk_free_returns', None)
                                
                                monthly_table, excess_table = create_monthly_returns_table(
                                    optimizer.returns_data, 
                                    result['weights'],
                                    dates,
                                    risk_free_returns
                                )
                                
                                # Função para aplicar cores baseadas no valor
                                def color_negative_red(val):
                                    """
                                    Aplica cor vermelha para valores negativos e verde para positivos
                                    """
                                    if val == "-" or pd.isna(val):
                                        return 'color: gray'
                                    
                                    # Extrair valor numérico da string formatada
                                    try:
                                        if isinstance(val, str) and '%' in val:
                                            numeric_val = float(val.replace('%', '')) / 100
                                        else:
                                            numeric_val = float(val)
                                        
                                        if numeric_val < 0:
                                            return 'color: red; font-weight: bold'
                                        elif numeric_val > 0:
                                            return 'color: green; font-weight: bold'
                                        else:
                                            return 'color: black'
                                    except:
                                        return 'color: black'
                                
                                # Mostrar tabela principal
                                st.subheader("📊 Retornos Mensais do Portfólio")
                                monthly_display = monthly_table.copy()
                                
                                # Aplicar formatação de porcentagem
                                for col in monthly_display.columns:
                                    monthly_display[col] = monthly_display[col].apply(
                                        lambda x: f"{x:.2%}" if pd.notna(x) else "-"
                                    )
                                
                                # Aplicar estilo com cores
                                styled_table = monthly_display.style.applymap(color_negative_red)
                                
                                # Exibir tabela com cores
                                st.dataframe(
                                    styled_table,
                                    use_container_width=True,
                                    height=300
                                )
                                
                                # Se temos tabela de excesso, mostrar também
                                if excess_table is not None:
                                    st.subheader("📊 Excesso de Retorno Mensal (Portfólio - Taxa de Referência)")
                                    
                                    excess_display = excess_table.copy()
                                    
                                    # Aplicar formatação
                                    for col in excess_display.columns:
                                        excess_display[col] = excess_display[col].apply(
                                            lambda x: f"{x:.2%}" if pd.notna(x) else "-"
                                        )
                                    
                                    # Aplicar estilo
                                    styled_excess = excess_display.style.applymap(color_negative_red)
                                    
                                    # Exibir
                                    st.dataframe(
                                        styled_excess,
                                        use_container_width=True,
                                        height=300
                                    )
                                
                            except Exception as e:
                                st.warning(f"⚠️ Não foi possível gerar a tabela mensal: {str(e)}")
                                st.info("💡 Isso pode acontecer se os dados não tiverem informações de data ou forem insuficientes.")
                            
                         
                        else:
                            st.error(f"❌ {result['message']}")
                    
                    except Exception as e:
                        st.error(f"❌ Erro durante a otimização: {str(e)}")
                        st.info("💡 Verifique se os dados estão no formato correto (primeira coluna = datas, demais = retornos)")

    except Exception as e:
        st.error(f"❌ Erro ao ler arquivo: {e}")

else:
    # Mensagem quando não há arquivo
    st.info("👈 Faça upload de uma planilha Excel para começar")
    
    # Verificar se GitHub está configurado
    if GITHUB_USER == "SEU_USUARIO_GITHUB":
        st.warning(
            "⚠️ **Para habilitar os dados de exemplo:**\n\n"
            "1. **Configure o GitHub** no código:\n"
            "   - Substitua `GITHUB_USER` pelo seu usuário\n"
            "   - Substitua `GITHUB_REPO` pelo nome do seu repositório\n\n"
            "2. **Crie a pasta** `sample_data/` no seu repositório\n\n"
            "3. **Faça upload** dos arquivos Excel de exemplo\n\n"
            "4. **Pronto!** Os botões de exemplo funcionarão automaticamente"
        )
    
    # Link para download dos dados
    st.markdown("### 📂 Dados Disponíveis")
    st.markdown(
        "**Baixe planilhas com dados históricos de ativos:**\n\n"
        "🔗 [Acessar pasta no Google Drive](https://drive.google.com/drive/folders/1t8EcZZqGqPIH3pzZ-DdBytrr3Rb1TuwV?usp=sharing)"
    )
    st.markdown("---")
    
    # Instruções
    st.markdown("""
    ### 📝 Como usar:
    
    1. **Baixe uma planilha** do link acima ou use sua própria
    
    2. **Estruture sua planilha** assim:
       - Primeira coluna: Datas
       - Segunda coluna: Coluna de referência (CDI, IBOV, etc)
       - Outras colunas: Retornos de cada ativo (base 0)
    
    3. **Faça upload** do arquivo Excel
    
    4. **Configure** os parâmetros de otimização
    
    5. **Clique em otimizar** e receba os pesos ideais!
    
    ### 💡 Dica:
    Se a célula B1 tiver no nome "Taxa Livre", "CDI", "Selic", "Ref" ou "IBOV" o sistema detecta e calcula o retorno dessa coluna!
    """)

# Rodapé
st.markdown("---")
st.markdown("*Desenvolvido com Streamlit - Otimização Portfólio v2.0* 🚀")
