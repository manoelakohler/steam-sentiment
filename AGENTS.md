# Regras do projeto

- Escrever Python simples e legível.
- Separar coleta, inferência, persistência e interface.
- Evitar frameworks desnecessários.
- Usar type hints quando ajudarem a leitura.
- Nunca colocar chaves ou segredos no código.
- Executar e testar o código depois de alterações relevantes.
- Preferir mudanças pequenas e incrementais.
- Explicar brevemente qualquer decisão arquitetural importante antes de fazer uma mudança grande.
- Usar o ambiente virtual do projeto (.venv), inclusive para instalar dependências e executar testes.
- Coletar reviews em inglês pela API pública da Steam, sem scraping de HTML.
- Preservar a deduplicação por review_id e analisar somente reviews ainda não salvas.
- Manter o modelo reutilizável e evitar carregá-lo a cada review ou atualização da interface.
- Não versionar bancos locais, cache de modelos, ambiente virtual ou segredos.
- Atualizar README.md e requirements.txt quando o uso ou as dependências mudarem.

Validação: .\.venv\Scripts\python.exe -m unittest discover -s tests -v
