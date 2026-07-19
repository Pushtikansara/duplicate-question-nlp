---
name: tensorflow
description: Use when building machine learning models with TensorFlow/Keras. Covers model building, training, deployment, and TF ecosystem.
---

# TensorFlow Skill

## Instructions

### Model Building

1. **Sequential API** - Use `tf.keras.Sequential` for simple layer stacks where each layer has exactly one input and one output tensor. Suitable for most feedforward networks, CNNs, and simple RNNs.

2. **Functional API** - Use `tf.keras.Model` with the functional API for complex architectures with multiple inputs, multiple outputs, shared layers, residual connections, or non-linear topology. This is the most commonly used API in production.

3. **Subclassing API** - Use `tf.keras.Model` subclassing when you need full control over forward pass logic. Implement `call(self, inputs, training=False)` and `__init__`. Be aware that subclassed models cannot be serialized as easily.

4. **Custom Layers** - Extend `tf.keras.layers.Layer` and implement `__init__`, `build(self, input_shape)`, and `call(self, inputs)`. Use `add_weight()` for trainable parameters and call `super().__init__()` in `__init__`.

5. **Loss Functions** - Choose task-appropriate losses: `CategoricalCrossentropy` for multiclass, `BinaryCrossentropy` for binary, `MeanSquaredError` for regression, `KLDivergence` for distribution matching. Create custom losses by defining a function that takes `y_true, y_pred`.

6. **Optimizers** - Prefer `Adam` as default optimizer with learning rate `1e-3`. Use `SGD` with momentum for computer vision. Use `AdamW` for transformer models. Adjust learning rate with `ExponentialDecay`, `CosineDecay`, or `ReduceLROnPlateau` callbacks.

7. **Metrics** - Track `Accuracy`, `Precision`, `Recall`, `AUC`, `MeanAbsoluteError`, etc. Use custom metrics by subclassing `tf.keras.metrics.Metric` and implementing `update_state`, `result`, and `reset_state`.

### Training

1. **Model.fit()** - Standard training loop with `epochs`, `batch_size`, `validation_split`, `callbacks`, `class_weight`, and `sample_weight` parameters. Use `steps_per_epoch` for large datasets.

2. **Custom Training Loops** - Use `tf.GradientTape` for full control. Structure as: open gradient tape, forward pass, compute loss, compute gradients with `tape.gradient`, apply with `optimizer.apply_gradients`. Update metrics manually.

3. **Callbacks** - Essential callbacks: `ModelCheckpoint` (save best weights), `EarlyStopping` (patience=5-10), `ReduceLROnPlateau` (factor=0.5, patience=3), `TensorBoard` (log everything), `CSVLogger` (training history), `LearningRateScheduler` (custom schedules).

4. **Distribution Strategy** - Use `tf.distribute.MirroredStrategy` for single-host multi-GPU. Use `MultiWorkerMirroredStrategy` for multi-host. Use `TPUStrategy` for TPUs. Wrap model creation and compilation inside the strategy scope.

5. **Mixed Precision** - Use `tf.keras.mixed_precision.set_global_policy('mixed_float16')` for faster training on compatible hardware. Use loss scaling with `LossScaleOptimizer` for stability.

6. **Data Pipeline** - Use `tf.data.Dataset` for efficient input pipelines. Apply `cache()`, `prefetch(tf.data.AUTOTUNE)`, `shuffle(buffer_size)`, `map(map_func, num_parallel_calls=tf.data.AUTOTUNE)`, `batch(batch_size)`, and `repeat()`.

### Deployment

1. **SavedModel Format** - Export with `model.save('path')` to SavedModel directory. This is the standard TF deployment format. Contains the computation graph, weights, and assets.

2. **TensorFlow Serving** - Deploy SavedModels with TF Serving using Docker. Create a `models.config` file for multi-model serving. Use REST or gRPC endpoints. Set up batching for throughput.

