---
name: transformers
description: Use when working with transformer architectures. Covers attention mechanisms, BERT, GPT, T5, fine-tuning, and inference optimization.
---

# Transformers Skill

## Instructions

### Attention Mechanisms

1. **Scaled Dot-Product Attention** - Computed as `softmax(Q * K^T / sqrt(d_k)) * V`. The scaling factor `1/sqrt(d_k)` prevents softmax saturation for large d_k. Implement with `torch.nn.functional.scaled_dot_product_attention` in PyTorch 2.0+.

2. **Multi-Head Attention** - Project Q, K, V through `h` separate heads, compute attention in parallel, concatenate outputs, and project through final linear layer. Each head captures different relationship patterns.

3. **Self-Attention** - Q, K, V all derived from the same sequence. Each position attends to every other position, capturing global dependencies. Complexity is O(n^2 * d) where n is sequence length.

4. **Cross-Attention** - Q from decoder, K and V from encoder output. Used in encoder-decoder architectures to let the decoder attend to input tokens. Key for translation and summarization.

5. **Causal (Masked) Attention** - Apply upper-triangular mask to attention scores to prevent attending to future tokens. Used in decoder-only models like GPT. Set `attn_mask` with `torch.triu(torch.ones(L, L), diagonal=1).bool()`.

6. **Flash Attention** - Uses tiling and recomputation to avoid materializing the full NxN attention matrix. Reduces memory from O(N^2) to O(N). Available in PyTorch 2.0+ and through the `flash-attn` library.

7. **Sparse Attention** - Restrict attention to local windows and a few global tokens. Implemented in Longformer, BigBird, and Reformer. Reduces complexity from O(n^2) to O(n * window_size). Use for long documents.

8. **Linear Attention** - Reformulate attention as `phi(Q) * (phi(K)^T * V)` where phi is a kernel feature map. Achieves O(n) complexity. Used in Performer (FAVOR+) and Linformer. Lower accuracy but faster for long sequences.

### BERT (Encoder-Only)

1. **Architecture** - Stack of bidirectional Transformer encoder blocks. Uses `[CLS]` token for classification and `[MASK]` for masked language modeling. Pre-trained with MLM and NSP (or SOP in RoBERTa).

2. **Input Representation** - Token embeddings + segment embeddings + position embeddings. `input_ids`, `token_type_ids`, `attention_mask` as inputs. `max_position_embeddings` of 512 typically.

3. **Pre-training** - Mask 15% of tokens: 80% replace with `[MASK]`, 10% random token, 10% unchanged. Predict masked tokens. Next Sentence Prediction (NSP) for understanding sentence relationships.

4. **Fine-tuning** - Add task-specific head on top of `[CLS]` representation. For classification: `Dropout -> Linear(num_labels)`. For QA: `Linear(start_logits), Linear(end_logits)`. For NER: `Linear(num_labels)` on each token.

5. **Variants** - RoBERTa (more data, no NSP), ALBERT (parameter sharing), DistilBERT (knowledge distilled), Electra (discriminator-based), DeBERTa (disentangled attention, relative position).

### GPT (Decoder-Only)

1. **Architecture** - Stack of causal Transformer decoder blocks. Each block: masked self-attention -> cross-attention (none in pure decoder) -> FFN. Uses learned position embeddings or rotary embeddings.

2. **Autoregressive Generation** - Generate one token at a time, feed generated token back as input. Use `model.generate()` with appropriate decoding strategy. KV cache stores past key/value tensors across steps.

3. **Decoding Strategies** - Greedy (argmax, deterministic), Beam Search (top-k beams, good for translation), Top-K Sampling (sample from top k tokens), Top-P Nucleus Sampling (sample from smallest set with cumulative prob > p), Temperature Scaling (softmax temperature).

4. **Prompting** - GPT models respond to prompt formatting. Chat models use `tokenizer.apply_chat_template(messages)`. Instruction-tuned models expect specific format. System prompts set behavior.

5. **Variants** - GPT-2 (open-source baseline), GPT-NeoX and Pythia (EleutherAI), LLaMA and LLaMA-2 (Meta, optimized), Mistral and Mixtral (sliding window, mixture of experts), Falcon (TII).

### T5 (Encoder-Decoder)

1. **Architecture** - Full encoder-decoder Transformer. Encoder: bidirectional self-attention. Decoder: causal self-attention + cross-attention to encoder output. Uses relative position biases.

