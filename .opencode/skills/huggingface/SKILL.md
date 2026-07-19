---
name: huggingface
description: Use when working with Hugging Face ecosystem. Covers transformers library, datasets, tokenizers, Hub, and model deployment.
---

# Hugging Face Skill

## Instructions

### Transformers Library

1. **Pipeline API** - Use `pipeline(task, model, tokenizer, device)` for quick inference on 30+ tasks. Supports text classification, NER, question answering, summarization, translation, text generation, and more. Set `device=0` for GPU.

2. **Auto Classes** - Use `AutoModel`, `AutoTokenizer`, `AutoConfig`, `AutoProcessor` for automatic model resolution from a pretrained identifier. Never hardcode specific model classes unless you need architecture-specific features.

3. **Model Loading** - Load with `AutoModel.from_pretrained('model_id', cache_dir, torch_dtype, device_map, trust_remote_code)`. Use `torch_dtype=torch.float16` for memory efficiency. Use `device_map='auto'` with accelerate for multi-GPU.

4. **Tokenizer** - Three steps: `tokenizer(text, padding, truncation, return_tensors)`. Set `padding='max_length'` or `True`, `truncation=True`, `return_tensors='pt'`. Use `tokenizer.batch_decode` for detokenization. Know special tokens: `[CLS]`, `[SEP]`, `[PAD]`, `[MASK]`.

5. **Training** - Use `Trainer` class with `TrainingArguments`. Set `output_dir`, `num_train_epochs`, `per_device_train_batch_size`, `gradient_accumulation_steps`, `fp16`, `logging_steps`, `save_strategy`, `evaluation_strategy`.

6. **Custom Trainer** - Subclass `Trainer` and override `compute_loss(self, model, inputs)` for custom loss functions or multi-task learning. Override `prediction_step` for custom generation logic.

7. **Configuration** - Use `AutoConfig.from_pretrained(model_id)` and modify attributes. Set `hidden_size`, `num_hidden_layers`, `num_attention_heads`, `intermediate_size`, `max_position_embeddings`, `vocab_size`.

### Datasets Library

1. **Loading** - Use `load_dataset('dataset_name', split='train', streaming=large)` for datasets from the Hub. Use `load_dataset('csv', data_files=path)` for local files. Supports CSV, JSON, Parquet, text files, and more.

2. **Dataset Operations** - Apply transformations with `dataset.map(function, batched=True, num_proc=4)`. Use `dataset.filter(condition)`, `dataset.select(indices)`, `dataset.shuffle(seed)`, `dataset.train_test_split(test_size=0.1)`.

3. **Processing** - Tokenize datasets by mapping the tokenizer across the dataset. Remove unused columns with `dataset.remove_columns()`. Set format with `dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'labels'])`.

4. **Streaming** - Use `streaming=True` for datasets that dont fit in memory. Iterates over shards without downloading full dataset. Compatible with `map` and `filter` operations.

### Tokenizers Library

1. **Training Tokenizers** - Use `tokenizers.BertWordPieceTokenizer` for subword tokenization. Train with `trainer.train(files)`. Set vocab size, min frequency, special tokens. Save with `tokenizer.save_model(directory)`.

2. **Fast Tokenizers** - Use Rust-backed fast tokenizers from Transformers (tokenizers with `is_fast=True`). Support `tokenizer.decode()` and `tokenizer.convert_ids_to_tokens()` for detailed inspection.

3. **Efficiency** - Use `batch_encode_plus` or `__call__` with batched inputs for parallel processing. Use `return_attention_mask=True`. For generation, use `tokenizer.pad_token_id` and `tokenizer.eos_token_id`.

### Hub Integration

1. **Uploading** - Use `model.push_to_hub(repo_name)`, `tokenizer.push_to_hub(repo_name)`, `dataset.push_to_hub(repo_name)`. Requires authentication via `huggingface-cli login` or `HuggingFaceHub` token.

2. **Model Cards** - Create `README.md` with YAML metadata: `license`, `language`, `tags`, `datasets`, `metrics`, `model-index`. Include evaluation results, intended use, limitations, and training details.

3. **Spaces** - Deploy interactive demos with Gradio or Streamlit. Create a `app.py` file and `requirements.txt` in a Space repo. Use `sdk: gradio` or `sdk: streamlit` in README metadata.

4. **API Inference** - Use Inference API for serverless model deployment. Call `requests.post(API_URL, headers=auth, json=payload)`. Rate limited on free tier. Supports all model types on the Hub.

## Examples

### Pipeline Inference

```python
from transformers import pipeline

classifier = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')
result = classifier('Hugging Face is amazing for NLP tasks!')
print(result)  # [{'label': 'POSITIVE', 'score': 0.9998}]

generator = pipeline('text-generation', model='gpt2', max_new_tokens=50)
output = generator('The future of AI is', do_sample=True, temperature=0.7)
```

### Fine-tuning with Trainer

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments

tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
model = AutoModelForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

