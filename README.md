# 📊 Otimizador de Portfólio v3.0 - Guia do Usuário

## 🎯 Visão Geral

O Otimizador de Portfólio v3.0 é uma ferramenta profissional baseada na Teoria Moderna de Portfólios de Harry Markowitz. **Agora com sistema de janelas temporais** para backtesting real (in-sample vs out-of-sample).

**Link para a ferramenta:** https://otimizador-portfolio.streamlit.app/

## ✨ Principais Funcionalidades v3.0

### 🆕 **NOVIDADES da v3.0:**
• **Sistema de Janelas Temporais** - Análise in-sample vs out-of-sample  
• **Backtesting Profissional** - Treino e validação separados  
• **Múltiplas Fontes de Dados** - Yahoo Finance integrado  
• **Consistência Matemática** - Tabelas mensais alinhadas com otimizador  
• **Interface Reorganizada** - Abas específicas para cada análise  

### 📈 **Funcionalidades Mantidas:**
• Múltiplos objetivos de otimização (Sharpe, Sortino, Mínimo Risco, etc.)  
• Posições Long e Short (vendas a descoberto)  
• Restrições flexíveis por ativo  
• Análise completa de risco e retorno  
• Visualizações interativas do desempenho  

---

## 🚀 Como Começar

### 1. Preparando seus Dados

#### Formato da Planilha Excel

Sua planilha deve seguir esta estrutura:

| Data | Taxa Ref (opcional) | Ativo 1 | Ativo 2 | Ativo 3 | ... |
|------|---------------------|---------|---------|---------|-----|
| 01/01/2023 | 120.54 | 205.32 | 145.65 | 398.56 | ... |
| 02/01/2023 | 123.67 | 204.21 | 139.57 | 399.01 | ... |

**Importante:**
• **Coluna A:** Datas  
• **Coluna B:** Taxa de referência (CDI, IBOV, etc.) - opcional  
• **Demais colunas:** Preços dos ativos (serão convertidos para base 0 automaticamente)  

> 💡 **NOVO em v3.0:** Carregue TODO o período disponível! A seleção temporal será feita depois.

### 2. Carregando os Dados

Agora você tem **três** opções:

#### 📤 Upload Manual
1. Clique em "Upload" na barra lateral
2. Selecione seu arquivo Excel
3. Aguarde o processamento

#### 📊 Dados de Exemplo
1. Clique em "Exemplos" na barra lateral
2. Escolha um dos conjuntos disponíveis:
   - 🏢 Ações Brasileiras
   - 🏠 Fundos Imobiliários  
   - 💰 Fundos de Investimento
   - 🌍 ETFs Nacionais
   - 🪙 Criptomoedas

#### 🌐 **NOVO: Yahoo Finance**
1. Clique em "Yahoo Finance" na barra lateral
2. Digite os códigos dos ativos (um por linha)
3. Escolha o tipo: Ações BR (.SA), Criptomoedas, Ações US, etc.
4. **NOVO:** Modo "Códigos Livres" - digite exatamente como no Yahoo
5. Selecione o período e clique "Buscar"

**Exemplos de códigos:**
- **Ações BR:** PETR4, VALE3, ITUB4
- **Criptomoedas:** BTC-USD, ETH-USD  
- **Ações US:** AAPL, MSFT, GOOGL
- **ETFs:** SPY, QQQ, IVV

---

## 📅 **NOVO: Sistema de Janelas Temporais**

### Conceito das 3 Datas Críticas

```
|-------- Dados Completos Carregados --------|
        |--- Otimização ---|--- Validação ---|
        ↑                 ↑                 ↑
     Início           Fim              Análise
    Otimização     Otimização          Final
```

### Como Configurar

1. **Carregue dados completos** (ex: 2020-2025)
2. **Defina 3 datas:**
   - **Início da Otimização:** Onde começar o treino
   - **Fim da Otimização:** Onde terminar o treino  
   - **Fim da Análise:** Até onde validar (opcional)

### Vantagens do Sistema

✅ **Backtesting Realista** - Otimize em dados históricos, valide em futuros  
✅ **Múltiplas Análises** - Teste vários períodos sem recarregar  
✅ **Comparação In/Out-of-Sample** - Veja performance real vs treino  

---

## 📋 Seleção de Ativos

### Escolhendo Ativos para Otimização

1. Use o campo multiselect para escolher os ativos
2. Digite para filtrar - útil quando há muitos ativos  
3. Mínimo 2 ativos são necessários para otimização

