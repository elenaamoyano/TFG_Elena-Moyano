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

