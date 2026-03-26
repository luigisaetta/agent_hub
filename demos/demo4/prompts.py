"""
Author: L. Saetta
Last modified: 2026-03-26
License: MIT

Description:
    Prompt definitions for Demo 4 RAG flow.
"""

from textwrap import dedent

# dedent+strip keeps the prompt readable in source code without sending
# indentation/newline artifacts to the model.
STRICT_INSTRUCTIONS = dedent(
    """
    Answer using only information from the retrieved documents.
    You may summarize or synthesize information that is explicitly supported by
    the retrieved text.
    Do not use outside knowledge.
    If the retrieved documents do not contain enough information to answer, say
    exactly: 'I don't have sufficient information in the documents.'
    """
).strip()
