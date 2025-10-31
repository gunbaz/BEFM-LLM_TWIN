# llm_local.py
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

"""
Hızlı demo için güvenli yükleme:
- Öncelik: ENV LLM_MODEL_ID ile verilen model (varsa)
- Aksi halde: meta-llama/Meta-Llama-3.1-8B-Instruct (gated) dene
- Gated erişim yoksa: TinyLlama/TinyLlama-1.1B-Chat-v1.0 (açık) fallback

Notlar:
- CPU ortamında 8-bit yükleme kapatılır (bitsandbytes GPU gerektirir).
- Model ve tokenizer LAZY (ilk çağrıda) yüklenir, import anında değil.
"""

PRIMARY_MODEL = os.environ.get("LLM_MODEL_ID", "meta-llama/Meta-Llama-3.1-8B-Instruct")
FALLBACK_MODEL = os.environ.get("LLM_FALLBACK_MODEL_ID", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")

LOW_MEM_MODE = True  # GPU varsa 8-bit / yoksa otomatik tam-precision

_tokenizer = None
_model = None


def _can_use_8bit() -> bool:
    """CUDA varsa ve bitsandbytes kurulumu mevcutsa 8-bit deneyebiliriz."""
    try:
        return torch.cuda.is_available()
    except Exception:
        return False


def _hf_token():
    """Hugging Face erişim token'ını ortamdan al (varsa)."""
    return (
        os.environ.get("HUGGINGFACE_HUB_TOKEN")
        or os.environ.get("HF_TOKEN")
        or None
    )


def _load(model_name: str):
    global _tokenizer, _model
    token = _hf_token()
    print(f"[llm_local] Tokenizer yükleniyor: {model_name} (auth={'yes' if token else 'no'})")
    _tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True, token=token)

    print(f"[llm_local] Model yükleniyor: {model_name}")
    if LOW_MEM_MODE and _can_use_8bit():
        # 8-bit quant (CUDA + bitsandbytes gerekli)
        _model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_8bit=True,
            token=token,
        )
    else:
        _model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=(torch.float16 if torch.cuda.is_available() else torch.float32),
            device_map="auto",
            token=token,
        )
    print("[llm_local] Model hazır.")


def _ensure_loaded():
    """Model/Tokenizer yüklü değilse yükle. Gated hata olursa fallback'e geç."""
    global _tokenizer, _model
    if _tokenizer is not None and _model is not None:
        return
    try:
        _load(PRIMARY_MODEL)
    except Exception as e:
        print(f"[llm_local] Uyarı: Birincil model yüklenemedi ({e}). Fallback'e geçiliyor: {FALLBACK_MODEL}")
        _load(FALLBACK_MODEL)


def generate_local_response(prompt: str, max_new_tokens: int = 300) -> str:
    """Prompt -> yerel model -> cevap (Türkçe öncelikli)."""
    _ensure_loaded()

    # instruct format
    full_prompt = (
        "You are a helpful assistant. "
        "Answer the user in Turkish if the user is Turkish.\n\n"
        f"User: {prompt}\n\nAssistant:"
    )

    enc = _tokenizer(full_prompt, return_tensors="pt")
    input_ids = enc["input_ids"].to(_model.device)

    with torch.no_grad():
        output_ids = _model.generate(
            input_ids=input_ids,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
        )

    decoded = _tokenizer.decode(output_ids[0], skip_special_tokens=True)

    # sadece Assistant: sonrası bize lazım
    if "Assistant:" in decoded:
        decoded = decoded.split("Assistant:", 1)[1].strip()

    return decoded.strip()
