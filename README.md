# Natural Language to SQL Assistant

A powerful application that converts natural language queries into SQL and executes them on a database, featuring a clean Streamlit interface and powered by open-source LLMs.

## 🚀 Features

- Natural language to SQL conversion using Mistral-7B (or similar) model
- Interactive Streamlit UI for query input and result visualization
- Support for SQLite (with extensibility for MySQL)
- Dynamic schema reading and SQL generation
- Result visualization in tables and charts
- Error handling and query validation

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI
- **LLM**: Mistral-7B (via HuggingFace)
- **Database**: SQLite (with MySQL support planned)
- **ORM**: SQLAlchemy
- **Frontend**: Streamlit
- **Additional**: Pandas, Transformers, PyTorch

## 📋 Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended for LLM inference)
- 16GB+ RAM (recommended)

## 🚀 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd nlp-to-sql-assistant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🎮 Usage

1. Start the application:
```bash
streamlit run gui/streamlit_app.py
```

2. Open your browser and navigate to the provided Streamlit URL (typically http://localhost:8501)

3. Enter your natural language query in the text input field

4. View the generated SQL and results in the interface

## 📁 Project Structure

```
project_root/
├── app/
│   ├── main.py              # FastAPI backend
│   ├── models/              
│   │   └── mistral_model.py # LLM model handling
│   ├── services/
│   │   ├── sql_generator.py # SQL generation logic
│   │   └── schema_reader.py # Database schema handling
│   └── utils/
│       └── db.py           # Database utilities
├── gui/
│   └── streamlit_app.py    # Streamlit interface
├── prompts/
│   └── generate_sql.txt    # LLM prompt template
├── data/
│   └── sample.db          # Sample SQLite database
├── requirements.txt
└── README.md
```

## 🔧 Configuration

The application uses environment variables for configuration. Create a `.env` file in the root directory with:

```env
MODEL_NAME=mistralai/Mistral-7B-v0.1
DATABASE_URL=sqlite:///data/sample.db
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Notes

- The application requires significant computational resources for LLM inference
- Initial setup may take time to download the model
- For production use, consider using a more optimized model or deployment strategy 