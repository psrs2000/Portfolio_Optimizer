📊 Otimizador de Portfólio - Guia do Usuário

🎯 Visão Geral

O Otimizador de Portfólio é uma ferramenta profissional baseada na Teoria Moderna de Portfólios de Harry Markowitz. Permite otimizar a alocação de investimentos maximizando retornos ajustados ao risco.

Link para a ferramenta: https://otimizador-portfolio.streamlit.app/

✨ Principais Funcionalidades

•	Múltiplos objetivos de otimização (Sharpe, Sortino, Mínimo Risco, etc.)

•	Posições Long e Short (vendas a descoberto)

•	Restrições flexíveis por ativo

•	Análise completa de risco e retorno

•	Visualizações interativas do desempenho

________________________________________

🚀 Como Começar

1. Preparando seus Dados

Formato da Planilha Excel

Sua planilha deve seguir esta estrutura:

Data	Taxa Ref (opcional)	Ativo 1	Ativo 2	Ativo 3	...

01/01/2023	120.54	205.32	145.65	398.56	...

02/01/2023	123.67	204.21	139.57	399.01	...

Importante:

•	Coluna A: Datas

•	Coluna B: Taxa de referência (CDI, IBOV, etc.) - opcional

•	Demais colunas: Retornos diários dos ativos (formato decimal, não percentual)

2. Carregando os Dados

Você tem duas opções:

📤 Upload Manual

1.	Clique em "Upload" na barra lateral

2.	Selecione seu arquivo Excel

3.	Aguarde o carregamento

📊 Dados de Exemplo

1.	Clique em "Exemplos" na barra lateral

2.	Escolha um dos conjuntos disponíveis: 

o	Ações Brasileiras

o	Fundos Imobiliários

o	ETFs Nacionais

o	Criptomoedas

________________________________________

📋 Seleção de Ativos

Escolhendo Ativos para Otimização

1.	Use o campo multiselect para escolher os ativos

2.	Digite para filtrar - útil quando há muitos ativos

3.	Mínimo 2 ativos são necessários para otimização

💡 Dica: Selecione apenas ativos que deseja na carteira final. Outros podem ser usados como short/hedge.

________________________________________

⚙️ Configurações de Otimização

🎯 Objetivos Disponíveis

1. Maximizar Sharpe Ratio

•	Melhor relação retorno/risco

•	Considera volatilidade total

•	Ideal para carteiras tradicionais

2. Maximizar Sortino Ratio

•	Similar ao Sharpe, mas considera apenas volatilidade negativa

•	Melhor para investidores avessos a perdas

•	Não penaliza volatilidade positiva

3. Minimizar Risco

•	Busca a menor volatilidade possível

•	Ideal para perfis conservadores

•	Pode resultar em retornos menores

4. Maximizar Inclinação

•	Busca a tendência de alta mais consistente

•	Útil para estratégias de tendência

5. Maximizar Inclinação/[(1-R²)×Vol]

•	Combina tendência, linearidade e volatilidade

•	Busca crescimento estável e previsível

6. Maximizar Qualidade da Linearidade
7. 
•	Minimiza [Vol × (1-R²)]/R²

•	Busca máxima previsibilidade

7. Maximizar Linearidade do Excesso (requer taxa de referência)

•	Otimiza a linearidade do retorno acima da taxa de referência

•	Ideal para fundos que buscam superar um benchmark

📊 Limites de Peso

Peso Mínimo Global (0-20%)

•	Define alocação mínima para cada ativo

•	0% = sem mínimo obrigatório

•	Útil para garantir diversificação

Peso Máximo Global (5-100%)

•	Limita exposição máxima por ativo

•	30% é um bom padrão para diversificação

•	100% permite concentração total

________________________________________

🎯 Restrições Individuais (Opcional)

Permite definir limites específicos para ativos selecionados.

Quando Usar

•	Posições existentes: Trave um ativo em peso específico (min = max)

•	Core holdings: Garanta alocação mínima em ativos principais

•	Limitar risco: Restrinja exposição a ativos voláteis

Como Configurar

1.	Ative "Definir limites específicos para alguns ativos"

2.	Selecione os ativos que terão limites customizados

3.	Defina Min% e Max% para cada ativo selecionado

Exemplos Práticos

•	Manter posição: PETR4 → Min: 15%, Max: 15%

•	Posição principal: VALE3 → Min: 20%, Max: 40%

•	Limitar small cap: MGLU3 → Min: 0%, Max: 5%

________________________________________

🔄 Posições Short/Hedge (Opcional)

Permite incluir vendas a descoberto (posições negativas) na carteira.

Como Funciona

1.	Ative "Habilitar posições short/hedge"

2.	Selecione ativos para posição vendida

3.	Defina o peso negativo (-100% a 0%)

Estratégias Comuns

Hedge de Mercado

•	Short -50% IBOV

