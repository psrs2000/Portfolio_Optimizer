import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from optimizer import PortfolioOptimizer

# Configuração da página
st.set_page_config(
    page_title="Otimizador de Portfólio",
    page_icon="📊",
    layout="wide"
)

# Título
st.title("📊 Otimizador de Portfólio")
st.markdown("*Baseado na metodologia da sua planilha Excel*")

# Sidebar para upload
with st.sidebar:
    st.header("📁 Upload dos Dados")
    uploaded_file = st.file_uploader(
        "Escolha sua planilha Excel",
        type=['xlsx', 'xls'],
        help="Planilha com dados históricos dos ativos"
    )

def create_monthly_returns_table(returns_data, weights, dates=None):
    """
    Cria tabela de retornos mensais do portfólio otimizado
    """
    # Calcular retornos diários do portfólio
    portfolio_returns_daily = np.dot(returns_data.values, weights)
    
    # Criar DataFrame com retornos diários
    portfolio_df = pd.DataFrame({
        'returns': portfolio_returns_daily
    }, index=range(len(portfolio_returns_daily)))
    
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
    
    # Formatar como porcentagem
    return pivot_table

# Área principal
if uploaded_file is not None:
    try:
        # Ler o arquivo
        df = pd.read_excel(uploaded_file)
        
        st.success("✅ Arquivo carregado com sucesso!")
        
        # Mostrar preview dos dados
        with st.expander("📋 Ver dados carregados"):
            st.write(f"Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
            st.dataframe(df.head(10))
        
        # Seleção de ativos
        st.header("🎯 Seleção de Ativos")
        
        # Identificar colunas de ativos (excluindo primeira coluna se for data)
        if isinstance(df.columns[0], str) and 'data' in df.columns[0].lower():
            asset_columns = df.columns[1:].tolist()
        else:
            asset_columns = df.columns.tolist()
        
        st.markdown("Selecione os ativos que deseja incluir na otimização:")
        
        # Opção com multiselect - NENHUM selecionado por padrão
        selected_assets = st.multiselect(
            "🔍 Digite para buscar ou clique para selecionar:",
            options=asset_columns,
            default=[],  # ALTERAÇÃO: Nenhum selecionado por padrão
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
            objective = st.selectbox(
                "🎯 Objetivo da Otimização",
                ["Maximizar Sharpe Ratio", "Minimizar Risco", "Maximizar Inclinação", "Maximizar Inclinação/[(1-R²)×Vol]"],
                help="Escolha o que você quer otimizar"
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
            risk_free_rate = st.number_input(
                "🏛️ Taxa Livre de Risco (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.1,
                help="Taxa livre de risco ACUMULADA do período (ex: se CDI acumulou 12% no período, digite 12.0)"
            ) / 100  # Converter para decimal
                                
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
                        
                        # Definir tipo de objetivo
                        if objective == "Maximizar Sharpe Ratio":
                            obj_type = 'sharpe'
                        elif objective == "Minimizar Risco":
                            obj_type = 'volatility'
                        elif objective == "Maximizar Inclinação":
                            obj_type = 'slope'
                        elif objective == "Maximizar Inclinação/[(1-R²)×Vol]":
                            obj_type = 'hc10'
                        
                        # Executar otimização
                        result = optimizer.optimize_portfolio(
                            objective_type=obj_type,
                            target_return=None,
                            max_weight=max_weight,
                            risk_free_rate=risk_free_rate  # Adicionar taxa livre de risco
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
                            
                            # Gráfico de evolução do portfólio
                            st.header("📈 Evolução do Portfólio Otimizado")
                            
                            # Criar DataFrame para o gráfico
                            portfolio_evolution_df = pd.DataFrame({
                                'Período': range(1, len(metrics['portfolio_cumulative']) + 1),
                                'Retorno Acumulado (%)': metrics['portfolio_cumulative'] * 100
                            })
                            
                            # Criar gráfico de linha
                            fig_line = px.line(
                                portfolio_evolution_df,
                                x='Período',
                                y='Retorno Acumulado (%)',
                                title='Evolução do Retorno Acumulado do Portfólio',
                                labels={'Período': 'Dias de Negociação', 'Retorno Acumulado (%)': 'Retorno Acumulado (%)'}
                            )
                            
                            # Personalizar o gráfico
                            fig_line.update_traces(
                                line_color='#1f77b4',
                                line_width=2.5
                            )
                            
                            fig_line.update_layout(
                                hovermode='x unified',
                                showlegend=False,
                                height=400,
                                xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)'),
                                yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
                            )
                            
                            # Adicionar anotação com retorno final
                            fig_line.add_annotation(
                                x=len(portfolio_evolution_df),
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
                                dates = getattr(optimizer, 'dates', None)  # Pegar datas se disponíveis
                                monthly_table = create_monthly_returns_table(
                                    optimizer.returns_data, 
                                    result['weights'],
                                    dates
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
                                
                                # Formatar tabela para exibição
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
    st.info("👆 Faça upload de uma planilha Excel para começar")
    
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
    
    2. **Prepare sua planilha** com:
       - Primeira coluna: Datas
       - Outras colunas: Retornos de cada ativo (base 0)
    
    3. **Faça upload** do arquivo Excel
    
    4. **Configure** os parâmetros de otimização
    
    5. **Clique em otimizar** e receba os pesos ideais!
    
    ### 💡 Dica:
    Caso vá criar seu próprio arquivo, os dados devem ser Inseridos na base 0. Isso significa que o primeiro valor (V1) = 0 e os subsequentes são: V2=(cota2-cota1)/cota1; V3=(cota3-cota2)/cota1; assim por diante
    """)

# Rodapé
st.markdown("---")
st.markdown("*Desenvolvido com Streamlit - Otimização Portifólio* 🚀")