2. **Text-to-Text Framework** - Every NLP task framed as text-to-text: prefix the input with task name. Examples: `translate English to German: ...`, `summarize: ...`, `cola sentence: ...`. Output is always text.

3. **Span Corruption** - T5 pretraining objective: replace spans of contiguous tokens with unique sentinel tokens. Model learns to reconstruct the corrupted spans. More efficient than MLM.

4. **Adapter-Based Fine-tuning** - T5 adapters for parameter-efficient tuning. Use `prefix_tuning` or `lora` adapters. Keep base model frozen; train only adapter parameters. Enables multi-task serving.

5. **Variants** - T5 (original, multiple sizes), mT5 (multilingual), Flan-T5 (instruction fine-tuned), CodeT5 (code understanding), UL2 (mixture of denoisers).

### Fine-Tuning

1. **Full Fine-tuning** - Update all parameters. Best accuracy but expensive. Requires storing full gradients and optimizer states. Practical for models up to ~1B parameters on consumer hardware.

2. **LoRA (Low-Rank Adaptation)** - Inject trainable low-rank matrices into attention layers. Rank r (typically 8-64). Reduces trainable parameters by 10,000x. Apply to `q_proj`, `v_proj` or all linear layers.

3. **QLoRA** - Quantize base model to 4-bit NormalFloat, add LoRA adapters. Enables fine-tuning 65B models on single 48GB GPU. Uses double quantization and paged optimizers.

4. **Prefix Tuning** - Prepends learnable prefix tokens to each transformer layer. Only prefix parameters are trained. Keeps base model frozen. Effective for generation tasks.

5. **Prompt Tuning** - Similar to prefix tuning but only adds learnable embeddings at the input layer. Simpler but may underperform prefix tuning for deep tasks.

### Inference Optimization

1. **KV Caching** - Cache keys and values from previous timesteps. Avoids recomputing entire attention for each new token. Implement with `past_key_values` in Hugging Face. Reduces decoding from O(n^2) to O(n).

2. **Quantization** - Reduce precision: FP16 (half memory), INT8 (quarter memory, 2-4x speed), INT4 (8x memory reduction). Use `bitsandbytes` for post-training quantization. Apply per-channel or per-token quantization.

3. **Speculative Decoding** - Use a small draft model to generate candidate tokens, then verify with the large model. Enables 2-3x speedup without quality loss. Requires both models on the same device.

4. **PagedAttention (vLLM)** - Manage KV cache in non-contiguous memory blocks. Enables efficient memory sharing and larger batch sizes. Used in vLLM for high-throughput serving.

5. **Continuous Batching** - Dynamically add/remove sequences from a running batch. Unlike static batching, no need to wait for all sequences to finish. Requires custom inference engine (vLLM, TGI).

6. **Tensor Parallelism** - Split attention heads and FFN intermediate dimensions across GPUs. Each GPU computes partial results; all-gather to combine. Requires high-bandwidth interconnects.

## Examples

### Multi-Head Attention Implementation

```python
import torch.nn as nn

class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, n_heads, dropout=0.1):
        super().__init__()
        assert d_model % n_heads == 0
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        batch_size = x.size(0)
        Q = self.w_q(x).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        K = self.w_k(x).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        V = self.w_v(x).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        attn = Q @ K.transpose(-2, -1) / (self.d_k ** 0.5)
        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))
        attn = self.dropout(attn.softmax(dim=-1))
        out = attn @ V
        out = out.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        return self.w_o(out)
```

### Causal Language Model Fine-tuning with LoRA

```python
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=8,
    lora_alpha=32,
    target_modules=['q_proj', 'v_proj', 'k_proj', 'o_proj'],
    lora_dropout=0.05,
    bias='none',
    task_type='CAUSAL_LM'
)
model = AutoModelForCausalLM.from_pretrained('meta-llama/Llama-2-7b-hf', torch_dtype=torch.bfloat16)
model = get_peft_model(model, lora_config)
trainer = Trainer(model=model, args=training_args, train_dataset=dataset)
trainer.train()
```

### Efficient Text Generation

```python
outputs = model.generate(
    input_ids,
    max_new_tokens=256,
    do_sample=True,
    temperature=0.7,
    top_p=0.9,
    top_k=50,
    repetition_penalty=1.1,
    num_beams=1,  # greedy sampling for speed
    use_cache=True,  # enable KV cache
    pad_token_id=tokenizer.pad_token_id,
    eos_token_id=tokenizer.eos_token_id,
)
```

