# Portfolio RAG Evaluation Tool

A comprehensive RAG (Retrieval-Augmented Generation) testing and evaluation tool for portfolio applications. This tool tests the entire RAG pipeline including document retrieval from vector databases and answer generation using LLMs.

## Features

- Vector similarity search using Cohere embeddings
- Document retrieval from AstraDB vector database
- Answer generation using Groq API (Llama 3.3 70B)
- Batch query testing with detailed performance metrics
- Comprehensive reporting with JSON and readable text formats
- Response time tracking and retrieval score analysis

## Prerequisites

- Python 3.8+
- AstraDB account and database
- Cohere API key(s)
- Groq API key(s)

## Installation

1. Clone the repository with submodules:
```bash
git clone --recurse-submodules <your-repo-url>
cd learn
```

Or if you already cloned it:
```bash
git clone <your-repo-url>
cd learn
git submodule update --init --recursive
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Copy `.env.sample` to `.env`
   - Fill in your actual API keys and credentials

```bash
cp .env.sample .env
```

## Configuration

Edit the `.env` file with your credentials:

- `ASTRA_DB_APPLICATION_TOKEN`: Your AstraDB application token
- `ASTRA_DB_API_ENDPOINT`: Your AstraDB API endpoint URL
- `ASTRA_DB_NAMESPACE`: Database keyspace (default: default_keyspace)
- `COHERE_API_KEY_1`, `COHERE_API_KEY_2`: Cohere API keys for embeddings
- `GROQ_API_KEY_1`, `GROQ_API_KEY_2`: Groq API keys for LLM generation
- `NEON_DATABASE_URL`: PostgreSQL connection string (if using Neon)

## Usage

1. The test queries are located in the submodule (`portfolio-data/portfolio_evaluation_queries.json`). You can edit this file to add or modify test queries:
```json
[
  {
    "query": "What are Srikanth's key skills?"
  },
  {
    "query": "Tell me about Srikanth's work experience"
  }
]
```

2. Run the evaluation:
```bash
python rag-eval-data.py
```

3. Check results in the `rag_results/` directory:
   - `evaluation_results_<timestamp>.json`: Detailed JSON results
   - `readable_report_<timestamp>.txt`: Human-readable report

## Project Structure

```
.
├── rag-eval-data.py              # Main RAG testing script
├── portfolio-data/               # Git submodule with portfolio data
│   ├── ai-portfolio.json         # Portfolio knowledge base
│   └── portfolio_evaluation_queries.json  # Test queries
├── rag_results/                  # Generated test results
├── index.ipynb                   # Jupyter notebook (if applicable)
├── .env                          # Environment variables (not in git)
├── .env.sample                   # Sample environment file
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
├── .gitmodules                   # Git submodule configuration
└── README.md                     # This file
```

## Submodule Information

This project uses a git submodule for the portfolio data:
- **Repository**: https://github.com/srikanth-karthi/portfolio-data
- **Contains**:
  - `ai-portfolio.json` - the knowledge base for the portfolio
  - `portfolio_evaluation_queries.json` - test queries for evaluation

To update the submodule to the latest version:
```bash
git submodule update --remote portfolio-data
```

## How It Works

1. **Initialization**: Connects to AstraDB vector database and initializes Cohere/Groq clients
2. **Query Processing**: For each query:
   - Generates query embedding using Cohere
   - Retrieves top-k similar documents from AstraDB
   - Generates answer using Groq LLM with retrieved context
3. **Evaluation**: Tracks response times, retrieval scores, and success rates
4. **Reporting**: Generates detailed reports in JSON and text formats

## Output Metrics

The tool tracks and reports:
- Total queries tested
- Success/failure rates
- Average response time
- Average retrieval scores
- Individual query results with full context
- Error details for failed queries

## Example Output

```
OVERALL STATISTICS
--------------------------------------------------------------------------------
  Total Queries:        10
  Successful:           10
  Failed:               0
  Success Rate:         100.0%
  Avg Response Time:    1.234s
  Avg Top Retrieval:    0.856
```

## Troubleshooting

- **Connection errors**: Verify your API keys and endpoints in `.env`
- **Rate limits**: The tool includes built-in delays and key rotation
- **Empty results**: Check that your vector database collection is populated
- **Module not found**: Ensure all dependencies are installed with `pip install -r requirements.txt`

## Security Notes

- Never commit the `.env` file to version control
- Keep your API keys secure and rotate them regularly
- Use environment variables for all sensitive data

## License

[Add your license here]

## Contact

[Add your contact information here]
