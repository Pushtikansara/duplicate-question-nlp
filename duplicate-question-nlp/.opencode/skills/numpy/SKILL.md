---
name: numpy
description: Use when performing numerical computations with NumPy. Covers arrays, broadcasting, vectorization, linear algebra, and random sampling.
---

# NumPy Skill

## Overview
NumPy is the fundamental package for scientific computing in Python. It provides a powerful N-dimensional array object, sophisticated broadcasting functions, tools for integrating C/C++ and Fortran code, and useful linear algebra, Fourier transform, and random number capabilities. It serves as the bedrock for the entire Python data science and machine learning ecosystem.

## Instructions
- Use `np.array()` for creating arrays from lists; use `np.zeros()`, `np.ones()`, `np.empty()` for initialized arrays
- Always use vectorized operations over Python loops — NumPy operations are implemented in C
- Use `dtype` parameter to control memory usage and precision (e.g., `np.float32` vs `np.float64`)
- Prefer `np.loadtxt()` and `np.genfromtxt()` for reading text data; use `np.save()`/`np.load()` for binary
- Use `np.memmap` for arrays too large to fit in memory
- Use `np.einsum()` for complex tensor contractions with clear notation
- Use `np.where()` for conditional array operations instead of loops
- Use `np.vectorize()` for applying functions element-wise to arrays
- Use `np.ufunc.reduce()` for cumulative operations across axes
- Use `axis` parameter consistently across all aggregation functions
- Use `keepdims=True` when broadcasting after reduction is needed
- Use `out` parameter to avoid unnecessary array allocation in memory-constrained environments

## Core Concepts

### ndarray (N-dimensional Array)
- Homogeneous data container: all elements have the same type
- Shape: tuple of dimension sizes `(n_rows, n_cols, ...)`
- dtype: data type (`int32`, `float64`, `complex128`, `bool`, `object`)
- Strides: bytes to skip to move to the next element along each axis
- Contiguous memory layout (row-major C order by default)
- Indexing: `arr[i, j]`, slicing `arr[1:5, 2:7]`, fancy indexing `arr[[0, 2, 4]]`, boolean indexing `arr[arr > 0]`

### Array Creation
```python
import numpy as np

# From Python lists
arr = np.array([[1, 2, 3], [4, 5, 6]])

# Pre-allocated arrays
zeros = np.zeros((3, 4), dtype=np.float32)
ones = np.ones((2, 5), dtype=np.int8)
empty = np.empty((100, 100))  # uninitialized (fast but contains garbage)
full = np.full((3, 3), fill_value=42)
eye = np.eye(5)  # identity matrix

# Sequences
linear = np.arange(0, 10, 2)  # [0, 2, 4, 6, 8]
spaced = np.linspace(0, 1, 5)  # [0., 0.25, 0.5, 0.75, 1.]
log_spaced = np.logspace(-3, 3, 7)  # logarithmic spacing

# Random
rng = np.random.default_rng(seed=42)
rand = rng.random((3, 3))  # uniform [0, 1)
normal = rng.normal(0, 1, size=(100,))  # standard normal
integers = rng.integers(0, 10, size=20)  # random integers
```

### Broadcasting
- Fundamental rule: arrays are compatible if their dimensions are equal or one of them is 1
- Trailing dimensions are compared; missing dimensions are treated as 1
- Broadcasting avoids creating large intermediate arrays
- Examples:
  - `(3,) + scalar` → `(3,)`
  - `(3, 4) + (4,)` → `(3, 4)`: `(4,)` is broadcast to `(1, 4)` then `(3, 4)`
  - `(3, 1) + (1, 4)` → `(3, 4)`: both are broadcast
  - `(3, 4) + (3, 1)` → `(3, 4)`: second array broadcast along columns
- Broadcasting fails when dimensions are incompatible: `(3, 4) + (2, 4)` raises ValueError

