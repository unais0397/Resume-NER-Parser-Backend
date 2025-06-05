import re
import torch
from transformers import BertTokenizerFast, BertForTokenClassification
import warnings
from transformers import logging as transformers_logging
import os

warnings.filterwarnings('ignore')  # Suppress general warnings
transformers_logging.set_verbosity_error()  # Suppress transformers warnings

# Then define your extract_resume_entities function...


def extract_resume_entities(resume_text, model_path="compressed_resume_ner_model_v2.pt"):
    """
    Extract and group named entities from resume text using a compressed fine-tuned BERT model.
    Returns only unique entities for each entity type.
    
    Args:
        resume_text (str): The text content of a resume
        model_path (str): Path to the compressed model weights
        
    Returns:
        dict: Dictionary with entity types as keys and lists of unique extracted entities as values
    """
    # Define labels based on your training data
    unique_labels = ['COLLEGE NAME', 'COMPANY', 'DEGREE', 'DESIGNATION', 'EMAIL', 'LOCATION', 'NAME', 'SKILLS']
    
    # Add 'O' for non-entity tokens and special tokens
    labels = ['O'] + [f'B-{label}' for label in unique_labels] + [f'I-{label}' for label in unique_labels]
    label2id = {label: i for i, label in enumerate(labels)}
    id2label = {i: label for i, label in enumerate(labels)}
    
    # Set device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Load the tokenizer
    tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased')
    
    # Check if compressed model exists
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Compressed model not found at {model_path}")
    
    
    
    # Load the base model structure
    model = BertForTokenClassification.from_pretrained(
        'bert-base-uncased', 
        num_labels=len(labels),
        id2label=id2label,
        label2id=label2id
    )
    
    # Load the compressed state dict (mixed precision)
    compressed_state_dict = torch.load(model_path, map_location=device)
    
    # Convert half precision back to float32 for inference
    state_dict_fp32 = {}
    for key, value in compressed_state_dict.items():
        if value.dtype == torch.float16:
            state_dict_fp32[key] = value.float()
        else:
            state_dict_fp32[key] = value
    
    model.load_state_dict(state_dict_fp32)
    
    model.to(device)
    model.eval()
    
    # Tokenize the text
    tokens = []
    for match in re.finditer(r'\S+', resume_text):
        tokens.append(match.group())
    
    # Prepare input for the model
    MAX_LEN = 256  # Match the max length used during training
    inputs = tokenizer(
        tokens,
        is_split_into_words=True,
        return_offsets_mapping=True,
        padding='max_length',
        truncation=True,
        max_length=MAX_LEN,
        return_tensors='pt'
    )
    
    # Move inputs to device
    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)
    
    # Get model predictions
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        predictions = torch.argmax(outputs.logits, dim=2)
    
    # Convert predictions to labels
    predicted_labels = []
    word_ids = inputs.word_ids(0)  # Batch index 0
    previous_word_idx = None
    
    for idx, word_idx in enumerate(word_ids):
        if word_idx is None or word_idx == previous_word_idx:
            continue
        
        if idx < len(predictions[0]):
            predicted_labels.append(id2label[predictions[0, idx].item()])
        else:
            predicted_labels.append('O')
            
        previous_word_idx = word_idx
    
    # Truncate predictions if needed
    predicted_labels = predicted_labels[:len(tokens)]
    
    # Combine tokens and predictions
    token_predictions = list(zip(tokens, predicted_labels))
    
    # Group entities by type
    entities_with_duplicates = {}
    current_entity = None
    current_text = []
    
    for token, label in token_predictions:
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
            current_entity = label[2:]  # Remove B- prefix
            current_text = [token]
        elif label.startswith('I-'):
            if current_entity == label[2:]:  # Only append if it's the same entity type
                current_text.append(token)
            else:
                # Start a new entity if the I- tag doesn't match current entity
                if current_entity:
                    if current_entity not in entities_with_duplicates:
                        entities_with_duplicates[current_entity] = []
                    entities_with_duplicates[current_entity].append(' '.join(current_text))
                current_entity = label[2:]
                current_text = [token]
    
    # Add the last entity if there is one
    if current_entity and current_text:
        if current_entity not in entities_with_duplicates:
            entities_with_duplicates[current_entity] = []
        entities_with_duplicates[current_entity].append(' '.join(current_text))
    
    # Remove duplicates while preserving order
    entities = {}
    for entity_type, mentions in entities_with_duplicates.items():
        # Clean up entity values - remove trailing commas and normalize whitespace
        cleaned_mentions = [m.strip().rstrip(',') for m in mentions]
        
        # Remove duplicates while preserving order
        unique_mentions = []
        for m in cleaned_mentions:
            # Case-insensitive comparison to better catch duplicates
            if not any(m.lower() == existing.lower() for existing in unique_mentions):
                unique_mentions.append(m)
        
        entities[entity_type] = unique_mentions
    
    return entities