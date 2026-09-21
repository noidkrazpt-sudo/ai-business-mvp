# AI Business MVP

Este projeto cria hoje um sistema local com agentes especializados para um negócio
global, em inglês, dirigido a pequenas empresas. Não envia mensagens, faz compras
ou movimenta dinheiro automaticamente: todos os resultados ficam em estado
`needs_review` para aprovação humana.

## Arranque

Requer Python 3.10+ e não precisa de instalar pacotes:

```powershell
python .\agent_business.py init
python .\agent_business.py research
python .\agent_business.py offer --service "AI lead follow-up setup"
python .\agent_business.py content --offer "AI lead follow-up setup"
python .\agent_business.py leads --companies '[{"company":"Example Co","website":"https://example.com","problem":"No clear contact follow-up"}]'
python .\agent_business.py suppliers --candidates '[{"name":"Supplier","url":"https://supplier.example","product":"Desk organizer"}]'
python .\agent_business.py delivery --client "Example Co" --items "Audit,Workflow,Training"
python .\agent_business.py analytics
```

O ficheiro `business_data.json` é criado localmente e não deve ser publicado.

## IA opcional

Para usar um modelo compatível com a API OpenAI, define `OPENAI_API_KEY` e,
opcionalmente, `OPENAI_MODEL`. Sem chave, o sistema usa modelos locais de fallback
para permitir validar o fluxo sem custos.

## Agentes

- `MarketResearchAgent`: problemas e oportunidades.
- `OfferAgent`: oferta, escopo e preço de teste.
- `ContentAgent`: conteúdo e rascunho de outreach.
- `LeadResearchAgent`: normalização de leads fornecidos pelo utilizador.
- `SupplierAgent`: organização de candidatos a fornecedores.
- `DeliveryAgent`: checklist de entrega.
- `AnalyticsAgent`: métricas do CRM local.

Para funcionamento 24/7, este MVP deve ser colocado posteriormente num servidor
com agendamento, logs, limites e alertas. Não se recomenda ativar envio de
outreach, encomendas ou pagamentos sem revisão humana.
