import re
import torch
from transformers import BertTokenizerFast, BertForTokenClassification
import warnings
from transformers import logging as transformers_logging
import os
import gc

warnings.filterwarnings('ignore')
transformers_logging.set_verbosity_error()

# Global variables to avoid reloading
_model = None
_tokenizer = None
_device = None

def clear_memory():
    """Clear GPU/CPU memory and run garbage collection"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()

def load_model_lazy(model_path="compressed_resume_ner_model_v2.pt"):
    """Load model and tokenizer only when needed"""
    global _model, _tokenizer, _device
    
    if _model is not None:
        return _model, _tokenizer, _device
    
    # Define labels
    unique_labels = ['COLLEGE NAME', 'COMPANY', 'DEGREE', 'DESIGNATION', 'EMAIL', 'LOCATION', 'NAME', 'SKILLS']
    labels = ['O'] + [f'B-{label}' for label in unique_labels] + [f'I-{label}' for label in unique_labels]
    label2id = {label: i for i, label in enumerate(labels)}
    id2label = {i: label for i, label in enumerate(labels)}
    
    # Force CPU usage to save memory
    _device = torch.device('cpu')
    
    # Load tokenizer
    _tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased')
    
    # Check model exists
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    
    # Load model with memory optimization
    _model = BertForTokenClassification.from_pretrained(
        'bert-base-uncased',
        num_labels=len(labels),
        id2label=id2label,
        label2id=label2id,
        low_cpu_mem_usage=True  # Optimize memory usage
    )
    
    # Load compressed weights
    compressed_state_dict = torch.load(model_path, map_location=_device)
    
    # Convert to float32 efficiently
    state_dict_fp32 = {}
    for key, value in compressed_state_dict.items():
        if value.dtype == torch.float16:
            state_dict_fp32[key] = value.float()
        else:
            state_dict_fp32[key] = value
    
    _model.load_state_dict(state_dict_fp32)
    _model.to(_device)
    _model.eval()
    
    # Clear temporary variables
    del compressed_state_dict, state_dict_fp32
    clear_memory()
    
    return _model, _tokenizer, _device

def extract_resume_entities(resume_text, model_path="compressed_resume_ner_model_v2.pt"):
    """
    Extract entities with optimized memory usage
    """
    try:
        # Load model lazily
        model, tokenizer, device = load_model_lazy(model_path)
        
        # Define labels
        unique_labels = ['COLLEGE NAME', 'COMPANY', 'DEGREE', 'DESIGNATION', 'EMAIL', 'LOCATION', 'NAME', 'SKILLS']
        labels = ['O'] + [f'B-{label}' for label in unique_labels] + [f'I-{label}' for label in unique_labels]
        id2label = {i: label for i, label in enumerate(labels)}
        
        # Tokenize with smaller chunks to save memory
        tokens = []
        for match in re.finditer(r'\S+', resume_text):
            tokens.append(match.group())
        
        # Limit token length to save memory
        MAX_LEN = 128  # Reduced from 256
        if len(tokens) > MAX_LEN - 2:  # Account for [CLS] and [SEP]
            tokens = tokens[:MAX_LEN - 2]
        
        # Tokenize
        inputs = tokenizer(
            tokens,
            is_split_into_words=True,
            return_offsets_mapping=True,
            padding='max_length',
            truncation=True,
            max_length=MAX_LEN,
            return_tensors='pt'
        )
        
        # Move to device
        input_ids = inputs['input_ids'].to(device)
        attention_mask = inputs['attention_mask'].to(device)
        
        # Get predictions with memory optimization
        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            predictions = torch.argmax(outputs.logits, dim=2)
        
        # Move results to CPU immediately to free GPU memory
        predictions = predictions.cpu()
        
        # Clear GPU memory
        del input_ids, attention_mask, outputs
        clear_memory()
        
        # Process predictions
        predicted_labels = []
        word_ids = inputs.word_ids(0)
        previous_word_idx = None
        
        for idx, word_idx in enumerate(word_ids):
            if word_idx is None or word_idx == previous_word_idx:
                continue
            
            if idx < len(predictions[0]):
                predicted_labels.append(id2label[predictions[0, idx].item()])
            else:
                predicted_labels.append('O')
                
            previous_word_idx = word_idx
        
        # Truncate predictions
        predicted_labels = predicted_labels[:len(tokens)]
        
        # Group entities
        entities_with_duplicates = {}
        current_entity = None
        current_text = []
        
        for token, label in zip(tokens, predicted_labels):
            if label == 'O':
                if current_entity:
                    if current_entity not in entities_with_duplicates:
                        entities_with_duplicates[current_entity] = []
                    entities_with_duplicates[current_entity].append(' '.join(current_text))
                    current_entity = None
                    current_text = []
            elif label.startswith('B-'):
                if current_entity:
                    if current_entity not in entities_with_duplicates:
                        entities_with_duplicates[current_entity] = []
                    entities_with_duplicates[current_entity].append(' '.join(current_text))
                current_entity = label[2:]
                current_text = [token]
            elif label.startswith('I-'):
                if current_entity == label[2:]:
                    current_text.append(token)
                else:
                    if current_entity:
                        if current_entity not in entities_with_duplicates:
                            entities_with_duplicates[current_entity] = []
                        entities_with_duplicates[current_entity].append(' '.join(current_text))
                    current_entity = label[2:]
                    current_text = [token]
        
        # Add last entity
        if current_entity and current_text:
            if current_entity not in entities_with_duplicates:
                entities_with_duplicates[current_entity] = []
            entities_with_duplicates[current_entity].append(' '.join(current_text))
        
        # Remove duplicates
        entities = {}
        for entity_type, mentions in entities_with_duplicates.items():
            cleaned_mentions = [m.strip().rstrip(',') for m in mentions]
            unique_mentions = []
            for m in cleaned_mentions:
                if not any(m.lower() == existing.lower() for existing in unique_mentions):
                    unique_mentions.append(m)
            entities[entity_type] = unique_mentions
        
        # Final memory cleanup
        clear_memory()
        
        return entities
        
    except Exception as e:
        # Clean up on error
        clear_memory()
        raise e

def unload_model():
    """Unload model to free memory when not needed"""
    global _model, _tokenizer, _device
    
    if _model is not None:
        del _model
        _model = None
    
    if _tokenizer is not None:
        del _tokenizer
        _tokenizer = None
    
    _device = None
    clear_memory() 