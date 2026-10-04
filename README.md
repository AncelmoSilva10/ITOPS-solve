# Case ITOps: Data Lake na AWS

Repositório do case prático de **Sistemas Operacionais** para a construção de um **Data Lake na AWS**, focado na análise de tráfego de rede corporativa.

O projeto simula a coleta de logs provenientes de **Access Points** e de um **Firewall**, processando os dados na nuvem para extrair informações relevantes para análise e tomada de decisão.

## 🏗️ Estrutura do Data Lake

O Data Lake é organizado em três camadas utilizando o **Amazon S3**:

### 🥉 Bronze — Raw

Responsável pela **ingestão e armazenamento dos dados brutos** de rede.

- Recebe dados no formato **JSON**;
- Os dados são coletados a cada minuto;
- Mantém os dados em seu formato original;
- Serve como fonte para as etapas posteriores de processamento.

### 🥈 Silver — Trusted

Responsável pelo **tratamento, padronização e consolidação dos dados**.

- Utiliza instâncias **AWS EC2**;
- Processamento realizado com **Python** e `pandas`;
- Limpeza e padronização dos dados;
- Consolidação das métricas;
- Cruzamento das informações provenientes dos **Access Points** e do **Firewall**;
- Geração de arquivos estruturados em **CSV**.

### 🥇 Gold — Analytics

Responsável pela disponibilização dos **dados analíticos** para apoiar a governança e a tomada de decisões.

## 🛠️ Principais Tecnologias

- ☁️ **AWS S3** — armazenamento e organização do Data Lake;
- 💻 **AWS EC2** — ambiente para processamento dos dados;
- ⚙️ **AWS CLI** — gerenciamento e interação com os recursos da AWS;
- 🐍 **Python** — desenvolvimento dos scripts de processamento;
- 🐼 **Pandas** — manipulação e transformação dos dados;
- 🔗 **Boto3** — integração entre Python e os serviços da AWS.

## 📂 Arquitetura

```text
                 ┌─────────────────────┐
                 │   Access Points     │
                 └──────────┬──────────┘
                            │
                            │ JSON
                            ▼
                 ┌─────────────────────┐
                 │      🥉 Bronze      │
                 │      AWS S3         │
                 │     Dados Raw       │
                 └──────────┬──────────┘
                            │
                            │ Processamento
                            ▼
                 ┌─────────────────────┐
                 │      🥈 Silver      │
                 │   AWS EC2 + Python │
                 │       Pandas        │
                 └──────────┬──────────┘
                            │
                            │ Dados tratados
                            ▼
                 ┌─────────────────────┐
                 │       🥇 Gold       │
                 │      AWS S3         │
                 │     Analytics       │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     Governança      │
                 │  e tomada de decisão│
                 └─────────────────────┘
