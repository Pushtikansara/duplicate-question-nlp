---
name: matplotlib
description: Use when creating data visualizations with Matplotlib. Covers figures, axes, plot types, customization, and saving.
---

# Matplotlib Skill

## Overview
Matplotlib is a comprehensive library for creating static, animated, and interactive visualizations in Python. It produces publication-quality figures in a variety of hardcopy formats and interactive environments across platforms. It provides a MATLAB-like interface with object-oriented API for fine-grained control.

## Instructions
- Use the object-oriented API (`fig, ax = plt.subplots()`) over the pyplot state machine for complex figures
- Use `plt.subplots()` with `figsize` parameter to set figure dimensions upfront
- Use `ax.plot()`, `ax.scatter()`, `ax.bar()` etc. on Axes objects for creating plots
- Set figure size, labels, titles, and legends explicitly rather than relying on defaults
- Use `fig.tight_layout()` or `constrained_layout=True` to prevent overlapping elements
- Customize fonts with `plt.rcParams.update()` for consistent styling across plots
- Use `ax.spines` to customize axis spines (visibility, position, color)
- Use `ax.grid()` for grid lines with customizable style
- Use `savefig()` with `dpi`, `bbox_inches='tight'`, and `transparent` for publication-quality output
- Use `colormaps` with `vmin`/`vmax` for consistent color mapping across subplots
- Use `.mplstyle` files or `plt.style.use()` for consistent plot styling
- Always close figures with `plt.close(fig)` when generating many plots to avoid memory leaks

## Core Concepts

### Figure and Axes
- **Figure**: The top-level container for all plot elements
- **Axes**: The plotting area with data space, ticks, labels, title
- One figure can contain multiple axes (subplots)
- `fig, ax = plt.subplots()` — single axis
- `fig, axes = plt.subplots(nrows=2, ncols=3)` — grid of axes
- `fig.add_axes([left, bottom, width, height])` — arbitrary axes placement
- `fig.subplots_adjust()` for spacing between subplots

### Pyplot vs OO API
- **Pyplot**: `plt.plot()`, `plt.xlabel()`, `plt.title()` — MATLAB-like, uses "current" figure/axes
- **OO API**: `ax.plot()`, `ax.set_xlabel()`, `ax.set_title()` — explicit, better for complex layouts
- OO API is strongly preferred for production code and multi-subplot figures
- Pyplot is convenient for interactive work and simple single-plot scripts

### Plot Types

#### Line Plots
- `ax.plot(x, y)` — basic line plot
- `ax.plot(x, y, '-o', color='blue', linewidth=2, markersize=6)` — styled line with markers
- `ax.fill_between(x, y1, y2)` — filled region between curves
- `ax.step(x, y)` — step plot
- `ax.stackplot(x, y1, y2, ...)` — stacked area plot

#### Scatter Plots
- `ax.scatter(x, y)` — basic scatter
- `ax.scatter(x, y, c=colors, s=sizes, alpha=0.5, cmap='viridis')` — styled scatter with color and size mapping
- `ax.scatter(x, y, marker='s', edgecolors='black', linewidths=0.5)` — with edge styling

#### Bar Plots
- `ax.bar(x, height)` — vertical bar chart
- `ax.barh(y, width)` — horizontal bar chart
- `ax.bar(x, height, bottom=y_bottom)` — stacked bars
- `ax.bar(x, height, width=0.8)` — bar width control

#### Histograms
- `ax.hist(data, bins=30)` — histogram with automatic bins
- `ax.hist(data, bins='auto', density=True, alpha=0.7)` — normalized histogram
- `ax.hist2d(x, y, bins=50, cmap='Blues')` — 2D histogram
- `ax.hist(data, bins=np.logspace(...))` — log-spaced bins for broad distributions

#### Box and Violin Plots
- `ax.boxplot(data)` — box plot (median, quartiles, outliers)
- `ax.boxplot(data, vert=False, widths=0.5, patch_artist=True)` — horizontal box plot
- `ax.violinplot(data, showmeans=True, showmedians=True)` — violin plot (density + box)

#### Heatmaps and Images
- `ax.imshow(data, cmap='viridis', aspect='auto')` — display image or 2D array
- `ax.contour(X, Y, Z, levels=10)` — contour plot
- `ax.contourf(X, Y, Z, cmap='RdYlBu_r')` — filled contour plot
- `ax.pcolormesh(X, Y, Z, shading='auto', cmap='viridis')` — pseudocolor mesh (for gridded data)