### Universal Functions (ufuncs)
- Operate element-wise on arrays
- Arithmetic: `np.add`, `np.subtract`, `np.multiply`, `np.divide`, `np.power`
- Trigonometry: `np.sin`, `np.cos`, `np.tan`, `np.arcsin`, `np.arctan2`
- Exponents and logs: `np.exp`, `np.log`, `np.log10`, `np.log2`
- Comparison: `np.greater`, `np.less`, `np.equal`, `np.isclose`
- Floating point: `np.floor`, `np.ceil`, `np.trunc`, `np.round`
- Cumulative: `np.cumsum`, `np.cumprod`
- Reduction: `np.add.reduce`, `np.multiply.reduce`
- `np.where(condition, x, y)` — conditional element selection
- `np.clip(arr, min, max)` — clamp values to range

### Aggregation and Statistics
- `np.sum`, `np.mean`, `np.median`, `np.std`, `np.var`, `np.min`, `np.max`
- `np.argmin`, `np.argmax` — indices of min/max values
- `np.percentile`, `np.quantile` — distribution statistics
- `np.corrcoef`, `np.cov` — correlation and covariance
- `np.histogram`, `np.bincount` — histogram and bin counting
- All support `axis` parameter; use `keepdims=True` to preserve dimensions

### Linear Algebra
- `np.dot(a, b)` / `a @ b` — matrix multiplication (Python 3.5+ uses @ operator)
- `np.linalg.inv` — matrix inverse
- `np.linalg.solve` — solve linear system Ax = b
- `np.linalg.eig` / `np.linalg.eigh` — eigenvalues and eigenvectors
- `np.linalg.svd` — singular value decomposition
- `np.linalg.qr` — QR decomposition
- `np.linalg.cholesky` — Cholesky decomposition (for positive definite matrices)
- `np.linalg.norm` — vector and matrix norms
- `np.linalg.det` — determinant
- `np.linalg.matrix_rank` — matrix rank
- `np.linalg.lstsq` — least squares solution

### Random Sampling
```python
rng = np.random.default_rng()

# Basic distributions
rng.uniform(low=0, high=1, size=(3, 3))
rng.normal(loc=0, scale=1, size=1000)
rng.exponential(scale=1, size=500)
rng.binomial(n=10, p=0.5, size=100)
rng.poisson(lam=3, size=200)
rng.gamma(shape=2, scale=1, size=300)

# Sampling and shuffling
rng.choice(['a', 'b', 'c'], size=10, p=[0.2, 0.5, 0.3])
rng.permutation(np.arange(10))  # shuffled copy
arr = np.arange(10)
rng.shuffle(arr)  # in-place shuffle
```

### Array Manipulation
- Reshaping: `arr.reshape(new_shape)`, `np.reshape(arr, new_shape)`
- Transpose: `arr.T`, `arr.transpose()`, `arr.swapaxes()`
- Flatten: `arr.flatten()` (copy), `arr.ravel()` (view if possible)
- Concatenation: `np.concatenate((a, b), axis=0)`, `np.vstack()`, `np.hstack()`, `np.dstack()`
- Splitting: `np.split()`, `np.vsplit()`, `np.hsplit()`
- Expanding dimensions: `np.expand_dims(arr, axis)`, `arr[np.newaxis, :]`
- Squeezing: `np.squeeze(arr)` — remove dimensions of size 1
- Padding: `np.pad(arr, pad_width, mode='constant')`

## Examples

### Vectorized Numerical Computation
```python
import numpy as np

def black_scholes_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Vectorized Black-Scholes call option pricing."""
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm_cdf(d1) - K * np.exp(-r * T) * norm_cdf(d2)

def norm_cdf(x: np.ndarray) -> np.ndarray:
    """Standard normal CDF using the error function."""
    return 0.5 * (1 + erf(x / np.sqrt(2)))

# Vectorized over arrays of parameters
S = np.linspace(80, 120, 1000)
K = 100
T = np.array([0.25, 0.5, 1.0, 2.0])
prices = black_scholes_call(S[:, np.newaxis], K, T[np.newaxis, :], 0.05, 0.2)
# prices shape: (1000, 4) — one price per spot value per time to maturity
```

### Efficient Image Processing
```python
import numpy as np

def rgb_to_grayscale(img: np.ndarray) -> np.ndarray:
    """Convert RGB image to grayscale using luminance weights."""
    return np.dot(img[..., :3], [0.2989, 0.5870, 0.1140])

def normalize_image(img: np.ndarray) -> np.ndarray:
    """Normalize image to [0, 1] range."""
    img_min = img.min()
    img_max = img.max()
    return (img - img_min) / (img_max - img_min)

def apply_convolution(img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Apply 2D convolution using FFT."""
    from scipy import signal
    return signal.convolve2d(img, kernel, mode='same', boundary='wrap')

# Sobel edge detection kernel
sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
edges = apply_convolution(normalize_image(img), sobel_x)
```

