import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from optimizer import PortfolioOptimizer
import gdown
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Otimizador de Portfólio",
    page_icon="📊",
    layout="wide"
)

# Título
st.title("📊 Otimizador de Portfólio")
st.markdown("*Baseado na metodologia de Markowitz*")

# Classe para carregar arquivos do Google Drive
class GoogleDriveLoader:
    """
    Classe para carregar arquivos diretamente do Google Drive
    """
    
    # Lista de arquivos conhecidos (atualize com os IDs reais dos seus arquivos)
    KNOWN_FILES = {
        "Ações Brasileiras (2020-2024)": {
            "id": "SEU_FILE_ID_AQUI_1",
            "description": "Dados históricos de ações do Ibovespa"
        },
        "Fundos Imobiliários (FIIs)": {
            "id": "SEU_FILE_ID_AQUI_2",
            "description": "Dados de FIIs brasileiros"
        },
        "Criptomoedas Principais": {
            "id": "SEU_FILE_ID_AQUI_3",
            "description": "Bitcoin, Ethereum e principais criptos"
        },
        "Portfólio com Taxa Livre (CDI)": {
            "id": "SEU_FILE_ID_AQUI_4",
            "description": "Exemplo com CDI na coluna B"
        },
        "ETFs Internacionais": {
            "id": "SEU_FILE_ID_AQUI_5",
            "description": "ETFs de mercados globais"
        }
    }
    
    @staticmethod
    def load_from_gdrive_id(file_id):
        """
        Carrega arquivo do Google Drive usando ID
        """
        try:
            # Primeiro tenta carregar direto com pandas
            url = f"https://drive.google.com/uc?id={file_id}"
            df = pd.read_excel(url)
            return df
        except:
            # Se falhar, baixa o arquivo primeiro
            try:
                temp_file = "temp_portfolio_data.xlsx"
                gdown.download(url, temp_file, quiet=True)
                df = pd.read_excel(temp_file)
                # Remove arquivo temporário
                Path(temp_file).unlink(missing_ok=True)
                return df
            except Exception as e:
                st.error(f"Erro ao carregar arquivo: {str(e)}")
                return None
    
    @staticmethod
    def load_from_url(url):
        """
        Carrega arquivo a partir de URL do Google Drive
        """
        try:
            # Extrai ID do arquivo da URL
            if "/file/d/" in url:
                file_id = url.split("/file/d/")[1].split("/")[0]
            elif "id=" in url:
                file_id = url.split("id=")[1].split("&")[0]
            else:
                st.error("URL do Google Drive inválido")
                return None
            
            return GoogleDriveLoader.load_from_gdrive_id(file_id)
            
        except Exception as e:
            st.error(f"Erro ao processar URL: {str(e)}")
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

# Interface principal - Sistema de carregamento de dados
st.sidebar.header("📁 Carregar Dados")

# Opções de carregamento
load_option = st.sidebar.radio(
    "Como deseja carregar os dados?",
    ["📂 Arquivos Disponíveis", "📤 Upload Local", "🔗 URL do Google Drive"],
    help="Escolha como carregar seus dados"
)

df = None
data_loaded = False

if load_option == "📂 Arquivos Disponíveis":
    st.sidebar.markdown("### Conjuntos de Dados Prontos")
    
    # Lista de arquivos disponíveis
    selected_dataset = st.sidebar.selectbox(
        "Escolha um conjunto de dados:",
        options=list(GoogleDriveLoader.KNOWN_FILES.keys()),
        format_func=lambda x: f"{x}"
    )
    
    if selected_dataset:
        file_info = GoogleDriveLoader.KNOWN_FILES[selected_dataset]
        st.sidebar.info(f"📄 {file_info['description']}")
        
        if st.sidebar.button("📥 Carregar Dados", type="primary", use_container_width=True):
            with st.spinner(f"Carregando {selected_dataset}..."):
                # Aqui você precisa adicionar os IDs reais dos arquivos
                # Por enquanto, vou mostrar uma mensagem
                st.sidebar.warning(
                    "⚠️ Para funcionar, você precisa:\n"
                    "1. Obter os IDs dos arquivos no Google Drive\n"
                    "2. Atualizar o dicionário KNOWN_FILES com os IDs reais"
                )
                st.sidebar.markdown(
                    "**Como obter o ID do arquivo:**\n"
                    "1. Abra o arquivo no Google Drive\n"
                    "2. O ID está na URL: drive.google.com/file/d/**ID_AQUI**/view"
                )