•	Reduz exposição ao risco sistemático

Arbitragem de Taxa

•	Short -100% CDI

•	Captura spread sobre a taxa livre

Long/Short

•	Long em ações selecionadas

•	Short em índice ou setor

⚠️ Importante

•	Pesos short são fixos (não otimizados)

•	Não entram na soma de 100% do portfólio

•	Entram no cálculo de todas as métricas

________________________________________

📈 Interpretando os Resultados

Métricas Principais

📊 Retorno e Risco

•	Retorno Total: Ganho acumulado no período

•	Ganho Anual: Retorno anualizado

•	Volatilidade: Risco anualizado (desvio padrão × √252)

⚡ Índices de Performance

•	Sharpe Ratio: Retorno por unidade de risco

o	> 1.0 = Bom

o	> 2.0 = Muito bom

o	> 3.0 = Excelente

•	Sortino Ratio: Similar ao Sharpe, mas considera apenas risco negativo

o	Geralmente maior que Sharpe

o	Melhor métrica para assimetria

📉 Métricas de Risco

•	R²: Qualidade da tendência (0 a 1)

o	> 0.8 = Alta linearidade

•	VaR 95%: Perda máxima esperada em 95% dos dias

o	Ex: -2% = Em 95% dos dias, não perderá mais que 2%

•	Downside Deviation: Volatilidade apenas dos retornos negativos

Composição do Portfólio

A tabela mostra:

•	Ativos com peso > 0.1%

•	Percentual exato de alocação

•	Visualização em gráfico de pizza

Gráfico de Evolução

Mostra três linhas:

1.	Azul: Portfólio otimizado

2.	Laranja (tracejada): Taxa de referência

3.	Verde (pontilhada): Excesso de retorno

Tabela de Performance Mensal

•	Retornos mensais organizados por ano

•	Cores: Verde (ganho) / Vermelho (perda)

•	Total anual na última coluna

________________________________________

💡 Dicas e Boas Práticas

Para Melhores Resultados

1.	Use dados de qualidade

o	Mínimo 1 ano de histórico

o	Dados diários preferíveis

o	Evite períodos com muitos feriados

2.	Diversifique adequadamente

o	5-15 ativos é ideal

o	Evite ativos muito correlacionados

o	Considere diferentes setores/classes

3.	Ajuste os limites com cuidado

o	Peso máximo 20-30% para diversificação

o	Peso mínimo 0-5% para flexibilidade

o	Use restrições individuais com parcimônia

Casos de Uso Comuns

Carteira Conservadora

•	Objetivo: Minimizar Risco

•	Peso máximo: 20%

•	Incluir renda fixa

Carteira Agressiva

•	Objetivo: Maximizar Sharpe/Sortino

•	Peso máximo: 40%

•	Considerar shorts para hedge

Carteira Balanceada

•	Objetivo: Maximizar Inclinação/[(1-R²)×Vol]

•	Peso máximo: 30%

•	Restrições em ativos core

________________________________________

❓ Perguntas Frequentes

O que é melhor: Sharpe ou Sortino?

Sortino é geralmente preferível pois não penaliza volatilidade positiva. Use Sharpe para comparação com benchmarks tradicionais.

Quantos ativos devo incluir?

Entre 5-15 ativos oferece boa diversificação sem complexidade excessiva. Mais que 20 pode diluir demais os retornos.

Posso confiar 100% na otimização?

A otimização é baseada em dados históricos. Use como guia, não como regra absoluta. Considere sempre:

•	Mudanças no cenário econômico

•	Custos de transação

•	Liquidez dos ativos

Por que meu ativo favorito ficou com peso zero?

O otimizador busca a melhor combinação matemática. Ativos com:

•	Alta correlação com outros

•	Baixo retorno ajustado ao risco

•	Alta volatilidade Podem receber peso zero. Use restrições individuais se quiser garantir alocação.

Como interpreto R² alto com Sharpe baixo?

•	R² alto: Tendência consistente

•	Sharpe baixo: Retorno insuficiente para o risco Comum em ativos com tendência de queda consistente.

________________________________________

🚧 Limitações Conhecidas

1.	Dados históricos: Performance passada não garante resultados futuros

2.	Custos não incluídos: Não considera taxas, impostos ou slippage

3.	Liquidez: Assume que todos ativos podem ser negociados nos pesos calculados

4.	Correlações estáticas: Assume que correlações históricas se manterão

________________________________________

📞 Suporte

Para dúvidas, sugestões ou reportar bugs:

•	Abra uma issue no GitHub

•	Contribua com melhorias via Pull Request

________________________________________

📜 Aviso Legal

Esta ferramenta é fornecida apenas para fins educacionais e informativos. Não constitui recomendação de investimento. Sempre consulte um profissional qualificado antes de tomar decisões de investimento.

________________________________________

Desenvolvido com ❤️ usando Streamlit e Python