### Principal Component Analysis (PCA)
```python
import numpy as np

def pca(X: np.ndarray, n_components: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Perform PCA on data matrix X (n_samples, n_features)."""
    # Center the data
    X_centered = X - X.mean(axis=0)

    # Compute covariance matrix
    cov = np.cov(X_centered, rowvar=False)

    # Eigendecomposition
    eigenvalues, eigenvectors = np.linalg.eigh(cov)

    # Sort by eigenvalues descending
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # Select top components
    components = eigenvectors[:, :n_components]

    # Project data
    transformed = X_centered @ components

    # Explained variance ratio
    explained_ratio = eigenvalues[:n_components] / eigenvalues.sum()

    return transformed, components, explained_ratio

# Usage
X = rng.normal(size=(1000, 50))
transformed, comps, ratio = pca(X, n_components=10)
print(f"Explained variance: {ratio.sum():.2%}")
```

### Efficient Distance Matrix
```python
import numpy as np

def pairwise_euclidean(X: np.ndarray, Y: np.ndarray | None = None) -> np.ndarray:
    """
    Compute pairwise Euclidean distance matrix efficiently.
    Uses the identity: ||x - y||^2 = ||x||^2 + ||y||^2 - 2 x·y
    """
    if Y is None:
        Y = X
    X_norm = np.sum(X ** 2, axis=1, keepdims=True)
    Y_norm = np.sum(Y ** 2, axis=1, keepdims=True)
    return np.sqrt(
        X_norm + Y_norm.T - 2 * np.dot(X, Y.T)
    )

def cosine_similarity(X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Compute cosine similarity matrix."""
    X_norm = X / np.linalg.norm(X, axis=1, keepdims=True)
    Y_norm = Y / np.linalg.norm(Y, axis=1, keepdims=True)
    return X_norm @ Y_norm.T
```

## Best Practices
- Use `np.array(..., dtype=...)` to control memory usage; `float32` and `int16` for large datasets
- Use `np.clip()` to handle outliers before computing statistics
- Use `np.isclose()` and `np.allclose()` for floating-point comparisons (never `==`)
- Use `np.nan_to_num()` for arrays with NaN values in numerical operations
- Use `np.set_printoptions()` for configuring display of large arrays
- Use `out` parameter in ufuncs to overwrite existing arrays and reduce memory allocation
- Use `np.broadcast_to()` for memory-efficient broadcasting (avoids data copying)
- Use `np.shares_memory()` to check if two arrays share data
- Use `np.ndarray.view()` to change dtype without copying
- Sort by column: `arr[arr[:, col].argsort()]`
- Use `np.unique()` with `return_counts=True` for value counting
- Use `np.searchsorted()` in sorted arrays for fast insertion point finding

