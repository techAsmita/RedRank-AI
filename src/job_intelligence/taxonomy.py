"""
taxonomy.py
-----------

Central taxonomy for technical skills.

The parser never hardcodes skill names.

Instead it asks this module.

Example

FAISS

↓

Retrieval

↓

Information Retrieval

Everything should be reusable.
"""

from __future__ import annotations


# ---------------------------------------------------------------------
# Skill Categories
# ---------------------------------------------------------------------

SKILL_TAXONOMY: dict[str, list[str]] = {

    # -------------------------------------------------------------
    # Programming
    # -------------------------------------------------------------

    "python": [
        "python",
        "django",
        "fastapi",
        "flask",
    ],

    # -------------------------------------------------------------
    # LLM
    # -------------------------------------------------------------

    "llm": [
        "openai",
        "gpt",
        "claude",
        "gemini",
        "llama",
        "ollama",
        "anthropic",
    ],

    # -------------------------------------------------------------
    # Agent Frameworks
    # -------------------------------------------------------------

    "agent_frameworks": [
        "langchain",
        "langgraph",
        "llamaindex",
        "autogen",
        "crewai",
        "semantic kernel",
    ],

    # -------------------------------------------------------------
    # Retrieval
    # -------------------------------------------------------------

    "retrieval": [
        "rag",
        "retrieval",
        "faiss",
        "pinecone",
        "chroma",
        "chromadb",
        "weaviate",
        "milvus",
        "elasticsearch",
        "bm25",
    ],

    # -------------------------------------------------------------
    # Evaluation
    # -------------------------------------------------------------

    "evaluation": [
        "ragas",
        "evaluation",
        "eval",
        "evaluating",
        "evaluation framework",
        "benchmark",
        "judge",
        "hallucination",
    ],

    # -------------------------------------------------------------
    # MLOps
    # -------------------------------------------------------------

    "mlops": [
        "mlflow",
        "kubeflow",
        "airflow",
        "docker",
        "kubernetes",
        "wandb",
        "weights & biases",
    ],

    # -------------------------------------------------------------
    # Cloud
    # -------------------------------------------------------------

    "cloud": [
        "aws",
        "azure",
        "gcp",
    ],

    # -------------------------------------------------------------
    # Data
    # -------------------------------------------------------------

    "data_engineering": [
        "spark",
        "hadoop",
        "kafka",
        "airflow",
        "snowflake",
    ],

    # -------------------------------------------------------------
    # ML
    # -------------------------------------------------------------

    "machine_learning": [
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "xgboost",
        "lightgbm",
    ],

    # -------------------------------------------------------------
    # Search
    # -------------------------------------------------------------

    "search": [
        "lucene",
        "elasticsearch",
        "solr",
    ],
}


# ---------------------------------------------------------------------
# Reverse Index
# ---------------------------------------------------------------------

SKILL_TO_CATEGORY: dict[str, str] = {}

for category, skills in SKILL_TAXONOMY.items():
    for skill in skills:
        SKILL_TO_CATEGORY[skill.lower()] = category


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def get_category(skill: str) -> str | None:
    """
    Return the taxonomy category for a skill.

    Example

    FAISS -> retrieval

    Docker -> mlops
    """

    return SKILL_TO_CATEGORY.get(skill.lower())


def all_known_skills() -> set[str]:
    """
    Return every known skill.
    """

    return set(SKILL_TO_CATEGORY.keys())