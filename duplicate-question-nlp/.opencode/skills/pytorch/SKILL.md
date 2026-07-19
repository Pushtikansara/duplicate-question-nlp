---
name: pytorch
description: Use when building deep learning models with PyTorch. Covers tensors, autograd, nn.Module, training loops, and deployment.
---

# PyTorch Skill

## Overview
PyTorch is an open-source machine learning framework that accelerates the path from research prototyping to production deployment. It provides a tensor computation library with strong GPU acceleration and automatic differentiation, a rich ecosystem of tools for computer vision, NLP, reinforcement learning, and more, and a flexible, Pythonic design that makes it intuitive for researchers and practitioners.

## Instructions
- Use `torch.nn.Module` for all neural network components; override `__init__` and `forward`
- Use `torch.nn.Sequential` for simple feed-forward architectures without custom forward logic
- Use `torch.utils.data.Dataset` and `DataLoader` for data loading with multiprocessing
- Use `torch.optim` optimizers (AdamW recommended as default); set weight decay for regularization
- Use `model.train()` for training mode and `model.eval()` for inference/evaluation
- Wrap inference code in `torch.no_grad()` to disable gradient computation and reduce memory
- Use `torch.cuda.amp` for mixed precision training (faster, less memory)
- Use `torch.nn.Loss` classes (CrossEntropyLoss, MSELoss) rather than manual loss computation
- Use `torchmetrics` for standardized metric computation (accuracy, F1, etc.)
- Use `tensorboard` or `wandb` for experiment tracking and visualization
- Use `torch.jit.script` or `torch.compile` for model optimization
- Use `torch.save(model.state_dict(), path)` for saving, `model.load_state_dict(torch.load(path))` for loading
- Use `torch.jit.trace` or `torch.onnx.export` for deployment to production

## Core Concepts

### Tensors
- Multi-dimensional arrays with GPU support and automatic differentiation
- Creation: `torch.tensor()`, `torch.zeros()`, `torch.ones()`, `torch.randn()`, `torch.arange()`
- Data types: `float32` (default), `float16`, `bfloat16`, `int64`, `int32`, `bool`
- Device: `.to('cuda')`, `.to('cpu')`, `.to('mps')` (Apple Silicon)
- Reshaping: `tensor.view(shape)`, `tensor.reshape(shape)`, `tensor.transpose()`, `tensor.permute()`
- Indexing: same as NumPy with additional advanced indexing
- Broadcasting: similar to NumPy broadcasting rules
- `torch.cat()`, `torch.stack()`, `torch.split()`, `torch.chunk()` for tensor manipulation
- `torch.unsqueeze()`, `torch.squeeze()` for dimension manipulation

### Autograd (Automatic Differentiation)
- `tensor.requires_grad = True` enables gradient tracking
- `.backward()` computes gradients via reverse-mode automatic differentiation
- `.grad` attribute holds the computed gradient
- `.detach()` creates a tensor that doesn't track gradients (for visualization, metrics)
- `torch.no_grad()` context manager disables gradient computation for inference
- `torch.set_grad_enabled(False)` globally disables gradients
- Gradient accumulates by default — call `optimizer.zero_grad()` in each training step
- `.retain_grad()` preserves gradient for non-leaf tensors
- `torch.autograd.Function` for custom autograd operations

### nn.Module
- Base class for all neural network modules
- Submodules defined in `__init__` are automatically registered
- `forward()` method defines the forward pass computation
- `parameters()` returns all trainable parameters
- `modules()` returns all submodules recursively
- `apply()` recursively applies a function to all submodules (for initialization)
- `state_dict()` / `load_state_dict()` for serialization
- `register_buffer()` for non-trainable tensors (running averages, etc.)
- `register_parameter()` for custom trainable parameters
- `train()` / `eval()` toggle training and evaluation modes for layers like Dropout, BatchNorm

### Training Loop Structure
```python
def train_one_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    total_loss = 0.0
    for batch_idx, (inputs, targets) in enumerate(dataloader):
        inputs, targets = inputs.to(device), targets.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item()

        if batch_idx % 100 == 0:
            print(f'Batch {batch_idx}, Loss: {loss.item():.4f}')

    return total_loss / len(dataloader)
```