## Common Mistakes
- Not specifying `dtype` and getting default `float64` (2x memory of `float32`)
- Using Python lists and loops instead of vectorized NumPy operations (100-1000x slower)
- Confusing `np.dot()` vs `np.multiply()` vs `@` operator for matrix operations
- Modifying a view and thinking it doesn't affect the original array
- Not understanding broadcasting rules leads to cryptic shape errors
- Using `np.append()` in a loop (O(n²)); pre-allocate with `np.zeros()` instead
- Checking array equality with `==` (returns element-wise bool array; use `np.array_equal()`)
- Forgetting that slicing returns a view (not a copy) — mutations affect the original
- Using `np.random.seed()` (legacy API) instead of `np.random.default_rng()` (modern API)
- Not handling NaN values in aggregations (use `np.nansum()`, `np.nanmean()`, etc.)
- Using `np.reshape()` where `np.resize()` is needed (reshape doesn't change total size)
- Assuming C-contiguous layout when interacting with C libraries (use `np.ascontiguousarray()`)

## Libraries
- **scipy** — scientific computing (optimization, signal processing, statistics)
- **scikit-learn** — machine learning built on NumPy
- **numba** — JIT compilation for NumPy array operations (loop vectorization)
- **dask** — parallel computation with NumPy-like API for larger-than-memory data
- **cupy** — GPU-accelerated NumPy for CUDA-capable GPUs
- **jax** — GPU/TPU-accelerated NumPy with automatic differentiation
- **xarray** — labeled multi-dimensional arrays with dataset-aware operations
- **numpy-stl** — fast NumPy-backed array storage and I/O
- **bottleneck** — C-accelerated array functions (nanmoving_mean, etc.)
- **numpyro** — probabilistic programming with NumPy backend
- **pandas** — built on NumPy for labeled tabular data
- **matplotlib** — plotting with NumPy arrays as input

## Design Principles
- **Homogeneous Arrays**: All elements have the same type for efficient storage and vectorized operations
- **Vectorized Operations**: Operations apply to entire arrays without explicit loops
- **Broadcasting**: Arrays of different shapes can be used in arithmetic operations
- **Views vs Copies**: Most operations return views to avoid unnecessary data copying
- **Contiguous Memory**: Arrays are stored in contiguous blocks for cache efficiency
- **N-dimensional Universality**: The same API works for 1D, 2D, and N-dimensional data

## Coding Standards
- Import as `import numpy as np`
- Use descriptive variable names: `samples`, `features`, `weights`, `gradients`
- Use `_` suffix for temporary arrays: `tmp_`, `mask_`
- Use `shape` tuple consistently throughout code
- Use `axis=` parameter explicitly (not positional) for clarity
- Use `dtype=` parameter for explicit type specification
- Document assumptions about array shapes in function docstrings
- Add `np.newaxis` / `None` explicitly for broadcasting dimensions
- Use `np.errstate()` context manager to control floating-point error handling
- Use `np.testing.assert_array_almost_equal` in tests

## Performance Tips
- Use `float32` instead of `float64` when precision requirements allow (2x speed, 2x memory)
- Pre-allocate arrays with `np.zeros()` or `np.empty()` instead of `np.append()` or `np.concatenate()` in loops
- Use `np.einsum()` with `optimize=True` for complex tensor contractions
- Use `out` parameter to reuse memory: `np.multiply(a, b, out=a)`
- Use `np.ufunc.reduceat()` for segmented operations
- Use `numba.jit(nopython=True)` for loops that cannot be vectorized
- Use `np.where()` over boolean indexing when modifying in place
- Use `np.ndarray.flat` for fast iteration if a loop is absolutely necessary
- Use `np.ndarray.view()` with different dtype for in-memory reinterpretation
- Use `np.broadcast_arrays()` explicitly when multiple broadcasts interact
- Use `np.matmul` / `@` for batched matrix multiplication (optimized BLAS)
- Use `np.linalg.multi_dot()` for chains of matrix multiplications (optimal order)
- Use `np.fft.fft()` for circular convolutions (O(n log n) vs O(n²))

## Memory Layout
- **C Order (Row-Major)**: Default; contiguous along the last axis
- **Fortran Order (Column-Major)**: Contiguous along the first axis
- Use `order='F'` for compatibility with Fortran libraries and column-wise operations
- `np.ascontiguousarray()` ensures C order; `np.asfortranarray()` ensures F order
- `arr.strides` gives bytes to step along each dimension
- `arr.flags` indicates memory layout (C_CONTIGUOUS, F_CONTIGUOUS, OWNDATA)
- Transposing returns a view with swapped strides (no data copy)
- Use `copy()` before modifying when you need an independent array

## Testing
- Use `np.testing.assert_array_equal()` for exact equality
- Use `np.testing.assert_array_almost_equal()` for floating-point tolerance
- Use `np.testing.assert_allclose()` with `rtol` and `atol` parameters
- Use `np.testing.assert_raises()` for expected error conditions
- Test with edge cases: empty arrays, single-element, all same value, NaN/Inf
- Test broadcasting behavior with arrays of various shapes
- Test random operations with fixed seed for reproducibility
- Compare vectorized implementations against naive loop versions for correctness
- Use `pytest-benchmark` for regression testing of performance
- Test `dtype` preservation and upcasting rules
- Test views vs copies behavior to ensure memory independence