💡 **Dica:** Selecione apenas ativos que deseja na carteira final. Outros podem ser usados como short/hedge.

---

## ⚙️ Configurações de Otimização

### 🎯 Objetivos Disponíveis

#### 1. Maximizar Sharpe Ratio
• Melhor relação retorno/risco  
• Considera volatilidade total  
• Ideal para carteiras tradicionais  

#### 2. Maximizar Sortino Ratio  
• Similar ao Sharpe, mas considera apenas volatilidade negativa  
• Melhor para investidores avessos a perdas  
• Não penaliza volatilidade positiva  

#### 3. Minimizar Risco
• Busca a menor volatilidade possível  
• Ideal para perfis conservadores  
• Pode resultar em retornos menores  

#### 4. Minimizar Under Water
• Minimiza o tempo e a profundidade que a carteira passa abaixo do topo anterior  
• Ideal para quem prioriza recuperação rápida de quedas  

#### 5. Maximizar Inclinação/[(1-R²)×Vol]
• Combina tendência, linearidade e volatilidade  
• Busca crescimento estável e previsível  

#### 6. Maximizar Qualidade da Linearidade  
• Minimiza [Vol × (1-R²)]/R²  
• Busca máxima previsibilidade  
• **Requer taxa de referência**

#### 7. Maximizar Linearidade do Excesso  
• Otimiza a linearidade do retorno acima da taxa de referência  
• Ideal para fundos que buscam superar um benchmark  
• **Requer taxa de referência**

#### 8. Maximizar Sharpe do Excesso
• Aplica a lógica do Sharpe sobre o retorno acima da taxa de referência  
• Combina superação do benchmark com controle de risco  
• **Requer taxa de referência**

### 🎯 Meta de Retorno (opcional)

Permite exigir um retorno mínimo da carteira otimizada, em dois modos:

• **Relativa:** % acima da taxa de referência no período (ex.: 5% acima do CDI)  
• **Absoluta:** % ao ano, independente da referência (ex.: 15% ao ano)  

Disponível tanto na otimização manual quanto na Auto-Otimização (onde é
aplicada em cada janela do walk-forward).

> 💡 Se a meta não for atingível, o otimizador entrega a **melhor carteira
> viável** e avisa, em vez de simplesmente falhar.

### 📊 Limites de Peso

#### Peso Mínimo Global (0-20%)
• Define alocação mínima para cada ativo  
• 0% = sem mínimo obrigatório  
• Útil para garantir diversificação  

#### Peso Máximo Global (5-100%)  
• Limita exposição máxima por ativo  
• 30% é um bom padrão para diversificação  
• 100% permite concentração total  

---

## 🎯 **Restrições Individuais (Opcional)**

Permite definir limites específicos para ativos selecionados.

### Quando Usar
• **Posições existentes:** Trave um ativo em peso específico (min = max)  
• **Core holdings:** Garanta alocação mínima em ativos principais  
• **Limitar risco:** Restrinja exposição a ativos voláteis  

### Como Configurar
1. Ative "Definir limites específicos para alguns ativos"  
2. Selecione os ativos que terão limites customizados  
3. Defina Min% e Max% para cada ativo selecionado  

### 📥 Importar Restrições de Excel/CSV

Em vez de digitar ativo por ativo, você pode enviar uma planilha:

| Formato | Colunas | Efeito |
|---|---|---|
| **Faixas** | `Ativo`, `Min`, `Max` | Define mínimo e máximo por ativo |
| **Pesos fixos** | `Ativo`, `Peso` | Fixa min = max = peso |

• Valores em percentual (`30` = 30%) ou fração (`0.30`)  
• Aceita vírgula decimal, símbolo `%` e CSV com `;` ou tabulação  
• Nomes de coluna flexíveis (`Ticker`, `Mínimo`, `Máximo`, `Peso`...)  
• Ativos fora da seleção atual são ignorados, com aviso  

> 🔒 **Modo analisador de carteira:** com pesos fixos somando 100%, o
> otimizador fica travado exatamente naquela composição — útil para
> avaliar as métricas de uma carteira que você já possui.

### Exemplos Práticos
• **Manter posição:** PETR4 → Min: 15%, Max: 15%  
• **Posição principal:** VALE3 → Min: 20%, Max: 40%  
• **Limitar small cap:** MGLU3 → Min: 0%, Max: 5%  

---