3. **TFLite** - Convert models with `tf.lite.TFLiteConverter.from_saved_model()`. Apply quantization: dynamic range, float16, or int8. Use `representative_dataset` for calibration. Deploy on mobile, edge, and embedded devices.

4. **TensorFlow.js** - Convert with `tensorflowjs_converter` for browser and Node.js deployment. Supports both inference and transfer learning in the browser using WebGL or WebAssembly backends.

5. **TensorRT Integration** - Use `TF-TRT` to optimize SavedModels for NVIDIA GPUs. Apply FP16 or INT8 precision. Achieve 2-5x inference speedup. Use `trt.SegmentIfRank` for dynamic shapes.

### TF Ecosystem

1. **TFX** - Use TensorFlow Extended for production ML pipelines. Components: ExampleGen, StatisticsGen, SchemaGen, Transform, Trainer, Evaluator, Pusher. Orchestrate with Apache Beam or Kubeflow.

2. **TF Datasets** - Use `tensorflow_datasets` for standard benchmarks. Load with `tfds.load('dataset_name', split='train', as_supervised=True)`. Supports versioning, data preprocessing, and visualization.

3. **TF Hub** - Reuse pretrained models from `tensorflow_hub`. Load with `hub.load(url)` or `hub.KerasLayer(url)`. Fine-tune by setting `trainable=True`. Covers text, image, audio, and video modalities.

4. **TF Agents** - Use for reinforcement learning. Provides algorithms (DQN, PPO, SAC), environments, and replay buffers. Integrates with TF and Keras. Suitable for training RL agents at scale.

5. **TF Model Optimization** - Use `tensorflow_model_optimization` for pruning, quantization, and clustering. Apply `prune_low_magnitude` for weight pruning, `quantize_apply` for quantization-aware training.

## Examples

### Binary Classification with Functional API

```python
import tensorflow as tf
from tensorflow import keras

inputs = keras.Input(shape=(128,))
x = keras.layers.Dense(256, activation='relu')(inputs)
x = keras.layers.BatchNormalization()(x)
x = keras.layers.Dropout(0.3)(x)
x = keras.layers.Dense(128, activation='relu')(x)
x = keras.layers.Dropout(0.2)(x)
outputs = keras.layers.Dense(1, activation='sigmoid')(x)
model = keras.Model(inputs=inputs, outputs=outputs)

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-3),
    loss=keras.losses.BinaryCrossentropy(),
    metrics=[keras.metrics.BinaryAccuracy(), keras.metrics.AUC()]
)

callbacks = [
    keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),
    keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=3),
    keras.callbacks.ModelCheckpoint('best_model.h5', save_best_only=True)
]

history = model.fit(
    x_train, y_train,
    validation_split=0.2,
    epochs=100,
    batch_size=32,
    callbacks=callbacks
)
```

### Custom Training Loop

```python
@tf.function
def train_step(x, y):
    with tf.GradientTape() as tape:
        logits = model(x, training=True)
        loss = loss_fn(y, logits)
        loss += sum(model.losses)
    grads = tape.gradient(loss, model.trainable_weights)
    optimizer.apply_gradients(zip(grads, model.trainable_weights))
    train_acc.update_state(y, logits)
    return loss

for epoch in range(epochs):
    for batch, (x, y) in enumerate(train_dataset):
        loss = train_step(x, y)
    for metric in metrics:
        metric.reset_state()
```

### Efficient Data Pipeline

```python
dataset = tf.data.Dataset.from_tensor_slices((files, labels))
dataset = dataset.shuffle(10000)
dataset = dataset.map(parse_function, num_parallel_calls=tf.data.AUTOTUNE)
dataset = dataset.cache()
dataset = dataset.batch(64)
dataset = dataset.prefetch(tf.data.AUTOTUNE)
```

## Best Practices

