ERROR_ANALYSIS_PROMPT = (
    "Analyse this code, find every bug, logic issue, and risky pattern. "
    "Return exact line references, short cause, and short fix only.\n\n{input}"
)

EXPLAIN_CODE_PROMPT = (
    "Explain this code simply, line by line, for a beginner. "
    "Keep it clear and structured.\n\n{input}"
)

WRITE_CODE_PROMPT = (
    "Write complete working clean code for this request. "
    "Stay practical, Termux-friendly, and include only code plus very short notes.\n\n{input}"
)

ANALYZE_TASK_PROMPT = (
    "Analyze this software task and return: understanding, risks, suggested plan, and verification checklist. "
    "Keep it concise and actionable.\n\n{input}"
)

DEBUG_PROMPT = (
    "Debug this issue end-to-end and return: root cause, exact fix steps, and verification checklist. "
    "Be concise and practical.\n\n{input}"
)

EDIT_FILE_PROMPT = (
    "You are applying an edit to a single file. Return only the full updated file content. "
    "No markdown fences, no explanations.\n\n"
    "Target path: {path}\n"
    "Edit request: {instruction}\n\n"
    "Current content:\n{current_content}"
)

RESTRUCTURE_PROMPT = (
    "Propose a clean folder structure and file naming convention for this project. "
    "Return a tree first, then short notes.\n\n{input}"
)

RECOVERY_PROMPT = (
    "AIDE-like recovery: reconstruct clean buildable source code from this broken or partial input. "
    "Fix imports and restore structure.\n\n{input}"
)

TERMUX_PROMPT = (
    "You are a Termux and Trimix expert. Give ready-to-run commands, balanced steps, and short explanations.\n\n{input}"
)

CHILD_BOT_PROMPT = (
    "Generate a single-file Python Telegram bot using telebot. "
    "Load TELEGRAM_BOT_TOKEN from environment, deny unauthorized users, and keep handlers short. "
    "Return Python code only.\n\n{input}"
)