def tokenize_fn(examples):
    return tokenizer(examples['text'], padding='max_length', truncation=True, max_length=128)

tokenized_dataset = dataset.map(tokenize_fn, batched=True)
tokenized_dataset = tokenized_dataset.remove_columns(['text'])
tokenized_dataset = tokenized_dataset.rename_column('label', 'labels')

training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=16,
    warmup_steps=500,
    logging_steps=100,
    evaluation_strategy='epoch',
    save_strategy='epoch',
    fp16=True,
    report_to='tensorboard',
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset['train'],
    eval_dataset=tokenized_dataset['test'],
)

trainer.train()
trainer.save_model('./final_model')
```

### Custom Dataset Loading

```python
from datasets import load_dataset, DatasetDict

dataset = load_dataset('imdb')
dataset = dataset.map(lambda x: tokenizer(x['text'], truncation=True, padding='max_length'), batched=True)
dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])

# For custom CSV data
custom_dataset = load_dataset('csv', data_files={'train': 'train.csv', 'test': 'test.csv'})
```

## Best Practices

1. **Use `accelerate`** with `device_map='auto'` for large model inference across multiple GPUs.
2. **Set `torch_dtype=torch.bfloat16`** for training stability with mixed precision.
3. **Use `gradient_checkpointing`** to trade compute for memory on large models.
4. **Cache models** with `TRANSFORMERS_CACHE` env var pointing to persistent storage.
5. **Monitor with `report_to='tensorboard'`** or `'wandb'` in TrainingArguments.
6. **Use `push_to_hub`** with `safe_serialization=True` to save in safetensors format.
7. **Pre-tokenize datasets** before training to avoid recomputing tokenization each epoch.
8. **Use `DataCollatorWithPadding`** for dynamic padding during training.
9. **Freeze embeddings** for domain adaptation tasks where vocabulary drift is minimal.
10. **Use `EarlyStoppingCallback`** from transformers to prevent overfitting.

## Common Mistakes

1. **Mismatched tokenizer and model** - Using a tokenizer that does not match the model architecture.
2. **Forgetting `return_tensors='pt'`** causing PyTorch tensor errors during training.
3. **Incorrect `num_labels`** for classification tasks; binary requires 2, not 1.
4. **Not setting `max_length`** causing variable-length sequences and inefficient batching.
5. **Ignoring `padding_side`** for generative models; should be left for causal LMs.
6. **Using `model.generate` without `max_new_tokens`** leading to unbounded generation.
7. **Not handling `pad_token_id`** in generation config causing warnings and misbehavior.
8. **Overriding `compute_loss`** without calling `super().compute_loss()` when using Trainer.
9. **Loading full dataset into memory** with `streaming=False` for datasets larger than RAM.
10. **Not removing unused columns** before training causing tensor shape errors in Trainer.

## Libraries

- `transformers` - Core library for 100k+ pretrained models
- `datasets` - Efficient dataset loading and processing
- `tokenizers` - High-performance tokenizer training
- `accelerate` - Multi-device inference and training orchestration
- `huggingface_hub` - API client for Hub operations
- `optimum` - Hardware optimization for Intel, AMD, and Habana
- `safetensors` - Safe and fast tensor serialization format
- `gradio` - Interactive ML demo creation for Spaces
- `evaluate` - Standardized evaluation metrics
- `trl` - Transformer Reinforcement Learning for alignment

## Design Principles

1. **Minimal API Surface** - Few entry points (pipelines, Auto classes) cover most use cases.
2. **Interoperability** - All models work with PyTorch, TensorFlow, and JAX through unified APIs.
3. **Stateful Configuration** - Config objects carry all hyperparameters for full reproducibility.
4. **Progressive Complexity** - Pipelines for quick use, Auto classes for control, raw classes for research.
5. **Community First** - Hub-first design encourages sharing and collaboration.
6. **Safety by Default** - Safetensors format, no pickle execution, security scanning on Hub.
7. **Hardware Flexibility** - Same code runs on CPU, GPU, TPU, and specialized accelerators.

## Coding Standards

1. **Model resolution** - Always use `from_pretrained` with explicit `model_id` version tags.
2. **Tokenizer pairing** - Store `tokenizer` alongside `model` as a tuple for pipeline consistency.
3. **Training arguments** - Use explicit `TrainingArguments` objects; avoid defaults for production.
4. **Dataset preparation** - Tokenize before training; save preprocessed datasets to disk.
5. **Checkpoint naming** - Name format: `checkpoint-{step}` for automatic resumption.
6. **Configuration files** - Save `config.json` with all model hyperparameters alongside weights.
7. **Logging setup** - Configure `transformers.logging.set_verbosity_error()` for production.
8. **Seed management** - Use `set_seed(seed)` from transformers for full reproducibility.
9. **Type safety** - Use `torch.Tensor` type hints and assert shape compatibility in forward methods.
10. **Model cards** - Every model push must include a complete model card with evaluation results.
