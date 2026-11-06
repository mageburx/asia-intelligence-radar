# Asia Intelligence Radar — 7 países

Bot **independente** de vigilância noticiosa: política e indústria automóvel (China, Japão, Alemanha, Coreia do Sul, Taiwan, Índia e Singapura), leitura horária de RSS público, traduções automáticas para português ou inglês e dashboard responsivo hospedável no GitHub Pages.

## O que faz

- 20 fontes/consultas, incluindo RSS original chinês (China News Service), japonês (NHK Política e Car Watch), imprensa especializada chinesa (CarNewsChina, CnEVPost) e pesquisa RSS por edições regionais e idiomas locais via Google News (DE/KR/TW/IN/SG).
- Recolha de **títulos, excertos RSS, autor/publicação, datas e URLs**. Não descarrega artigos completos nem contorna paywalls / CAPTCHAs.
- Deduplicação por URL/categoria/país; retenção de 60 dias. Armazenamento JSON para facilitar o MVP.
- Tradução dos **títulos e excertos** para `pt` (padrão) ou `en`; o original fica acessível no dashboard. Tradução grátis experimental via MyMemory (limitada por quota partilhada) e, opcionalmente, DeepL API. Se a tradução falhar, exibe claramente o original com estado pendente e tenta novamente passadas 6 horas.
- Dashboard HTML estático, sem servidor e com pesquisa, filtros de país/tema/tempo, números de notícias e tópicos em crescimento.
- Cron GitHub Actions `17 * * * *` (todos os dias, 24 vezes/dia, 17 minutos após cada hora, UTC), com execução manual por botão.

## Configuração do repositório GitHub

O projeto já foi instalado em **https://github.com/mageburx/asia-intelligence-radar** e a primeira execução do GitHub Actions foi validada.

Para publicar o dashboard, vai a **Settings → Pages → Build and deployment**, escolhe **Deploy from a branch**, seleciona `main` e `/docs`, e guarda. O endereço esperado, depois da publicação, será **https://mageburx.github.io/asia-intelligence-radar/**.

Para consultar a execução, abre **Actions → Asia Intelligence Radar**. Para iniciar manualmente, usa **Run workflow**.

### Escolher idioma

Por predefinição, a tradução é PT. Para inglês: **Settings → Secrets and variables → Actions → Variables → New repository variable**: `TARGET_LANG` = `en`. `pt` = português; `en` = inglês.

### Tradução com maior fiabilidade (opcional)

A tradução gratuita via MyMemory tem uma quota anónima reduzida (5 000 caracteres/dia, partilhada pelo IP). Para aumentar a quota até 50 000 caracteres/dia, podes adicionar um email válido como secret opcional `MYMEMORY_EMAIL`, conforme as condições do fornecedor. Mesmo assim, a disponibilidade não é garantida. Para maior estabilidade, configura **Settings → Secrets and variables → Actions → Secrets → New repository secret** com `DEEPL_API_KEY`. Usa uma chave DeepL API da tua conta e confirma preços/limites. O código presume o endpoint Free (`https://api-free.deepl.com/v2/translate`); se tiveres plano Pro, configura `DEEPL_API_URL` no ambiente para `https://api.deepl.com/v2/translate` (requer ajustar o workflow para passar essa variável).

O idioma da tradução é `PT-PT` ou `EN-GB` no DeepL. Não traduz conteúdos de artigos com direitos de autor, apenas títulos e excertos RSS. Quando alterares `TARGET_LANG`, o bot retraduz gradualmente os itens guardados, sujeito ao limite por execução.

## Execução local

Precisas de Python 3.11 ou superior.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m asia_radar.collector
python -m asia_radar.report
```

Abre `docs/index.html` diretamente no navegador. Para mudar o idioma numa sessão local:

```bash
# macOS/Linux
TARGET_LANG=en python -m asia_radar.collector
# Windows PowerShell
$env:TARGET_LANG="en"; python -m asia_radar.collector
```

## Política de fontes, qualidade e limites

- As pesquisas de RSS `Google News` são agregadores por idioma/país de consulta. **Não provam que o artigo foi publicado fisicamente nos países monitorizados.** Os feeds nativos dão uma ligação mais direta à imprensa local.
- As contagens medem só cobertura das fontes escolhidas. Não são medidas de vendas, audiência, impacto económico ou factualidade; não identificam automaticamente quem iniciou uma tendência.
- Nos primeiros 48 h de recolha, os sinais recebem a etiqueta `Histórico inicial`, pois ainda não há base comparativa suficiente.
- As etiquetas `Tema emergente` e `Cobertura crescente` exigem várias menções recentes de pelo menos dois publicadores distintos; ainda assim, podem ser republicações/agências da mesma peça original.
- A classificação por tema é baseada em **palavras-chave** e pode falhar. A política é apresentada factualmente sem análise de sentimento, opinião política nem previsão eleitoral.
- Os feeds podem alterar URL, bloquear pedidos ou deixar de publicar. O dashboard apresenta quantas fontes falharam e o histórico de recolha.
- GitHub Actions usa cron **não garantido ao minuto**, pois execuções podem atrasar ou, em casos raros, ser omitidas. Em repositórios públicos inativos, os workflows agendados podem ser desativados após 60 dias sem atividade.
- Sem dados reais de histórico, o painel inicia vazio. Não são inseridas notícias fictícias.
- Repositório **público significa que o histórico de títulos/excertos e o dashboard serão públicos**. Não inclua segredos em ficheiros versionados.
- O armazenamento JSON em commits horários é adequado a uma experiência inicial, não a uma operação de larga escala. Para produção, migrar para PostgreSQL/SQLite externo com backups, observabilidade e alertas.

## Estrutura

```text
asia_radar/core.py            # texto, tópicos, deduplicação e tendências
asia_radar/collector.py       # RSS, histórico e traduções
asia_radar/report.py          # relatório HTML offline
config/sources.json           # 20 fontes e pesquisas
.github/workflows/hourly.yml  # GitHub Actions / 1 hora
data/articles.json            # notícias recolhidas (inicia vazio)
data/status.json              # estado de saúde das fontes
docs/index.html               # dashboard para GitHub Pages
tests/test_core.py            # testes sem rede
```

## Próximos passos recomendados

Alertas para acontecimentos específicos (por exemplo BYD, Toyota, baterias, tarifas), agrupamento de várias notícias sobre o mesmo evento, deteção de novos termos e exportação de briefings diários. A versão inicial é intencionalmente simples, auditável e de baixo custo. As 10 fontes foram acessíveis na primeira execução; isto não garante que todos os artigos sejam relevantes ou que os fornecedores mantenham disponibilidade permanente.

## Expansão de países (novembro de 2026)

Acrescentados **Alemanha, Coreia do Sul, Taiwan, Índia e Singapura**, mantendo China e Japão. As duas categorias são **Política** e **Automóvel** para todos os sete países. As dez novas fontes são pesquisas de Google News com edição regional e termos orientados para cada mercado (não são jornais nativos de origem verificada); o histórico é preenchido a partir da primeira recolha. Detetar língua de origem por escrita é aproximado: a tradução pode ficar pendente devido às quotas gratuitas. Os novos países requerem até 48 horas de histórico para que o sinal deixe de ser preliminar.
