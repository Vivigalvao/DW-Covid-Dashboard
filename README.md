# 🦠 COVID-19 ES — Dashboard Streamlit

Dashboard de análise de notificações de COVID-19 do estado do Espírito Santo, construído com **Streamlit** e hospedado via **Supabase + Streamlit Cloud**.

## 📊 Funcionalidades

| Aba | Conteúdo |
|-----|----------|
| **Visão Geral** | KPIs (notificações, confirmados, óbitos, curados, internações), evolução mensal, semana epidemiológica |
| **Geografia** | Top 20 municípios, distribuição por macrorregião, taxa de letalidade |
| **Perfil do Paciente** | Por sexo, faixa etária, raça/cor, populações especiais |
| **Clínico** | Sintomas, comorbidades, classificação, evolução, testes, tempos médios |

## 🏗️ Stack

- **Frontend**: Streamlit
- **Banco de dados**: PostgreSQL via Supabase
- **Visualizações**: Plotly
- **Deploy**: Streamlit Community Cloud (GitHub)

## 🚀 Executar Localmente

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar credenciais
Copie o template de secrets:
```bash
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```
Edite `.streamlit/secrets.toml` com as credenciais reais do Supabase.

### 3. Rodar o app
```bash
streamlit run streamlit_app.py
```

## ☁️ Deploy no Streamlit Cloud

1. Faça fork/push deste repositório para o GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Clique em **New app** → selecione o repo e `streamlit_app.py`
4. Em **Advanced settings → Secrets**, cole o conteúdo de `.streamlit/secrets.toml.example` com os valores reais
5. Clique em **Deploy**

## 🔒 Segurança

- O arquivo `.streamlit/secrets.toml` está no `.gitignore` e **nunca** deve ser commitado
- As credenciais são gerenciadas pelo Streamlit Cloud Secrets Manager (criptografadas)

## 📁 Estrutura do Projeto

```
dw_covid_dashboard/
├── streamlit_app.py               # App principal
├── requirements.txt               # Dependências Python
├── .gitignore                     # Ignora secrets e arquivos temporários
├── .streamlit/
│   └── secrets.toml.example       # Template de credenciais (seguro para commit)
└── README.md
```

## 🗄️ Fonte dos Dados

- **DW**: `dw_covid` (PostgreSQL local → Supabase)
- **Schema**: `dw` (star schema com fact table `fato_notificacao_covid`)
- **Origem**: SESA-ES — Secretaria de Estado de Saúde do Espírito Santo