#### Error Bars
- `ax.errorbar(x, y, yerr=errors, fmt='o', capsize=3)` — vertical error bars
- `ax.errorbar(x, y, xerr=xerr, yerr=yerr, fmt='none', ecolor='gray')` — both axes error bars

### Customization

#### Labels and Titles
```python
ax.set_xlabel('X Axis Label (units)', fontsize=12, fontweight='bold')
ax.set_ylabel('Y Axis Label (units)', fontsize=12)
ax.set_title('Plot Title', fontsize=14, pad=15)
ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
```

#### Ticks and Tick Labels
```python
ax.set_xticks([0, 1, 2, 3, 4])
ax.set_xticklabels(['Zero', 'One', 'Two', 'Three', 'Four'], rotation=45)
ax.tick_params(axis='both', labelsize=10, pad=5)
ax.xaxis.set_major_locator(plt.MaxNLocator(5))
ax.xaxis.set_major_formatter(plt.FormatStrFormatter('%.2f'))
```

#### Spines and Grids
```python
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_position(('outward', 10))
ax.grid(True, which='major', linestyle='--', alpha=0.7)
ax.set_axisbelow(True)  # grid behind data
```

#### Text and Annotations
```python
ax.text(x, y, 'Text', fontsize=10, ha='center', va='center')
ax.annotate('Max', xy=(x_max, y_max), xytext=(x_max+0.1, y_max+0.1),
            arrowprops=dict(facecolor='black', shrink=0.05))
```

### Colormaps
- Sequential: `'viridis'`, `'plasma'`, `'inferno'`, `'magma'`, `'Blues'`
- Diverging: `'RdBu'`, `'PiYG'`, `'coolwarm'`, `'Spectral'`
- Qualitative: `'Set1'`, `'Set2'`, `'tab10'`, `'Pastel1'`
- Cyclic: `'twilight'`, `'hsv'`
- Use `cmap='viridis'` as default — it's perceptually uniform and colorblind-friendly
- Add colorbars: `fig.colorbar(im, ax=ax, label='Value')`
- Reverse with `_r` suffix: `'viridis_r'`

## Examples

### Multi-Panel Figure with Shared Axes
```python
import matplotlib.pyplot as plt
import numpy as np

# Create figure with 2x2 subplots, sharing x and y axes
fig, axes = plt.subplots(2, 2, figsize=(10, 8), sharex='col', sharey='row')
fig.suptitle('Multi-Panel Analysis', fontsize=14, fontweight='bold')

x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)
y3 = np.exp(-x/3) * np.sin(x)
y4 = x ** 0.5 * np.sin(x)

# Top-left
axes[0, 0].plot(x, y1, color='#1f77b4', linewidth=2)
axes[0, 0].set_title('Sine')
axes[0, 0].grid(True, alpha=0.3)

# Top-right
axes[0, 1].plot(x, y2, color='#ff7f0e', linewidth=2)
axes[0, 1].set_title('Cosine')
axes[0, 1].grid(True, alpha=0.3)

# Bottom-left
axes[1, 0].plot(x, y3, color='#2ca02c', linewidth=2)
axes[1, 0].set_title('Damped Sine')
axes[1, 0].set_xlabel('Time (s)')
axes[1, 0].grid(True, alpha=0.3)

# Bottom-right
axes[1, 1].plot(x, y4, color='#d62728', linewidth=2)
axes[1, 1].set_title('Amplified Sine')
axes[1, 1].set_xlabel('Time (s)')
axes[1, 1].grid(True, alpha=0.3)

fig.tight_layout()
plt.show()
```

### Publication-Quality Figure
```python
import matplotlib.pyplot as plt
import numpy as np

# Use a style
plt.style.use('seaborn-v0_8-paper')

# Configure rcParams for consistent styling
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})

# Generate data
rng = np.random.default_rng(42)
x = np.arange(1, 13)
y_mean = 10 + 2 * np.sin(x * 2 * np.pi / 12)
y_std = 0.5 + 0.3 * np.random.random(12)
y_obs = y_mean + rng.normal(0, y_std, size=(20, 12))

fig, ax = plt.subplots(figsize=(8, 5))

# Plot with error band
ax.plot(x, y_mean, '-o', color='#1f77b4', linewidth=2, label='Mean', zorder=3)
ax.fill_between(x, y_mean - y_std, y_mean + y_std,
                alpha=0.2, color='#1f77b4', label='±1 Std Dev')

# Individual observations with jitter
for i in range(y_obs.shape[0]):
    jitter = rng.uniform(-0.15, 0.15, size=12)
    ax.scatter(x + jitter, y_obs[i], s=8, alpha=0.3, color='gray', zorder=1)

# Customization
ax.set_xlabel('Month')
ax.set_ylabel('Measurement (units)')
ax.set_title('Annual Pattern with Observations')
ax.set_xticks(x)
ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
ax.legend(loc='upper right', framealpha=0.9)
ax.grid(True, which='major', linestyle=':', alpha=0.5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.show()
```

