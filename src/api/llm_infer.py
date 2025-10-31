# llm_infer.py
from .llm_local import generate_local_response

def generate_answer(prompt: str) -> str:
    """
    Persona prompt'u alır, lokal Llama modelinden cevap üretir.
    """
    return generate_local_response(prompt)
