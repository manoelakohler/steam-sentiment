# Steam Sentiment Monitor

App local para acompanhar reviews em inglês da Steam e comparar o sentimento
previsto por um Transformer com a recomendação do usuário.

## Instalação e execução

Requer Python 3.11 ou superior. Ambiente testado: Python 3.13, CPU e Windows.
Execute os comandos na raiz do projeto, em PowerShell. Se o ambiente virtual
não existir, crie-o:

```powershell
python -m venv .venv
```

Instale as dependências e inicie o app:

```powershell
.\.venv\Scripts\python.exe -m pip install "torch==2.14.1" --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra [http://localhost:8501](http://localhost:8501), informe o App ID
(por exemplo, 620 para Portal 2) e clique em **Atualizar reviews**.
A primeira análise baixa o modelo público do Hugging Face; não exige chave de API.
As versões das dependências diretas estão fixadas em requirements.txt.

## Dashboard

- Total armazenado e novas reviews da última atualização.
- Percentual positivo segundo a IA, recomendações na Steam e accuracy contra voted_up.
- Distribuição positiva/negativa e evolução diária do percentual positivo.
- Matriz IA × recomendação, com rótulos Recomendou/Não recomendou e Positivo/Negativo.
- Até cinco reviews por seção: positivas mais confiantes, negativas mais confiantes
  e discordâncias entre IA e usuário. Cada item expansível mostra texto completo,
  confiança e recomendação do usuário.

Os indicadores usam todas as reviews salvas do App ID selecionado. A evolução
agrupa pela data de criação em UTC e não preenche dias sem reviews; o tooltip
informa a quantidade de reviews do dia. A contagem da última atualização é
mantida por jogo durante a sessão. Sem dados, os percentuais aparecem como —.

## Fluxo e persistência

Cada atualização consulta uma página de até 100 reviews recentes pela
[API pública da Steam](https://partner.steamgames.com/doc/store/getreviews), sem
scraping de HTML. Usa language=english e inclui qualquer tipo de compra,
mantendo o filtro padrão da Steam para atividade fora de tópico.
O idioma segue a classificação da Steam. Não há paginação ou repetição automática.

O fluxo verifica os IDs existentes, analisa somente reviews novas e salva o lote
em uma transação SQLite. review_id é a chave primária; conflitos não duplicam
nem sobrescrevem registros. Reviews já salvas mantêm texto, votos e previsão
originais. Tabela, índice e pasta do banco são criados automaticamente.

Campos armazenados: review_id, app_id, texto, timestamp de criação (Unix,
segundos), voted_up, votes_up, playtime_forever (minutos), label e confidence.
Uma falha na análise ou na gravação não salva parcialmente o lote.

## Modelo e avaliação

Usa Hugging Face Transformers com
[DistilBERT ajustado em SST-2 para inglês](https://huggingface.co/distilbert/distilbert-base-uncased-finetuned-sst-2-english).
A classificação é binária: POSITIVE e NEGATIVE. O modelo é carregado na primeira
análise e reutilizado no processo; roda em CPU, em lotes de oito por padrão.
Textos longos são truncados em 512 tokens; textos vazios geram ValueError.

A avaliação usa POSITIVE como previsão de voted_up=True e retorna accuracy,
precision, recall, F1, matriz de confusão e exemplos discordantes. A matriz tem
linhas reais e colunas previstas, na ordem negativo/positivo: [[TN, FP], [FN, TP]].
Divisões por zero retornam 0.0; uma amostra vazia gera ValueError.

As métricas medem concordância com a recomendação do usuário. O modelo não foi
ajustado em reviews da Steam; sarcasmo e textos mistos podem produzir divergências.
confidence é o score da classe prevista, não uma garantia calibrada de acerto.

## Configuração local

| Configuração | Padrão | Alteração |
| --- | --- | --- |
| Banco do app | data/reviews.sqlite3 na pasta do projeto | Variável STEAM_SENTIMENT_DB |
| Cache do modelo no app | .venv/hf-cache na pasta do projeto | Variável HF_HOME |
| Banco do runner de persistência | data/reviews.sqlite3 relativo à execução | Opção --db |

Os runners de análise usam o cache padrão do Hugging Face quando HF_HOME não
está definida. Para compartilhar o cache do app:

```powershell
$env:HF_HOME = "$PWD\.venv\hf-cache"
```

Bancos, caches e segredos locais ficam fora do Git. O .gitignore não remove
arquivos que já estejam versionados.

## Execução pelo terminal

```powershell
# Somente coleta, sem modelo ou persistência
.\.venv\Scripts\python.exe manual_runner.py 620 --limit 10 --timeout 15

# Análise de reviews reais
.\.venv\Scripts\python.exe sentiment_runner.py 620 --limit 5

# Duas coletas consecutivas com SQLite
.\.venv\Scripts\python.exe persistence_runner.py 620 --runs 2

# Avaliação de previsões em JSON
.\.venv\Scripts\python.exe evaluation_runner.py
```

O runner de persistência informa recebidas, novas, analisadas, inseridas e total
salvo. A segunda coleta pode conter IDs novos: somente eles serão analisados.
O runner de avaliação aceita um caminho JSON opcional e usa, por padrão,
samples/previous_sentiment_sample.json. Essa amostra contém cinco previsões reais
transcritas da saída do runner, com textos de prévia e confidence arredondado.
Todas têm voted_up=True; ela não mede desempenho na classe negativa.

## Estrutura

| Arquivo | Responsabilidade |
| --- | --- |
| collection.py | Coleta pela API pública da Steam |
| sentiment.py | Inferência de sentimento com Transformers |
| persistence.py | Leitura e gravação no SQLite |
| workflow.py | Coleta incremental, análise e persistência |
| evaluation.py | Métricas e exemplos de discordância |
| dashboard_data.py | Agregação diária e seleção de exemplos |
| app.py | Interface Streamlit |
| *_runner.py | Execução manual de cada fluxo |
| tests/ | Testes unitários e da interface com AppTest |
| samples/ | Amostra reproduzível para avaliação |

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
```

A suíte usa bancos temporários e substitui chamadas externas nos testes.
Não requer baixar o modelo ou consultar a Steam. Os runners manuais de coleta
e inferência exigem rede na primeira execução.