### Datasets and DataLoaders
- `torch.utils.data.Dataset` — abstract class with `__len__` and `__getitem__`
- `torch.utils.data.DataLoader` — batches, shuffling, multiprocessing
- `num_workers` — number of subprocesses for data loading (set to 4-8 per GPU)
- `pin_memory=True` for faster GPU data transfer
- `prefetch_factor=2` for prefetching batches
- `sampler` for custom sampling strategies (imbalanced datasets, distributed training)
- `torch.utils.data.random_split()` for train/val splitting
- `torchvision.datasets`, `torchtext.datasets`, `torchaudio.datasets` for standard datasets
- `torchdata` for advanced data pipelines (map-style, iterable-style, sharding)

### Optimizers and Schedulers
- `torch.optim.SGD` — standard SGD with momentum
- `torch.optim.Adam` — adaptive learning rate (default lr=0.001)
- `torch.optim.AdamW` — Adam with decoupled weight decay (recommended default)
- `torch.optim.lr_scheduler.StepLR` — step decay at intervals
- `torch.optim.lr_scheduler.CosineAnnealingLR` — cosine annealing schedule
- `torch.optim.lr_scheduler.ReduceLROnPlateau` — reduce LR when metric plateaus
- `torch.optim.lr_scheduler.OneCycleLR` — one-cycle learning rate policy
- Scheduler step: `scheduler.step()` after each epoch (or after each batch for OneCycleLR)

### Loss Functions
- `torch.nn.CrossEntropyLoss` — classification (combines LogSoftmax + NLLLoss)
- `torch.nn.BCELoss` — binary classification (sigmoid + BCE)
- `torch.nn.BCEWithLogitsLoss` — binary classification (more numerically stable)
- `torch.nn.MSELoss` — regression (mean squared error)
- `torch.nn.L1Loss` — regression (mean absolute error)
- `torch.nn.SmoothL1Loss` — Huber loss (robust to outliers)
- `torch.nn.CTCLoss` — sequence alignment (speech, OCR)
- `torch.nn.NLLLoss` — negative log likelihood (for log-softmax outputs)
- `torch.nn.KLDivLoss` — KL divergence (distillation, variational methods)
- `torch.nn.TripletMarginLoss` — metric learning (face recognition, embeddings)

## Examples

### Convolutional Neural Network
```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class ConvNet(nn.Module):
    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )

        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(128, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.classifier(x)
        return x

# Weight initialization
def init_weights(m: nn.Module) -> None:
    if isinstance(m, (nn.Conv2d, nn.Linear)):
        nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
        if m.bias is not None:
            nn.init.constant_(m.bias, 0)
    elif isinstance(m, nn.BatchNorm2d):
        nn.init.constant_(m.weight, 1)
        nn.init.constant_(m.bias, 0)

model = ConvNet(num_classes=100)
model.apply(init_weights)
```

### Transformer for Text Classification
```python
import torch
import torch.nn as nn

class TransformerClassifier(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        d_model: int = 256,
        nhead: int = 8,
        num_layers: int = 4,
        num_classes: int = 2,
        max_len: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoding = PositionalEncoding(d_model, max_len, dropout)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True,
            activation='gelu',
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.classifier = nn.Linear(d_model, num_classes)
        self.dropout = nn.Dropout(dropout)
        self.d_model = d_model

    def forward(self, input_ids: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        x = self.embedding(input_ids) * (self.d_model ** 0.5)
        x = self.pos_encoding(x)
        x = self.transformer(x, src_key_padding_mask=mask)
        x = x.transpose(1, 2)  # (batch, d_model, seq_len)
        x = self.pool(x).squeeze(-1)  # (batch, d_model)
        x = self.dropout(x)
        return self.classifier(x)

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-torch.log(torch.tensor(10000.0)) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)
```

