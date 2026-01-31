# Hola-Dermat - Personalized Skincare Assistant

A Streamlit-based chat application that provides personalized skincare recommendations using CrewAI agents, Qdrant vector database, and Perplexity search.

## Features

- **Interactive Chat Interface**: Natural conversation flow to understand user's skin type, region, lifestyle, and needs
- **Intelligent Agent System**: CrewAI-powered agent that researches weather conditions, product availability, and user history
- **Vector Database**: Qdrant with ACORN algorithm for efficient product and history search
- **Personalized Recommendations**: Morning and night skincare regimens tailored to individual needs

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```
ANTHROPIC_API_KEY=your_claude_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### 3. Ingest Product Data

Before running the app, populate the Qdrant database with products:

```bash
python data/ingest_products.py
```

**Note:** The Qdrant vector database is stored on disk in the `vectordb/` directory. This directory will be created automatically when you first run the ingestion script or the application. The database persists between sessions, so you only need to ingest products once (unless you want to re-ingest or update the product data).

### 4. Run the Application

```bash
streamlit run app.py
```

## Usage

1. Start a conversation with the assistant
2. Answer questions about your skin type, region, lifestyle, etc.
3. Receive personalized morning and night skincare regimen recommendations
4. Provide feedback on products to improve future recommendations

## Project Structure

- `app.py` - Main Streamlit application
- `agents/` - CrewAI agent configuration and tools
- `database/` - Qdrant client and collection setup
- `data/` - Product data and ingestion scripts
- `utils/` - Chat management and user profile utilities
- `config/` - Configuration management

## Technologies

- **Streamlit**: Chat interface
- **CrewAI**: Agent orchestration
- **Qdrant v1.16+**: Vector database with ACORN algorithm for intelligent filtering
- **Claude Sonnet 4.5**: LLM for agentic workflows
- **Perplexity**: Weather and product research
- **Sentence Transformers**: Embeddings for vector search

## Key Features

### ACORN Algorithm Integration
The application uses Qdrant's ACORN (Algorithm for Complex OR-query Navigation) algorithm from v1.16+, which solves the "zero results" problem when applying multiple filters simultaneously. This ensures that even with complex queries combining skin type, region availability, ingredient requirements, and usage timing, the system can find relevant products.

### Intelligent Agent Workflow
The CrewAI agent intelligently decides when to use:
- **Perplexity Search**: For real-time weather data, regional product research, and environmental analysis
- **Qdrant Vector Search**: For product matching, user history retrieval, and semantic product discovery

### User History Tracking
All user interactions, product recommendations, and feedback are stored in Qdrant's history collection, allowing the agent to learn from past interactions and provide increasingly personalized recommendations.

### Persistent Storage
The Qdrant vector database is stored on disk in the `vectordb/` directory, ensuring that product data and user history persist between application sessions. This means you don't need to re-ingest products every time you restart the application.
