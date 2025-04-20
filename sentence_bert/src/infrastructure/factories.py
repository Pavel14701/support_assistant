from transformers import T5Tokenizer, T5EncoderModel

from sentence_bert.src.config import BertConfig

async def get_model(config: BertConfig) -> T5EncoderModel: 
    return T5EncoderModel.from_pretrained(config.model_name)

async def get_tokenizer(config: BertConfig) -> T5Tokenizer:
    return T5Tokenizer.from_pretrained(config.model_name)