elif load_option == "📤 Upload Local":
    uploaded_file = st.sidebar.file_uploader(
        "Escolha sua planilha Excel",
        type=['xlsx', 'xls'],
        help="Planilha com dados históricos dos ativos"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            data_loaded = True
            st.sidebar.success("✅ Arquivo carregado!")
        except Exception as e:
            st.sidebar.error(f"❌ Erro: {str(e)}")

elif load_option == "🔗 URL do Google Drive":
    st.sidebar.markdown("### Carregar de URL")
    
    url_input = st.sidebar.text_input(
        "Cole o link do Google Drive:",
        placeholder="https://drive.google.com/file/d/.../view",
        help="Link de compartilhamento do arquivo"
    )
    
    example_url = "https://drive.google.com/file/d/1ABC123/view?usp=sharing"
    st.sidebar.caption(f"Exemplo: {example_url}")
    
    if st.sidebar.button("🔗 Carregar do URL", type="secondary"):
        if url_input:
            with st.spinner("Carregando arquivo..."):
                df = GoogleDriveLoader.load_from_url(url_input)
                if df is not None:
                    data_loaded = True
                    st.sidebar.success("✅ Arquivo carregado!")

# Link para pasta do Google Drive
st.sidebar.markdown("---")
st.sidebar.markdown(
    "📂 [Ver pasta com todos os arquivos]"
    "(https://drive.google.com/drive/folders/1t8EcZZqGqPIH3pzZ-DdBytrr3Rb1TuwV?usp=sharing)"
)

# Área principal
if df is not None:
    try:
        st.success("✅ Dados carregados com sucesso!")
        
        # Mostrar preview dos dados
        with st.expander("📋 Ver dados carregados"):
            st.write(f"Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
            st.dataframe(df.head(10))
        
        # Verificar se há taxa livre de risco na coluna B
        has_risk_free = False
        risk_free_column_name = None
        if len(df.columns) > 2 and isinstance(df.columns[1], str):
            col_name = df.columns[1].lower()
            if any(term in col_name for term in ['taxa', 'livre', 'risco', 'risk', 'free', 'cdi', 'selic']):
                has_risk_free = True
                risk_free_column_name = df.columns[1]
                st.info(f"📊 Taxa livre de risco detectada: '{risk_free_column_name}'")
        
        # Seleção de ativos
        st.header("🎯 Seleção de Ativos")
        
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
        
        # Configurações de otimização
        st.header("⚙️ Configurações da Otimização")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Lista de objetivos com condicional
            objectives_list = [
                "Maximizar Sharpe Ratio", 
                "Minimizar Risco", 
                "Maximizar Inclinação", 
                "Maximizar Inclinação/[(1-R²)×Vol]"
            ]
            
            # Adicionar objetivo de excesso apenas se taxa livre foi detectada
            if has_risk_free:
                objectives_list.append("🆕 Maximizar Linearidade do Excesso")
                
            objective = st.selectbox(
                "🎯 Objetivo da Otimização",
                objectives_list,
                help="Escolha o que você quer otimizar. NOVO: Linearidade do Excesso disponível quando taxa livre é detectada!"
            )
        
        with col2:
            max_weight = st.slider(
                "📊 Peso máximo por ativo (%)",
                min_value=5,
                max_value=100,
                value=30,
                step=1,
                help="Limite máximo para cada ativo no portfólio"
            ) / 100
        
        with col3:
            # Inicializar otimizador para verificar taxa livre
            temp_optimizer = PortfolioOptimizer(df, [])
            
            if has_risk_free and hasattr(temp_optimizer, 'risk_free_rate_total'):
                # Mostrar taxa livre detectada como informação
                detected_rate = temp_optimizer.risk_free_rate_total
                st.metric(
                    "🏛️ Taxa Livre de Risco",
                    f"{detected_rate:.2%}",
                    help="Taxa detectada automaticamente da coluna B (acumulada do período)"
                )
                used_risk_free_rate = detected_rate
            else:
                # Campo manual se não detectou
                used_risk_free_rate = st.number_input(
                    "🏛️ Taxa Livre de Risco (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=0.1,
                    help="Taxa livre de risco ACUMULADA do período"
                ) / 100

        # Botão de otimização
        if st.button("🚀 OTIMIZAR PORTFÓLIO", type="primary", use_container_width=True):
            
            # Verificar novamente se há ativos suficientes
            if len(selected_assets) < 2:
                st.error("❌ Selecione pelo menos 2 ativos para otimização")
            else:
                with st.spinner("🔄 Otimizando... Aguarde alguns segundos"):
                    try:
                        # Inicializar otimizador com ativos selecionados
                        optimizer = PortfolioOptimizer(df, selected_assets)
                        
                        # Usar taxa livre detectada ou manual
                        if has_risk_free and hasattr(optimizer, 'risk_free_rate_total'):
                            final_risk_free_rate = optimizer.risk_free_rate_total
                        else:
                            final_risk_free_rate = used_risk_free_rate
                        
                        # Definir tipo de objetivo
                        if objective == "Maximizar Sharpe Ratio":
                            obj_type = 'sharpe'
                        elif objective == "Minimizar Risco":
                            obj_type = 'volatility'
                        elif objective == "Maximizar Inclinação":
                            obj_type = 'slope'
                        elif objective == "Maximizar Inclinação/[(1-R²)×Vol]":
                            obj_type = 'hc10'
                        elif objective == "🆕 Maximizar Linearidade do Excesso":
                            obj_type = 'excess_hc10'
                        
                        # Executar otimização
                        result = optimizer.optimize_portfolio(
                            objective_type=obj_type,
                            target_return=None,
                            max_weight=max_weight,
                            risk_free_rate=final_risk_free_rate
                        )
                        
                        if result['success']:
                            st.success("🎉 Otimização concluída com sucesso!")
                            
                            # Métricas principais
                            metrics = result['metrics']
                            
                            # Primeira linha de métricas
                            col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
                            
                            with col1:
                                st.metric(
                                    "📈 Retorno Total", 
                                    f"{metrics['gv_final']:.2%}",
                                    help="GV final - Retorno acumulado total"
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
                                    help="HC5 - Risco anualizado (DESVPAD.P × √252)"
                                )
                            
                            with col4:
                                st.metric(
                                    "⚡ Sharpe Ratio", 
                                    f"{metrics['sharpe_ratio']:.3f}",
                                    help=f"HC8 - (Retorno Total - Taxa Livre de Risco) / Volatilidade\nTaxa Livre de Risco usada: {metrics['risk_free_rate']:.2%}"
                                )
                            
                            with col5:
                                st.metric(
                                    "📈 Inclinação (×1000)", 
                                    f"{metrics['slope']*1000:.3f}",
                                    help="Inclinação da regressão linear do retorno acumulado (multiplicada por 1000 para melhor visualização)"
                                )
                            
                            with col6:
                                st.metric(
                                    "🎯 Inclinação/[(1-R²)×Vol]", 
                                    f"{metrics['hc10']:.4f}",
                                    help="Inclinação / [Volatilidade × (1-R²)]"
                                )
                            
                            with col7:
                                st.metric(
                                    "📈 R²", 
                                    f"{metrics['r_squared']:.3f}",
                                    help="Qualidade da linearidade da tendência"
                                )
                            
                            # Segunda linha - Métricas de risco e taxa livre de risco
                            st.subheader("📊 Métricas de Risco e Taxa Livre de Risco")
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric(
                                    "⚠️ VaR 95% (Diário)", 
                                    f"{metrics['var_95_daily']:.2%}",
                                    help="Perda máxima esperada em 95% dos dias"
                                )
                            
                            with col2:
                                st.metric(
                                    "🚨 VaR 99% (Diário)", 
                                    f"{metrics['var_99_daily']:.2%}",
                                    help="Perda máxima esperada em 99% dos dias"
                                )
                            
                            with col3:
                                st.metric(
                                    "🏛️ Taxa Livre de Risco", 
                                    f"{metrics['risk_free_rate']:.2%}",
                                    help="Taxa livre de risco acumulada do período usada no cálculo"
                                )
                            
                            with col4:
                                st.metric(
                                    "📈 Retorno em Excesso", 
                                    f"{metrics['excess_return']:.2%}",
                                    help="Retorno Total - Taxa Livre de Risco (numerador do Sharpe Ratio)"
                                )
                            
                            # NOVO: Se otimizou excesso, mostrar métricas específicas
                            if objective == "🆕 Maximizar Linearidade do Excesso" and metrics.get('excess_r_squared') is not None:
                                st.subheader("🆕 Métricas de Linearidade do Excesso")
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric(
                                        "📈 Inclinação Excesso (×1000)", 
                                        f"{metrics['excess_slope']*1000:.3f}",
                                        help="Inclinação da regressão linear do EXCESSO de retorno"
                                    )
                                
                                with col2:
                                    st.metric(
                                        "📊 R² do Excesso", 
                                        f"{metrics['excess_r_squared']:.3f}",
                                        help="Qualidade da linearidade do excesso (quanto mais próximo de 1, mais linear)"
                                    )
                                
                                with col3:
                                    # Calcular volatilidade do excesso
                                    if hasattr(optimizer, 'risk_free_returns') and optimizer.risk_free_returns is not None:
                                        excess_returns_daily = metrics['portfolio_returns_daily'] - optimizer.risk_free_returns.values
                                        excess_vol = np.std(excess_returns_daily, ddof=0) * np.sqrt(252)
                                    else:
                                        excess_vol = 0
                                    
                                    st.metric(
                                        "📊 Volatilidade do Excesso", 
                                        f"{excess_vol:.2%}",
                                        help="Volatilidade anualizada do excesso de retorno (desvio padrão do excesso × √252)"
                                    )
                            
                            # Explicação sobre VaR e Taxa Livre de Risco
                            st.info(
                                "💡 **VaR**: Mostra a perda máxima esperada. "
                                f"Ex: VaR 95% = {metrics['var_95_daily']:.2%} significa que "
                                f"em 95% dos dias você não perderá mais que {abs(metrics['var_95_daily']):.2%}\n\n"
                                "🏛️ **Taxa Livre de Risco**: Representa o retorno de um investimento sem risco (ex: CDI, Tesouro). "
                                "O Sharpe Ratio mede quanto retorno extra você obtém por unidade de risco adicional."
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
                                    name='Taxa Livre de Risco',
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
                                    st.subheader("📊 Excesso de Retorno Mensal (Portfólio - Taxa Livre)")
                                    
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
        st.error(f"❌ Erro ao processar dados: {e}")

else:
    # Mensagem quando não há arquivo
    st.info("👈 Escolha uma opção de carregamento de dados na barra lateral")
    
    # Instruções atualizadas
    st.markdown("""
    ### 🚀 Como usar o novo sistema:
    
    #### 📂 **Opção 1: Arquivos Disponíveis** (NOVO!)
    - Selecione um conjunto de dados pré-carregado
    - Clique em "Carregar Dados"
    - **Nota**: Você precisa atualizar os IDs dos arquivos no código
    
    #### 📤 **Opção 2: Upload Local**
    - Faça upload de sua própria planilha Excel
    - Formato: primeira coluna = datas, outras = retornos
    
    #### 🔗 **Opção 3: URL do Google Drive** (NOVO!)
    - Cole o link de compartilhamento de qualquer arquivo Excel do Google Drive
    - O sistema carregará automaticamente
    
    ### 📝 Estrutura dos dados:
    - **Coluna A**: Datas
    - **Coluna B** (opcional): Taxa Livre de Risco (CDI, Selic, etc.)
    - **Demais colunas**: Retornos de cada ativo (base 0)
    
    ### 💡 Dicas:
    - Se a coluna B tiver "Taxa Livre", "CDI", ou "Selic" no nome, o sistema detecta automaticamente!
    - Para obter o ID de um arquivo do Google Drive, abra o arquivo e copie o ID da URL
    - Exemplo de URL: `drive.google.com/file/d/ID_AQUI/view`
    """)

# Rodapé
st.markdown("---")
st.markdown("*Desenvolvido com Streamlit - Otimização Portfólio v3.0* 🚀")