### Heatmap with Colorbar
```python
import matplotlib.pyplot as plt
import numpy as np

# Generate correlation matrix
n_vars = 8
corr = np.zeros((n_vars, n_vars))
for i in range(n_vars):
    for j in range(n_vars):
        corr[i, j] = 0.8 ** abs(i - j)  # autoregressive correlation

labels = ['Var A', 'Var B', 'Var C', 'Var D', 'Var E', 'Var F', 'Var G', 'Var H']

fig, ax = plt.subplots(figsize=(8, 7))
im = ax.imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1, aspect='equal')

# Add text annotations
for i in range(n_vars):
    for j in range(n_vars):
        ax.text(j, i, f'{corr[i, j]:.2f}',
                ha='center', va='center',
                color='white' if abs(corr[i, j]) > 0.5 else 'black',
                fontsize=9)

# Labels
ax.set_xticks(range(n_vars))
ax.set_yticks(range(n_vars))
ax.set_xticklabels(labels, rotation=45, ha='right')
ax.set_yticklabels(labels)

# Colorbar
cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label('Pearson Correlation', rotation=270, labelpad=15)

ax.set_title('Correlation Matrix')
plt.tight_layout()
plt.show()
```

### Composition Plot (Pie + Bar)
```python
import matplotlib.pyplot as plt

fig = plt.figure(figsize=(12, 5))

# Pie chart for market share
ax1 = fig.add_subplot(121)
categories = ['Product A', 'Product B', 'Product C', 'Product D', 'Other']
shares = [35, 25, 20, 12, 8]
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#7f7f7f']
explode = (0.05, 0, 0, 0, 0)

wedges, texts, autotexts = ax1.pie(
    shares, labels=categories, autopct='%1.1f%%',
    explode=explode, colors=colors, startangle=90,
    textprops={'fontsize': 10},
)
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')
ax1.set_title('Market Share by Product')

# Bar chart for growth rate
ax2 = fig.add_subplot(122)
growth = [5.2, 3.8, 7.1, -1.2, 0.5]
bars = ax2.bar(categories, growth, color=colors, edgecolor='white', linewidth=0.5)
ax2.axhline(y=0, color='black', linewidth=0.5)
ax2.set_title('Year-over-Year Growth')
ax2.set_ylabel('Growth (%)')

# Color bars by sign
for bar, val in zip(bars, growth):
    bar.set_color('#2ca02c' if val >= 0 else '#d62728')

plt.tight_layout()
plt.show()
```

## Best Practices
- Use `fig, ax = plt.subplots()` consistently — avoid using `plt.gca()` and `plt.gcf()`
- Set figure size before plotting: `plt.subplots(figsize=(width, height))` in inches
- Use vector formats (PDF, SVG) for publications; PNG for web (300 DPI minimum)
- Use perceptually uniform colormaps (`viridis`/`plasma`) instead of `jet`/`rainbow`
- Add grid lines with low alpha for reference without distracting from data
- Use semantic colors: red for negative/danger, green for positive/success, blue for primary data
- Label all axes with units in parentheses when applicable
- Use `scatter()` with `alpha` for overlapping points (overplotting)
- Use `ax.set_aspect('equal')` for plots where aspect ratio matters
- Always include a legend when plotting multiple datasets
- Use log scales with `ax.set_xscale('log')` for data spanning orders of magnitude
- Use `ax.invert_xaxis()` / `ax.invert_yaxis()` for appropriate axis orientation
- Use `markevery` for downsampling markers in dense line plots
- Remove unnecessary spines (top and right) for cleaner appearance

