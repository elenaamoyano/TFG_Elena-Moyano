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

Download Node.js 22.x LTS from [nodejs.org](https://nodejs.org)

**Windows:**
1. Double-click the downloaded `.msi` file (Windows Installer)
2. Click "Next" through the installation wizard
3. Accept the license agreement
4. Leave default installation path (`C:\Program Files\nodejs`)
5. Click "Install" and then "Finish"
6. **Restart your terminal** 

**Linux:**
1. Extract the downloaded archive:
```bash
tar -xzf node-v22.22.3-linux-x64.tar.gz -C ~/
```
2. Edit ~/.bashrc to add Node.js to PATH:
```bash
nano ~/.bashrc
```
3. Add this line at the end of the file:
```bash
export PATH="$HOME/node-v22.22.3-linux-x64/bin:$PATH"
```
4. Save and exit.
5. Apply the changes:
```bash
source ~/.bashrc
```

**macOS:**
1. Double-click the downloaded `.pkg` file (Apple package)
2. Click "Continue" through the installation wizard
3. Accept the license agreement
4. Leave default installation path
5. Click "Install" (may require your system password)
6. Click "Close" when finished
7. **Restart your terminal** 

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

Access the web interface at: http://localhost:5678 and create an account

### 5. Import workflows

- Click 'Create worflow'
- Click '...' -> Import from File
- Select the workflow JSON files from /n8n_workflows/

complete_system.json contains the full multi-agent system. The rest of the workflows were used only for evaluation during benchmark testing.

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
Access the web interface at: http://127.0.0.1:8001/docs#

Import all solutions for each collection
```bash
cd ..
python load_all_collections.py
```

You can review this in the GET/collections section of the interface. Click 'Try it out' and 'Execute'.

### 8. Start Streamlit UI

```bash
cd streamlit-ui
pip install -r requirements.txt
streamlit run app.py
```
Access the web interface at: http://localhost:8501/

### 🛠️ Possible Issue: `streamlit: command not found`

If after installing the dependencies with:

```bash
pip install -r requirements.txt
```

the `streamlit` command is not recognized, it is likely that it was installed in the user site directory (`--user install`), which is not always included in the `PATH`.

---

### Check installation

Try running it directly:

```bash
~/.local/bin/streamlit --version
```

If it works, you can run the app using:

```bash
~/.local/bin/streamlit run app.py
```

### System requirements

| Requirement | Version |
|-------------|---------|
| Node.js | 20.x or 22.x LTS |
| Python | 3.12+ |
| npm | Included with Node.js |
| Ports | 5678 (n8n), 8001 (Chroma), 8501 (Streamlit) |
