Uma ferramenta profissional de otimização de portfólio baseada na Teoria Moderna de Portfólios de Harry Markowitz.
✨ Features

📈 Múltiplos objetivos de otimização (Sharpe, Sortino, Mínima Volatilidade)
🔄 Suporte para posições Long e Short
🎯 Restrições flexíveis por ativo
📊 Visualizações interativas com Plotly
📅 Análise de performance mensal
💹 Métricas avançadas de risco (VaR, Downside Deviation)

🚀 Demo
Acesse a aplicação online: portfolio-optimizer.streamlit.app
🛠️ Instalação
Pré-requisitos

Python 3.8 ou superior
pip (gerenciador de pacotes Python)

Passo a passo

Clone o repositório:

bashgit clone https://github.com/psrs2000/Portfolio_Optimizer.git
cd Portfolio_Optimizer

Crie um ambiente virtual (recomendado):

bashpython -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

Instale as dependências:

bashpip install -r requirements.txt

Execute a aplicação:

bashstreamlit run app.py

Acesse no navegador:

http://localhost:8501
📁 Estrutura do Projeto
Portfolio_Optimizer/
│
├── app.py                 # Aplicação principal Streamlit
├── optimizer.py           # Motor de otimização
├── requirements.txt       # Dependências Python
├── config.toml           # Configurações do Streamlit
│
├── sample_data/          # Dados de exemplo
│   ├── acoes_brasileiras.xlsx
│   ├── fundos_imobiliarios.xlsx
│   └── ...
│
└── docs/                 # Documentação
    └── USER_GUIDE.md     # Guia completo do usuário
📊 Formato dos Dados
Os dados devem estar em formato Excel (.xlsx) com a seguinte estrutura:
DataTaxa Ref (opcional)Ativo 1Ativo 2...01/01/20230.00050.0120-0.0050...02/01/20230.0005-0.00300.0100...

Coluna A: Datas
Coluna B: Taxa de referência (opcional)
Demais colunas: Retornos diários dos ativos

🔧 Tecnologias Utilizadas

Streamlit - Interface web
Pandas - Manipulação de dados
NumPy - Cálculos numéricos
SciPy - Otimização
Plotly - Visualizações interativas

📖 Documentação
Para guia completo de uso, consulte o Guia do Usuário.
🤝 Contribuindo
Contribuições são bem-vindas! Por favor:

Faça um Fork do projeto
Crie uma branch para sua feature (git checkout -b feature/AmazingFeature)
Commit suas mudanças (git commit -m 'Add some AmazingFeature')
Push para a branch (git push origin feature/AmazingFeature)
Abra um Pull Request

🐛 Reportando Bugs
Encontrou um bug? Por favor, abra uma issue com:

Descrição do problema
Passos para reproduzir
Comportamento esperado
Screenshots (se aplicável)

📈 Roadmap

 Adicionar mais métricas de risco (CVaR, Maximum Drawdown)
 Implementar backtesting com rebalanceamento
 Suporte para importação via APIs (Yahoo Finance, etc.)
 Exportar resultados em PDF
 Otimização multi-período

👨‍💻 Autor
Paulo Reis - @psrs2000
📄 Licença
Este projeto está sob a licença MIT - veja o arquivo LICENSE para detalhes.
🙏 Agradecimentos

Harry Markowitz pela Teoria Moderna de Portfólios
Comunidade Streamlit pelo excelente framework
Todos os contribuidores e usuários do projeto


⭐ Se este projeto foi útil, considere dar uma estrela no GitHub!