## Common Mistakes
- Using pyplot state machine when OO API would be clearer (mixing `plt.plot()` and `ax.plot()`)
- Forgetting to call `fig.tight_layout()` or `constrained_layout=True` (overlapping elements)
- Using `jet` colormap which is not perceptually uniform and distorts data perception
- Not setting figure size before plotting — default is too small for complex figures
- Using too many colors in a single plot (limit to 6-8 distinguishable colors)
- Not handling overplotting in scatter plots (use alpha, hexbin, or 2D histograms)
- Nesting `plt.subplots()` calls — creates unnecessary figures
- Plotting all data points in large datasets (use downsampling or rasterization)
- Using pie charts with many categories (hard to read; bar charts are often better)
- Not considering colorblindness (use patterns/markers in addition to color)
- Saving figures with `plt.savefig()` without specifying `dpi` (default 100 is low)
- Forgetting to close figures with `plt.close()` in loops (memory leak)

## Libraries
- **seaborn** — statistical data visualization (built on matplotlib, high-level API)
- **plotly** — interactive web-based visualizations
- **bokeh** — interactive visualization library for browser
- **ggplot** — R-like grammar of graphics (based on matplotlib)
- **cartopy** — geospatial data mapping
- **networkx** — network/graph visualization (uses matplotlib)
- **basemap** — map plotting (legacy; use cartopy)
- **proplot** — wrapper for matplotlib with better subplot layout and styling
- **scienceplots** — publication-quality styling for scientific papers
- **mplcursors** — interactive data cursors for matplotlib
- **matplotlib-venn** — Venn diagram plotting
- **adjustText** — automatic label positioning to avoid overlap
- **pillow** — image loading/saving used by matplotlib internally

## Design Principles
- **Publication Quality**: Defaults designed for scientific publication standards
- **Full Control**: Every element of a figure can be customized
- **Layered Architecture**: Figure → Axes → Lines/Markers/Text with hierarchical styling
- **Consistent API**: Similar methods across different plot types
- **Interactive and Static**: Same code works for screen display and file output
- **Backend Independence**: Same code works with different rendering engines (Agg, PDF, SVG, TkAgg, WebAgg)

## Coding Standards
- Import as `import matplotlib.pyplot as plt`
- OO API for production code: `fig, ax = plt.subplots()`
- Pyplot API only for quick interactive work or very simple scripts
- Variable naming: `fig`, `ax` for single, `axes` for arrays, `im` for images
- Use `fig.savefig()` not `plt.savefig()` for explicit control
- Define plotting functions that take data and return figure objects
- Use `from matplotlib import rcParams` for global settings
- Use `with plt.style.context('ggplot'):` for temporary style changes
- Configure styles in a central `plot_style.py` or `.mplstyle` file
- Use `pathlib.Path` for file paths when saving figures
- Test with `plt.close('all')` at the beginning of scripts for isolation

## Customization Checklist
- [ ] Figure size appropriate for content and output medium
- [ ] Axis labels with units
- [ ] Title (if needed for context)
- [ ] Legend with clear labels (when multiple datasets)
- [ ] Tick labels readable (rotation if needed)
- [ ] Color scheme (perceptually uniform, colorblind-friendly)
- [ ] Grid lines (subtle, not overpowering)
- [ ] Axis limits (no excess whitespace unless meaningful)
- [ ] Line widths and marker sizes (visible at output size)
- [ ] Font sizes (readable at final display size)
- [ ] Annotations (key points, outliers, trends)
- [ ] Aspect ratio (appropriate for data type)
- [ ] Spines (remove top/right for cleaner look)
- [ ] Tight layout (no overlapping elements)
- [ ] File format (SVG/PDF for publication, PNG for web)
- [ ] DPI (300+ for print, 150 for screen)

## Saving and Exporting
- `fig.savefig('figure.pdf', bbox_inches='tight')` — vector format, tight crop
- `fig.savefig('figure.png', dpi=300, bbox_inches='tight')` — raster, high DPI
- `fig.savefig('figure.svg', transparent=True)` — SVG with transparent background
- `fig.savefig('figure.jpg', quality=95, dpi=200)` — JPEG for photographs
- Use `bbox_inches='tight'` to remove extra whitespace
- Use `pad_inches=0.1` with `bbox_inches='tight'` for slight padding
- Use `transparent=True` for overlay on colored backgrounds
- Use `facecolor` and `edgecolor` parameters to set background colors
- For publications: submit as PDF with embedded fonts (set `rcParams['pdf.fonttype'] = 42`)
- For web: use PNG at 2x resolution for retina displays (200-300 DPI)
- Use `plt.style.use('tableau-colorblind10')` for colorblind-safe defaults
- Embed fonts with `rcParams['svg.fonttype'] = 'none'` (SVG) or `'path'` (paths) for cross-platform consistency