1. **Set random seeds** for reproducibility: `tf.random.set_seed(42)` and `np.random.seed(42)`.
2. **Use `tf.function`** to decorate training and inference functions for graph compilation.
3. **Log with TensorBoard** using the TensorBoard callback; monitor scalars, histograms, and images.
4. **Validate with `tf.config.run_functions_eagerly(False)`** to ensure graph mode works correctly.
5. **Freeze layers** during fine-tuning by setting `layer.trainable = False` for initial epochs.
6. **Use `ModelCheckpoint`** with `save_weights_only=True` to save disk space.
7. **Profile performance** using `tf.profiler.experimental.start()` and stop tracing for bottlenecks.
8. **Apply `tf.keras.utils.set_random_seed`** for deterministic operations where possible.
9. **Normalize inputs** to zero mean and unit variance or scale to [0,1] for stable training.
10. **Use `tf.keras.mixed_precision`** on modern GPUs for 2-3x training speedup.

## Common Mistakes

1. **Not resetting metrics** between epochs in custom loops, causing incorrect epoch-level reporting.
2. **Calling `.numpy()` on tensors inside `tf.function`** which disables graph tracing and slows execution.
3. **Using Python-side augmentation** inside `tf.data.Dataset.map` without `tf.py_function` wrapper.
4. **Forgetting `training=True`** in `call()` during training for dropout/batch norm layers.
5. **Overlapping train and test data** through improper `tf.data.Dataset` sharding.
6. **Not using `prefetch`** causing GPU starvation while CPU processes the next batch.
7. **Saving subclassed models** with `save_weights_only=True` only; full model save may fail.
8. **Ignoring `input_shape`** argument in first layer, causing shape inference errors.
9. **Using `model.evaluate`** on a dataset that is not batched identically to training.
10. **Applying gradient clipping** incorrectly: use `clipnorm=1.0` or `clipvalue=0.5` in optimizer.

## Libraries

- `tensorflow` - Core framework for ML and deep learning
- `tensorflow-datasets` - Curated datasets as tf.data.Datasets
- `tensorflow-hub` - Pretrained model repository
- `tensorflow-model-optimization` - Model compression toolkit
- `tensorflow-probability` - Probabilistic modeling and Bayesian deep learning
- `tensorflow-text` - Text preprocessing ops
- `tensorflow-addons` - Community-contributed layers and ops
- `tfx` - Production ML pipeline framework
- `tensorflow-serving` - Model serving infrastructure
- `tflite` - Mobile and edge deployment runtime

## Design Principles

1. **Composability** - Build complex models from simple, reusable layer components.
2. **Eager Execution First** - Debug eagerly, deploy with graph compilation for performance.
3. **Data Pipeline Decoupling** - Separate data preparation from model code using `tf.data`.
4. **Progressive Disclosure** - Start with high-level Keras APIs, drop down to low-level APIs as needed.
5. **Determinism by Default** - Seed random operations and log seeds for reproducibility.
6. **Graph Optimization** - Rely on XLA compilation and Grappler for automatic optimization.
7. **Hardware Agnosticism** - Write once, deploy on CPU, GPU, or TPU without code changes.

## Coding Standards

1. **Import convention**: `import tensorflow as tf` and `from tensorflow import keras`.
2. **Model class names**: Capitalized CamelCase extending `tf.keras.Model`.
3. **Layer naming**: Use descriptive `name` parameter in layers for graph readability.
4. **Shape documentation**: Document expected tensor shapes in docstrings as `(batch, seq_len, features)`.
5. **Configuration dictionaries**: Pass hyperparameters as `config` dicts instead of individual arguments.
6. **Type hints**: Use `tf.Tensor` type annotations for inputs and return values.
7. **Checkpointing**: Save checkpoints every N steps, not just at epoch end for long training.
8. **Logging**: Use `tf.summary` for scalar, histogram, and image logging to TensorBoard.
9. **Testing**: Write unit tests for custom layers, losses, and metrics using `tf.test.TestCase`.
10. **Version pinning**: Pin `tensorflow>=2.12,<2.16` in requirements for stability.