## 🔄 Posições Short/Hedge (Opcional)

Permite incluir vendas a descoberto (posições negativas) na carteira.

### Como Funciona
1. Ative "Habilitar posições short/hedge"  
2. Selecione ativos para posição vendida  
3. Defina o peso negativo (-100% a 0%)  

### Estratégias Comuns

#### Hedge de Mercado
• Short -50% IBOV  
• Reduz exposição ao risco sistemático  

#### Arbitragem de Taxa  
• Short -100% CDI  
• Captura spread sobre a taxa livre  

#### Long/Short
• Long em ações selecionadas  
• Short em índice ou setor  

⚠️ **Importante**
• Pesos short são fixos (não otimizados)  
• Não entram na soma de 100% do portfólio  
• Entram no cálculo de todas as métricas  

---

## 📈 Interpretando os Resultados

### Sistema de 3 Abas

#### 📊 **Aba "Período de Otimização" (In-Sample)**
• **Métricas:** Período de treino apenas  
• **Tabela mensal:** Período de treino apenas  
• **Gráfico:** Período de treino com 3 linhas  

#### 🔍 **Aba "Período de Validação" (Out-of-Sample)**  
• **Métricas:** Período de validação  
• **Tabela mensal:** Período completo (treino + teste)  
• **Gráfico:** Período completo com divisão visual  

#### 📈 **Aba "Comparação"**
• **Tabela comparativa:** In-sample vs Out-of-sample  
• **Análise de robustez:** Performance fora da amostra  

### 🤖 Colunas da Auto-Otimização

| Coluna | Significado |
|---|---|
| **Sharpe** | Sharpe do walk-forward completo |
| **Retorno(%)** | Retorno anualizado |
| **Meta_OK(%)** | % dos rebalanceamentos que bateram a meta *dentro* da janela de otimização (`—` se a meta não foi usada) |
| **Taxa_Ref(%)** | Taxa de referência anualizada |
| **Volatilidade(%)** | Risco anualizado |
| **VaR(%)** | Perda diária esperada no pior 5% dos dias (média dos períodos) |
| **Pos>Ref(%)** | % dos períodos que superaram a taxa de referência |
| **Positivos(%)** | % dos períodos com retorno acima de zero |

> ⚠️ **Positivos** e **Pos>Ref** são medidos **por período de rebalanceamento**,
> não por dia.

**Exportação:** CSV e Excel saem com **números de verdade** (não texto), então
dá para ordenar e recalcular na planilha. No Excel os percentuais vêm com
formato de célula percentual; no CSV, já multiplicados (`18.5` = 18,5%).

### Métricas Principais

#### 📊 Retorno e Risco
• **Retorno Total:** Ganho acumulado no período  
• **Ganho Anual:** Retorno anualizado  
• **Volatilidade:** Risco anualizado (desvio padrão × √252)  

#### ⚡ Índices de Performance
• **Sharpe Ratio:** Retorno por unidade de risco  
  - \> 1.0 = Bom  
  - \> 2.0 = Muito bom  
  - \> 3.0 = Excelente  

• **Sortino Ratio:** Similar ao Sharpe, mas considera apenas risco negativo  
  - Geralmente maior que Sharpe  
  - Melhor métrica para assimetria  

#### 📉 Métricas de Risco
• **R²:** Qualidade da tendência (0 a 1)  
  - \> 0.8 = Alta linearidade  

• **VaR 95%:** Perda máxima esperada em 95% dos dias  
  - Ex: -2% = Em 95% dos dias, não perderá mais que 2%  

### **Gráficos com Divisão Visual**

Na aba de validação, o gráfico mostra:  
• **Área verde:** Período de otimização (treino)  
• **Área azul:** Período de validação (teste)  
• **Linha vermelha:** Divisão entre os períodos  
• **3 linhas:** Portfólio, Taxa Ref, Excesso  

### **Tabela de Performance Mensal**

• **Metodologia consistente** com otimizador (base 0)  
• **Retornos mensais** Os valores são calculados em relação à "cota" inicial e não do mês anterior.
• **Total anual** = soma dos meses (como descrito no ítem anterior)  
• **Cores:** Verde (ganho) / Vermelho (perda)  

---

## 💡 Dicas e Boas Práticas v3.0

### Para Melhores Resultados

#### 1. **NOVO: Use o Sistema de Janelas**
• **70% otimização / 30% validação** é uma boa proporção  
• **Teste múltiplos períodos** para verificar robustez  
• **Performance out-of-sample** é mais importante que in-sample  

