# TFG_Elena-Moyano
Multi-agent automated system for error correction in microservices files using n8n orchestration, Chroma RAG, and LLMs

## Description

This system uses a 5-agent workflow in n8n to automatically detect and correct errors in:

- **Python files** (.py)
- **configuration files** (.conf)
- **Docker files** (Dockerfile)
- **Environment files** (.env)

All agents are connected to an LLM, which can be selected depending on the nature of the problem to solve. The agents use Chroma as an internal RAG tool to support the corrections and Serper as an external RAG tool for web search when needed. 

## Technologies

- **n8n** - Workflow orchestration
- **Streamlit** - User interface
- **Chroma + FastAPI** - Vector database
- **Serper** - External search

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/elenaamoyano/TFG_Elena-Moyano.git
cd TFG_Elena-Moyano
```

### 2. Install Node.js

Download and install Node.js 22.x LTS from [nodejs.org](https://nodejs.org)

Verify installation:
```bash
node --version
npm --version
```

### 3. Install n8n globally

```bash
npm install n8n -g
```

### 4. Start n8n

```bash
n8n start
```

Access the web interface at: http://localhost:5678

### 5. Import workflows

- Click 'Create worflow'
- Click '...' -> Import from File
- Select the workflow JSON files from /n8n_workflows/

### 6. Configure credentials

In n8n Personal panel, go to Credentials → Create Credential and add:
- OpenRouter API Key (for LLMs)
- Serper API Key

### 7. Start Chroma API

```bash
cd chroma-api
pip install -r requirements.txt
python main.py
```

### 8. Start Streamlit UI

```bash
cd streamlit-ui
pip install -r requirements.txt
streamlit run app.py
```

### System requirements

| Requirement | Version |
|-------------|---------|
| Node.js | 20.x or 22.x LTS |
| Python | 3.12+ |
| npm | Included with Node.js |
| Ports | 5678 (n8n), 8001 (Chroma), 8501 (Streamlit) |
