import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

model_name = "ai4bharat/indictrans2-en-indic-dist-200M"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForSeq2SeqLM.from_pretrained(
    model_name,
    trust_remote_code=True
).to(DEVICE)


def translate(text, src_lang="hin_Deva", tgt_lang="eng_Latn"):
    input_text = f"{src_lang} {tgt_lang} {text}"

    inputs = tokenizer(input_text, return_tensors="pt").to(DEVICE)

    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=256)

    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return result