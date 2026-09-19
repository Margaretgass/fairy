from langchain_ollama import ChatOllama

from fairy.prompts import NEUROFAIRY_SYSTEM_PROMPT

MODEL_NAME = "qwen2.5:3b"

model = ChatOllama(
    model=MODEL_NAME,
    temperature=0.3,
)


def reply_to_user(message: str) -> str:
    response = model.invoke(
        [
            ("system", NEUROFAIRY_SYSTEM_PROMPT),
            ("human", message),
        ]
    )

    return str(response.content)