### Mixed Precision Training
```python
import torch
from torch.cuda.amp import autocast, GradScaler

def train_mixed_precision(model, dataloader, optimizer, criterion, device, epochs):
    scaler = GradScaler('cuda' if torch.cuda.is_available() else 'cpu')

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0

        for inputs, targets in dataloader:
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()

            with autocast('cuda' if torch.cuda.is_available() else 'cpu'):
                outputs = model(inputs)
                loss = criterion(outputs, targets)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()

            epoch_loss += loss.item()

        print(f'Epoch {epoch+1}/{epochs}, Loss: {epoch_loss/len(dataloader):.4f}')
```

### Custom Dataset and DataLoader
```python
import torch
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from PIL import Image
import numpy as np

class ImageDataset(Dataset):
    def __init__(self, root_dir: str, transform=None):
        self.root = Path(root_dir)
        self.transform = transform
        self.samples = []

        for class_idx, class_dir in enumerate(sorted(self.root.iterdir())):
            if class_dir.is_dir():
                for img_path in class_dir.glob('*.[jp][pn]g'):
                    self.samples.append((str(img_path), class_idx))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert('RGB')

        if self.transform:
            image = self.transform(image)

        return image, label

# Usage
from torchvision import transforms

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

dataset = ImageDataset('data/train', transform=transform)
dataloader = DataLoader(
    dataset,
    batch_size=64,
    shuffle=True,
    num_workers=4,
    pin_memory=True,
    drop_last=True,
)
```

## Best Practices
- Set `torch.manual_seed(seed)` for reproducibility; also set `cudnn.deterministic = True` for GPU
- Use `torch.backends.cudnn.benchmark = True` for fixed input sizes (faster conv ops)
- Move model to device before creating optimizer (optimizer references model parameters)
- Use `model.apply(init_weights)` for custom weight initialization
- Use gradient clipping (`clip_grad_norm_`) to prevent exploding gradients
- Use learning rate scheduling with warmup for transformer models
- Monitor training with gradient histograms and weight distributions in TensorBoard
- Use `torch.jit.script` for production deployment (faster, no Python dependency)
- Use `torch.compile` (PyTorch 2.0+) for graph-level optimization
- Use `DataLoader` with `pin_memory=True` and `num_workers=4-8` for GPU training
- Use `torch.inference_mode()` (PyTorch 1.9+) instead of `torch.no_grad()` for inference
- Use `torch.set_float32_matmul_precision('high')` for faster matmul on modern GPUs

