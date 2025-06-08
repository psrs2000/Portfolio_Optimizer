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
st.title("📊 Otimizador de Portfólio Markowitz")
st.markdown("*Baseado na metodologia da sua planilha Excel*")

# Sidebar para upload
with st.sidebar:
    st.header("📁 Upload dos Dados")
    uploaded_file = st.file_uploader(
        "Escolha sua planilha Excel",
        type=['xlsx', 'xls'],
        help="Planilha com dados históricos dos ativos"
    )

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
        
        # Opção com multiselect - MUITO mais compacto
        selected_assets = st.multiselect(
            "🔍 Digite para buscar ou clique para selecionar:",
            options=asset_columns,
            default=asset_columns,  # Todos selecionados por padrão
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
                ["Maximizar Sharpe Ratio", "Minimizar Risco", "Maximizar HC10"],
                help="Escolha o que você quer otimizar"
            )
        
        with col2:
            max_weight = st.slider(
                "📊 Peso máximo por ativo (%)",
                min_value=10,
                max_value=100,
                value=30,
                step=1,
                help="Limite máximo para cada ativo no portfólio"
            ) / 100
        
        with col3:
            st.info("💡 **HC10**: Sua métrica especial que considera inclinação e qualidade da tendência")
        
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
                        elif objective == "Maximizar HC10":
                            obj_type = 'hc10'
                        
                        # Executar otimização
                        result = optimizer.optimize_portfolio(
                            objective_type=obj_type,
                            target_return=None,
                            max_weight=max_weight
                        )
                        
                        if result['success']:
                            st.success("🎉 Otimização concluída com sucesso!")
                            
                            # Métricas principais
                            metrics = result['metrics']
                            
                            # Primeira linha de métricas
                            col1, col2, col3, col4, col5, col6 = st.columns(6)
                            
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
                                    help="HC8 - GV_final / Volatilidade"
                                )
                            
                            with col5:
                                st.metric(
                                    "🎯 HC10", 
                                    f"{metrics['hc10']:.4f}",
                                    help="HC10 - Inclinação / [Vol × (1-R²)]"
                                )
                            
                            with col6:
                                st.metric(
                                    "📈 R²", 
                                    f"{metrics['r_squared']:.3f}",
                                    help="Qualidade da linearidade da tendência"
                                )
                            
                            # Segunda linha - Métricas de risco (VaR)
                            st.subheader("📊 Métricas de Risco")
                            col1, col2, col3 = st.columns(3)
                            
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
                                # Explicação do VaR
                                st.info(
                                    "💡 **VaR**: Mostra a perda máxima esperada. "
                                    f"Ex: VaR 95% = {metrics['var_95_daily']:.2%} significa que "
                                    f"em 95% dos dias você não perderá mais que {abs(metrics['var_95_daily']):.2%}"
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
                            
                            # Instruções para o usuário
                            st.header("📝 Como Implementar")
                            st.info(
                                "💡 **Próximos passos:** Use os pesos acima para alocar seu capital. "
                                "Por exemplo, se você tem R$ 10.000, aplique conforme a tabela: "
                                "35% = R$ 3.500 no primeiro ativo, etc."
                            )
                        
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
    
    # Instruções
    st.markdown("""
    ### 📝 Como usar:
    
    1. **Prepare sua planilha** com:
       - Primeira coluna: Datas
       - Outras colunas: Retornos de cada ativo (base 0)
    
    2. **Faça upload** do arquivo Excel
    
    3. **Configure** os parâmetros de otimização
    
    4. **Clique em otimizar** e receba os pesos ideais!
    
    ### 💡 Dica:
    Use a mesma planilha que você já tem, só remova as colunas de fórmulas (GP, GQ, HC, etc.)
    """)

# Rodapé
st.markdown("---")
st.markdown("*Desenvolvido com Streamlit - Otimização Markowitz* 🚀")