## Best Practices

1. **Use Flash Attention** when sequence length exceeds 512 tokens; enables longer contexts.
2. **Apply RoPE (Rotary Position Embeddings)** for better length generalization than learned positions.
3. **Use gradient checkpointing** during training to trade compute for memory on large models.
4. **Implement KV cache** for all autoregressive decoding; essential for production inference.
5. **Use speculative decoding** for latency-critical applications with large models.
6. **Choose model size based on task**: base for classification, large for reasoning, XL for generation.
7. **Fine-tune with LoRA** first; only full fine-tune if LoRA is insufficient.
8. **Use `torch.compile`** for 10-20% speedup on compatible transformer architectures.
9. **Monitor attention patterns** for degenerate behavior (uniform attention, attention collapse).
10. **Validate positional encoding extrapolation** before deploying on sequences longer than training.

## Common Mistakes

1. **Incorrect attention mask shape** - Mask must match `(batch, 1, seq_len, seq_len)` or broadcast correctly.
2. **Not scaling attention logits** by `1/sqrt(d_k)`, causing softmax saturation and vanishing gradients.
3. **Forgetting causal masking** in decoder models, allowing future token leakage during training.
4. **Ignoring KV cache** and recomputing full attention for each generation step (O(n^3) complexity).
5. **Mismatched `max_position_embeddings`** when fine-tuning on sequences longer than pretraining.
6. **Using incorrect `token_type_ids`** in BERT models; affects segment-level understanding.
7. **Applying LoRA to all layers** when only attention layers need adaptation; wasteful parameters.
8. **Not setting `model.eval()`** during inference, causing dropout and batch norm to behave incorrectly.
9. **Using beam search for creative tasks** like story generation; use sampling with temperature.
10. **Loading tokenizer without `use_fast=True`** missing performance benefits of Rust-backed tokenizers.

## Libraries

- `transformers` - Model architectures, tokenizers, pipelines, trainer API
- `accelerate` - Multi-device training and inference orchestration
- `peft` - Parameter-efficient fine-tuning (LoRA, prefix tuning, prompt tuning)
- `bitsandbytes` - 4-bit and 8-bit quantization for training and inference
- `flash-attn` - Optimized Flash Attention kernels
- `vllm` - High-throughput LLM serving engine
- `xformers` - Memory-efficient attention implementations
- `sentencepiece` - Tokenization for many multilingual models
- `tiktoken` - OpenAI's fast BPE tokenizer
- `jingoo` - Low-bit quantization toolkit for transformers

## Design Principles

1. **Attention is All You Need** - Self-attention is the fundamental building block; feedforward networks are secondary.
2. **Scale Is All You Need** - Model performance improves predictably with scale (compute, data, parameters).
3. **Unified Architecture** - Encoder-only, decoder-only, and encoder-decoder share core attention mechanisms.
4. **Position-Aware Representations** - Position information is explicitly encoded; transformers have no inherent notion of order.
5. **Parallel Training** - Unlike RNNs, all positions are computed in parallel, enabling efficient GPU utilization.
6. **Composable Blocks** - Transformer layers are identical, stackable blocks enabling arbitrary depth.
7. **Transfer Learning** - Pretrain on large corpora, fine-tune on specific tasks with minimal data.

## Coding Standards

1. **Module definition** - Each transformer component is a `nn.Module` with clearly separated `__init__` and `forward`.
2. **Attention implementation** - Use `scaled_dot_product_attention` when available; fall back to manual implementation.
3. **Configuration objects** - Use dataclasses or `PretrainedConfig` subclasses for all hyperparameters.
4. **Shape documentation** - Document tensor shapes as comments: `# (batch, heads, seq, d_k)`.
5. **Mask handling** - Accept `attention_mask` and `causal_mask` as optional boolean tensors.
6. **Device management** - All tensors and modules explicitly moved to device; no global device assumptions.
7. **Numerical stability** - Always apply `softmax` in float32, then cast down if using mixed precision.
8. **Efficient operations** - Use `torch.chunk` over `torch.split_` and in-place ops only when safe.
9. **Testing** - Test attention masking, causal masking, KV cache correctness, and gradient flow.
10. **Documentation** - Every attention variant includes a reference paper tag and complexity analysis.