## Common Mistakes
- Not calling `model.train()` or `model.eval()` — Dropout and BatchNorm behave differently
- Forgetting `optimizer.zero_grad()` — gradients accumulate across batches
- Moving data to device inside the training loop repeatedly (slow; move once per batch)
- Using too many `num_workers` (causes CPU oversubscription; 4-8 per GPU is typical)
- Not setting `pin_memory=True` for DataLoader (slows GPU transfer)
- Using `torch.Tensor` instead of `torch.tensor` (the former is a class constructor, not a factory function)
- Modifying tensors with `requires_grad=True` in-place (autograd can't track it)
- Not handling gradient computation properly in evaluation mode (memory leak)
- Using `loss.item()` on a GPU tensor without moving to CPU (works but is slower)
- Not calling `torch.cuda.empty_cache()` when clearing GPU memory
- Overfitting the validation set by tuning hyperparameters on test set performance
- Using too large a batch size (memory exhaustion) or too small (noisy gradients)
- Not saving optimizer state_dict for resuming training (loss of momentum/learning rate state)
- Confusing `model.state_dict()` and `model.parameters()` (state_dict includes buffers like running_mean)
- Using `torch.save(model, path)` instead of `torch.save(model.state_dict(), path)` (less portable)

## Libraries
- **torchvision** — datasets, model architectures, image transforms
- **torchtext** — NLP datasets, tokenizers, and data processing
- **torchaudio** — audio datasets, I/O, transforms
- **pytorch-lightning** — high-level training framework with structured boilerplate
- **transformers** (Hugging Face) — pretrained transformer models (BERT, GPT, T5, etc.)
- **accelerate** — Hugging Face's distributed training utility
- **torchmetrics** — standardized metrics (accuracy, F1, IoU, perplexity)
- **timm** — pretrained vision models and training utilities
- **wandb** — experiment tracking and visualization
- **tensorboard** — training visualization (built-in via `torch.utils.tensorboard`)
- **torchinfo** — model summary (parameter count, layer shapes)
- **onnxruntime** — ONNX model inference (deployment)
- **torchserve** — production model serving
- **torchgeo** — geospatial data and models

## Design Principles
- **Define-by-Run**: The computation graph is defined dynamically as operations are executed
- **Pythonic**: Deep learning models are just Python classes with `nn.Module`
- **Tensor-Centric**: All computations use tensor operations with autograd
- **GPU-First**: Tensors and models can be moved to GPU with `.to('cuda')`
- **Eager Execution**: Operations are executed immediately (no static graph compilation by default)
- **Research to Production**: Same codebase from experimentation to deployment with TorchScript

## Coding Standards
- Import as `import torch`, `import torch.nn as nn`, `import torch.nn.functional as F`
- Model classes inherit from `nn.Module`
- `__init__` defines all layers, `forward` defines the computation
- Use `nn.Sequential` for simple linear stacks
- Name tensors meaningfully: `input_ids`, `attention_mask`, `pixel_values`
- Type hint tensor shapes in docstrings: `(batch, channels, height, width)`
- Use `super().__init__()` at the beginning of `__init__`
- Use `self.training` for conditional logic that differs between train and eval
- Register non-trainable tensors with `self.register_buffer()`
- Define custom `__repr__` or use `torchinfo.summary()` for model debugging
- Organize training code: `train.py`, `model.py`, `dataset.py`, `config.py`, `utils.py`

## Distributed Training
- `torch.nn.DataParallel` — single-node, multi-GPU (simple but slower)
- `torch.nn.DistributedDataParallel` — recommended for multi-GPU (faster, multi-node capable)
- `torch.distributed.init_process_group()` for backend initialization
- Use `torch.utils.data.distributed.DistributedSampler` for sharding data
- Use `torch.cuda.set_device(local_rank)` for GPU assignment
- Use `accelerate` library for easier distributed training setup
- Use `torchrun` launcher: `torchrun --nproc_per_node=4 train.py`
- Gradient accumulation for large models that don't fit in GPU memory

## Model Deployment
- **TorchScript**: `torch.jit.script(model)` or `torch.jit.trace(model, example_input)`
- **ONNX**: `torch.onnx.export(model, example_input, 'model.onnx')`
- **TorchServe**: Production model serving with REST API
- **TensorRT**: NVIDIA optimization for inference (via `torch2trt` or `onnx-tensorrt`)
- **Core ML**: Export for Apple devices (via `coremltools`)
- **TFLite**: Export for mobile/edge (via ONNX → TFLite)
- **Quantization**: `torch.quantization` for INT8 inference (2-4x speedup)
- **Pruning**: `torch.nn.utils.prune` for model compression
- **Dynamic batching**: Combine multiple requests into a single batch for GPU efficiency
- **Model optimization**: `torch.compile(model)` for 10-20% inference speedup

## Debugging
- Use `torch.autograd.set_detect_anomaly(True)` to find NaN gradient sources (slows training)
- Use `torch.isnan(tensor).any()` and `torch.isinf(tensor).any()` to check for numerical issues
- Use `tensorboard` gradient histogram to monitor gradient flow
- Use `torchinfo.summary(model, input_size)` to verify layer shapes
- Use `torch.jit.script` errors to find unsupported ops
- Visualize intermediate activations by registering forward hooks
- Use `with torch.autograd.profiler.profile()` for performance profiling
- Use `torch.cuda.memory_summary()` for GPU memory debugging
- Use `torch.set_printoptions(precision=4, sci_mode=False)` for readable tensor output
- Add `assert not torch.isnan(loss)` in training loop to catch NaN early
- Use gradient clipping to mitigate exploding gradients
- Use learning rate finder (`torch-lr-finder`) for optimal initial learning rate
- Gradually overfit a small subset of data to verify model correctness before full training
