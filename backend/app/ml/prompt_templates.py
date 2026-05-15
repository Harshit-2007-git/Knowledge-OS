"""
RAG prompt templates for different LLM models and use cases.

Templates use Python string formatting for injection safety
and support multiple prompt styles.
"""


# ── System Prompts ───────────────────────────────────────────

SYSTEM_PROMPT = """You are a knowledgeable AI assistant for the Knowledge OS platform.
You help users understand and analyze their documents.
You MUST base your answers on the provided context.
If the context does not contain relevant information, say so clearly.
Always cite your sources using [Source N] notation."""


# ── RAG Prompt Templates ────────────────────────────────────

RAG_PROMPT_TEMPLATE = """Answer the user's question based on the following context from their documents.

## Context
{context}

## Instructions
- Answer based ONLY on the context provided above.
- If the context doesn't contain enough information, explicitly state that.
- Cite specific sources using [Source N] notation (e.g., [Source 1], [Source 2]).
- Be concise but thorough.
- Use markdown formatting for readability.

## User Question
{question}

## Answer"""


RAG_PROMPT_WITH_HISTORY = """Answer the user's question based on the context and conversation history.

## Context from Documents
{context}

## Conversation History
{history}

## Instructions
- Answer based ONLY on the document context provided above.
- Consider the conversation history for context continuity.
- If the context doesn't contain enough information, explicitly state that.
- Cite specific sources using [Source N] notation.
- Be concise but thorough.

## User Question
{question}

## Answer"""


# ── Context Formatting ───────────────────────────────────────

def format_context(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a context string for prompt injection.

    Args:
        chunks: List of chunk dicts with 'content', 'document_name', 'page_number'.

    Returns:
        Formatted context string with source annotations.
    """
    if not chunks:
        return "No relevant context found."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("document_name", "Unknown")
        page = chunk.get("page_number")
        page_info = f", Page {page}" if page else ""
        context_parts.append(
            f"[Source {i}] ({source}{page_info}):\n{chunk['content']}"
        )

    return "\n\n---\n\n".join(context_parts)


def format_chat_history(messages: list[dict], max_messages: int = 10) -> str:
    """
    Format recent conversation history for context.

    Args:
        messages: List of message dicts with 'role' and 'content'.
        max_messages: Maximum number of recent messages to include.

    Returns:
        Formatted history string.
    """
    recent = messages[-max_messages:]
    parts = []
    for msg in recent:
        role = msg["role"].capitalize()
        parts.append(f"{role}: {msg['content']}")
    return "\n".join(parts)


def build_rag_prompt(
    question: str,
    chunks: list[dict],
    history: list[dict] | None = None,
) -> str:
    """
    Build a complete RAG prompt.

    Args:
        question: User's question.
        chunks: Retrieved context chunks.
        history: Optional conversation history.

    Returns:
        Complete prompt string ready for LLM.
    """
    context = format_context(chunks)

    if history:
        formatted_history = format_chat_history(history)
        return RAG_PROMPT_WITH_HISTORY.format(
            context=context,
            history=formatted_history,
            question=question,
        )

    return RAG_PROMPT_TEMPLATE.format(
        context=context,
        question=question,
    )