#### 2. Use dados de qualidade  
• **Mínimo 2 anos** de histórico para janelas temporais  
• Dados diários preferíveis  
• Evite períodos com muitos feriados  

#### 3. Diversifique adequadamente
• 5-15 ativos é ideal  
• Evite ativos muito correlacionados  
• Considere diferentes setores/classes  

### Casos de Uso

#### Validação de Estratégia
• **Otimização:** 2020-2022  
• **Validação:** 2023-2024  
• **Objetivo:** Verificar se estratégia funciona fora da amostra  

#### Análise de Robustez  
• **Múltiplas janelas:** Teste vários períodos  
• **Compare in vs out:** Performance deve ser consistente  
• **Ajuste parâmetros** se out-of-sample for muito pior  

#### Backtesting Rolling
• **Janeiro-Dezembro:** Otimize  
• **Próximo ano:** Valide  
• **Rebalanceie** periodicamente  

---

## ❓ Perguntas Frequentes

### Como usar as janelas temporais?
**R:** Carregue dados completos, depois selecione períodos específicos. Use 70% para otimização e 30% para validação. Performance out-of-sample mais importante.

### Yahoo Finance não encontra meu ativo
**R:** 
- **Ações BR:** Use código + .SA (ex: PETR4.SA)  
- **Criptos:** Use formato completo (ex: BTC-USD)  
- **Códigos livres:** Digite exatamente como aparece no Yahoo  
- **Verifique** se o período tem dados suficientes  

### Por que in-sample é melhor que out-of-sample?
**R:** Normal! Otimização "conhece" os dados de treino. Se diferença for muito grande (>50%), pode indicar overfitting. Ajuste parâmetros ou período.

### O que é melhor: Sharpe ou Sortino?
**R:** Sortino é geralmente preferível pois não penaliza volatilidade positiva. Use Sharpe para comparação com benchmarks tradicionais.

### Quantos ativos devo incluir?  
**R:** Entre 5-15 ativos oferece boa diversificação sem complexidade excessiva. Mais que 20 pode diluir demais os retornos.

### **NOVO: Tabela mensal diferente do período?**
**R:** v3.0 corrigiu isso! Agora usa mesma metodologia base 0. Retornos mensais somam exatamente o total do período.

---

## 🚧 Limitações Conhecidas

1. **Dados históricos:** Performance passada não garante resultados futuros  
2. **Custos não incluídos:** Não considera taxas, impostos ou slippage  
3. **Liquidez:** Assume que todos ativos podem ser negociados nos pesos calculados  
4. **Correlações estáticas:** Assume que correlações históricas se manterão  
5. **NOVO: Overfitting:** Performance in-sample pode não se repetir out-of-sample  

---

## 📞 Suporte

Para dúvidas, sugestões ou reportar bugs:
• Abra uma issue no GitHub  
• Contribua com melhorias via Pull Request  

---

## 📜 Aviso Legal

Esta ferramenta é fornecida apenas para fins educacionais e informativos. Não constitui recomendação de investimento. Sempre consulte um profissional qualificado antes de tomar decisões de investimento.

---

## 🏆 Changelog v3.0

### ✨ Principais Novidades
- [x] **Sistema de Janelas Temporais** - Backtesting in-sample vs out-of-sample  
- [x] **Integração Yahoo Finance** - Busca automática de dados  
- [x] **Abas Reorganizadas** - Otimização, Validação e Comparação  
- [x] **Gráficos com Divisão Visual** - Áreas coloridas para treino/teste  

### 🔧 Melhorias Técnicas  
- [x] **Consistência Matemática** - Tabelas mensais alinhadas com otimizador  
- [x] **Metodologia Base 0** - Cálculos uniformes em todo sistema  
- [x] **Interface Limpa** - Remoção de elementos desnecessários  
- [x] **Tratamento de Erros** - Validações para casos sem dados  

### 🐛 Correções
- [x] **Tabela mensal** agora usa mesma metodologia do otimizador  
- [x] **Retornos anuais** = soma dos retornos mensais  
- [x] **Gráficos com 12 datas** no eixo X (sem sobreposição)  
- [x] **Validação sem período** não gera mais erro  

---

**Desenvolvido com ❤️ usando Streamlit e Python**  
**v3.0 - Agora com Janelas Temporais para Backtesting Profissional** 🚀
