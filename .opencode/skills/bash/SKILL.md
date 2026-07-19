---
name: bash
description: Use when writing shell scripts. Covers syntax, control flow, functions, error handling, and best practices.
---

# Bash Skill

## Instructions

Bash (Bourne Again SHell) is the most widely used Unix/Linux shell and scripting language. It provides powerful features for automating tasks, processing text, managing files, and orchestrating system operations. This skill covers Bash scripting syntax, control flow, functions, error handling, and professional best practices.

### Shebang and Script Setup

Every Bash script should start with a shebang and strict mode settings:

```bash
#!/bin/bash
# -e: Exit on any error
# -u: Treat unset variables as errors
# -o pipefail: Pipeline exit code is the last non-zero command
set -euo pipefail

# Optional: Enable debugging
# set -x
# set -v
```

### Variables

```bash
# Assignment (no spaces around =)
name="John"
age=30

# Using variables
echo "$name is $age years old"
message="Hello, ${name}!"  # Braces for clarity

# Command substitution
current_date=$(date +%Y-%m-%d)
files=$(ls -la)

# Arithmetic
result=$((5 + 3 * 2))
counter=$((counter + 1))

# Special variables
$0          # Script name
$1, $2, ... # Positional arguments
$@          # All arguments as separate words
$*          # All arguments as single word
$#          # Number of arguments
$?          # Exit code of last command
$$          # PID of current script
$!          # PID of last background process
$LINENO     # Current line number
```

### Arrays

```bash
# Indexed arrays
fruits=("apple" "banana" "cherry")
echo "${fruits[0]}"       # apple
echo "${fruits[@]}"       # All elements
echo "${#fruits[@]}"      # Length

# Associative arrays (Bash 4+)
declare -A user
user[name]="John"
user[email]="john@example.com"
echo "${user[name]}"
```

### Strings

```bash
# String operations
name="John Doe"
echo "${#name}"                      # Length: 8
echo "${name:0:4}"                   # Substring: John
echo "${name/Doe/Smith}"             # Replace first
echo "${name//o/a}"                  # Replace all
echo "${name,,}"                     # Lowercase
echo "${name^^}"                     # Uppercase
echo "${name^}"                      # Capitalize first

# String comparison
[[ "$name" == "John" ]]             # Equality
[[ "$name" != "Jane" ]]             # Inequality
[[ -z "$empty" ]]                   # Empty string
[[ -n "$name" ]]                    # Non-empty string
[[ "hello" == h* ]]                 # Wildcard match
[[ "abc" =~ ^a.*c$ ]]              # Regex match

# Default values
echo "${var:-default}"              # Use default if unset/null
echo "${var:=default}"              # Assign default if unset/null
echo "${var:?error message}"        # Error if unset/null
```

## Examples

### Example 1: Command-Line Argument Parsing

```bash
#!/bin/bash
set -euo pipefail

usage() {
    cat <<EOF
Usage: $0 [options] <input-file>

Options:
    -o, --output FILE    Output file (default: stdout)
    -v, --verbose       Enable verbose output
    -d, --debug         Enable debug mode
    -h, --help          Show this help message
EOF
    exit 1
}

# Default values
output_file=""
verbose=false
debug=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            output_file="$2"
            shift 2
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        -d|--debug)
            debug=true
            set -x
            shift
            ;;
        -h|--help)
            usage
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage
            ;;
        *)
            input_file="$1"
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "${input_file:-}" ]]; then
    echo "Error: input file is required" >&2
    usage
fi

if [[ ! -f "$input_file" ]]; then
    echo "Error: file '$input_file' not found" >&2
    exit 1
fi

# Main logic
if [[ "$verbose" == true ]]; then
    echo "Processing: $input_file"
fi

process_file "$input_file" "$output_file"
```

### Example 2: File Processing with Error Handling

```bash
#!/bin/bash
set -euo pipefail

# Logging functions
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

# Cleanup function (runs on script exit)
cleanup() {
    local exit_code=$?
    log_info "Cleaning up..."
    if [[ -n "${temp_dir:-}" && -d "$temp_dir" ]]; then
        rm -rf "$temp_dir"
        log_info "Removed temporary directory: $temp_dir"
    fi
    exit "$exit_code"
}
trap cleanup EXIT

# Error handler
handle_error() {
    local line=$1
    local command=$2
    log_error "Error on line $line: $command"
}
trap 'handle_error $LINENO "$BASH_COMMAND"' ERR

process_directory() {
    local dir="$1"
    local output="$2"

    if [[ ! -d "$dir" ]]; then
        log_error "Directory does not exist: $dir"
        return 1
    fi

    temp_dir=$(mktemp -d)
    log_info "Created temp directory: $temp_dir"

    # Process files
    local count=0
    while IFS= read -r -d '' file; do
        if [[ -f "$file" ]]; then
            log_info "Processing: $file"
            # Process file here
            ((count++))
        fi
    done < <(find "$dir" -type f -print0)

    if [[ $count -eq 0 ]]; then
        log_info "No files found in $dir"
        return 0
    fi

    log_info "Processed $count files"
}

main() {
    local target_dir="${1:-.}"
    local output_file="${2:-/dev/stdout}"

    if ! command -v find &> /dev/null; then
        log_error "Required command 'find' not found"
        exit 1
    fi

    process_directory "$target_dir" "$output_file"
}

main "$@"
```

### Example 3: Text Processing with awk and sed

```bash
#!/bin/bash
set -euo pipefail

# Parse CSV file
parse_csv() {
    local file="$1"
    local delimiter="${2:-,}"

    if [[ ! -f "$file" ]]; then
        echo "Error: File not found" >&2
        return 1
    fi

    awk -v FS="$delimiter" -v OFS=" | " '
    NR == 1 {
        # Header row
        print "Header:", $0
        next
    }
    {
        # Data rows
        for (i = 1; i <= NF; i++) {
            printf "Column %d: %s\n", i, $i
        }
        print "---"
    }
    ' "$file"
}

# Find and replace in files
find_and_replace() {
    local search="$1"
    local replace="$2"
    local pattern="${3:-*}"
    local dry_run="${4:-false}"

    if [[ "$dry_run" == "true" ]]; then
        grep -rl "$search" --include="$pattern" . | while read -r file; do
            echo "Would modify: $file"
            grep -n "$search" "$file"
        done
    else
        find . -type f -name "$pattern" -exec sed -i "s/$search/$replace/g" {} +
        echo "Replacement complete"
    fi
}

# Log file analysis
analyze_logs() {
    local logfile="$1"

    if [[ ! -f "$logfile" ]]; then
        echo "Error: Log file not found" >&2
        return 1
    fi

    echo "=== Log Analysis ==="

    # Most frequent IP addresses
    echo "Top 10 IP addresses:"
    grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' "$logfile" |
        sort | uniq -c | sort -rn | head -10

    # HTTP status code distribution
    echo "HTTP Status Codes:"
    grep -oE 'HTTP/[0-9.]+" [0-9]{3}' "$logfile" |
        awk '{print $2}' | sort | uniq -c | sort -rn

    # Request methods
    echo "HTTP Methods:"
    grep -oE '"(GET|POST|PUT|DELETE|PATCH|HEAD)' "$logfile" |
        sort | uniq -c | sort -rn

    # Error rate
    local total total_errors
    total=$(wc -l < "$logfile")
    total_errors=$(grep -cE '" 5[0-9]{2}' "$logfile")
    printf "Error rate (5xx): %.2f%%\n" "$(echo "scale=4; $total_errors * 100 / $total" | bc)"
}

main() {
    analyze_logs "/var/log/nginx/access.log"
}

main "$@"
```

### Example 4: Parallel Processing with Subshells

```bash
#!/bin/bash
set -euo pipefail

# Parallel processing with job control
parallel_process() {
    local max_jobs="${1:-4}"
    local items=("${@:2}")
    local job_count=0

    for item in "${items[@]}"; do
        # Wait if we've reached max parallel jobs
        while [[ $(jobs -r | wc -l) -ge "$max_jobs" ]]; do
            sleep 1
        done

        # Start job in background
        (
            echo "Processing: $item"
            sleep $((RANDOM % 5 + 1))  # Simulate work
            echo "Finished: $item"
        ) &

        ((job_count++))
    done

    # Wait for all remaining jobs
    wait
    echo "All $job_count jobs completed"
}

# Using xargs for parallel execution
parallel_xargs() {
    local dir="$1"
    find "$dir" -type f -name "*.log" -print0 |
        xargs -0 -P 4 -I {} bash -c '
            echo "Processing: {}"
            wc -l "{}"
        '
}

# GNU parallel example (if installed)
parallel_gnu() {
    if command -v parallel &> /dev/null; then
        seq 10 | parallel -j 4 echo "Processing item {}"
    else
        echo "GNU parallel not installed"
    fi
}

# Batch processing with rate limiting
batch_process() {
    local batch_size=10
    local items=({1..50})
    local total=${#items[@]}

    for ((i=0; i<total; i+=batch_size)); do
        local batch=("${items[@]:i:batch_size}")
        echo "Processing batch $((i / batch_size + 1))"

        for item in "${batch[@]}"; do
            echo "  Item: $item" &
        done
        wait

        echo "Batch $((i / batch_size + 1)) complete"
    done
}

main() {
    local items=("file1" "file2" "file3" "file4" "file5")
    parallel_process 2 "${items[@]}"
}

main "$@"
```

### Example 5: Configuration File Parser

```bash
#!/bin/bash
set -euo pipefail

# Parse INI-style config file
parse_ini() {
    local file="$1"
    local section=""
    local line_num=0

    if [[ ! -f "$file" ]]; then
        echo "Error: Config file not found" >&2
        return 1
    fi

    while IFS= read -r line; do
        ((line_num++))

        # Trim whitespace
        line="${line## }"
        line="${line%% }"

        # Skip comments and empty lines
        [[ -z "$line" ]] && continue
        [[ "$line" =~ ^[[:space:]]*# ]] && continue

        # Section header
        if [[ "$line" =~ ^\[(.+)\]$ ]]; then
            section="${BASH_REMATCH[1]}"
            continue
        fi

        # Key=value pair
        if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
            local key="${BASH_REMATCH[1]}"
            local value="${BASH_REMATCH[2]}"

            # Trim key/value
            key="${key## }"
            key="${key%% }"
            value="${value## }"
            value="${value%% }"

            # Remove quotes from value
            value="${value%\"}"
            value="${value#\"}"

            printf "CONFIG[%s][%s]='%s'\n" "$section" "$key" "$value"
        else
            echo "Warning: Invalid syntax at line $line_num" >&2
        fi
    done < "$file"
}

# Source a config file safely
safe_source() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        echo "Error: File not found: $file" >&2
        return 1
    fi

    # Validate file before sourcing
    if bash -n "$file" 2>/dev/null; then
        source "$file"
        echo "Sourced: $file"
    else
        echo "Error: Invalid Bash syntax in $file" >&2
        return 1
    fi
}

# YAML-like parser (simple)
parse_simple_yaml() {
    local file="$1"
    local prefix="${2:-config}"

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ "$line" =~ ^[[:space:]]*$ ]] && continue

        if [[ "$line" =~ ^[[:space:]]*([a-zA-Z_][a-zA-Z0-9_]*):[[:space:]]*(.*)$ ]]; then
            local key="${BASH_REMATCH[1]}"
            local value="${BASH_REMATCH[2]}"
            value="${value#\"}"
            value="${value%\"}"
            printf "declare -g %s_%s='%s'\n" "$prefix" "$key" "$value"
        fi
    done < "$file"
}

main() {
    # Create a sample config
    local config="/tmp/app.ini"
    cat > "$config" << 'CFG'
# Application configuration
[database]
host=localhost
port=5432
name=myapp

[logging]
level=info
file=/var/log/myapp.log
CFG

    parse_ini "$config"
    rm -f "$config"
}

main "$@"
```

### Example 6: Network Operations

```bash
#!/bin/bash
set -euo pipefail

# Health check with retry
health_check() {
    local url="$1"
    local max_retries="${2:-5}"
    local timeout="${3:-5}"

    for ((i=1; i<=max_retries; i++)); do
        if curl -sf -m "$timeout" "$url" &> /dev/null; then
            echo "Service is healthy: $url"
            return 0
        fi
        echo "Attempt $i/$max_retries: $url not reachable"
        sleep $((2 ** i))  # Exponential backoff
    done

    echo "Service unhealthy after $max_retries attempts: $url" >&2
    return 1
}

# Download with resume and progress
download_file() {
    local url="$1"
    local output="${2:-$(basename "$url")}"

    echo "Downloading: $url"

    if [[ -f "$output" ]]; then
        echo "Resuming partial download..."
        curl -C - -o "$output" "$url"
    else
        curl -L -o "$output" "$url"
    fi
}

# Port scan
port_scan() {
    local host="$1"
    local ports=(${@:2})

    echo "Scanning $host..."

    for port in "${ports[@]}"; do
        timeout 2 bash -c "echo >/dev/tcp/$host/$port" &>/dev/null &&
            echo "Port $port: OPEN" ||
            echo "Port $port: CLOSED" &
    done
    wait
}

# Extract SSL certificate info
ssl_info() {
    local host="$1"
    local port="${2:-443}"

    echo | openssl s_client -connect "${host}:${port}" -servername "$host" 2>/dev/null |
        openssl x509 -noout -dates -subject -issuer 2>/dev/null || {
        echo "Failed to get SSL info for $host:$port" >&2
        return 1
    }
}

main() {
    health_check "https://example.com" 3 2
}

main "$@"
```

### Example 7: Interactive Menu System

```bash
#!/bin/bash
set -euo pipefail

# Color codes
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'  # No Color

print_header() {
    local title="$1"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $title${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}" >&2
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

confirm_action() {
    local prompt="$1"
    local response

    read -p "$prompt [y/N] " response
    [[ "$response" =~ ^[Yy] ]]
}

select_option() {
    local prompt="$1"
    shift
    local options=("$@")
    local selected=0

    echo "$prompt"

    # Display options
    for i in "${!options[@]}"; do
        echo "$((i+1)). ${options[$i]}"
    done

    # Get selection
    read -p "Select (1-${#options[@]}): " choice
    if [[ "$choice" =~ ^[0-9]+$ ]] && ((choice >= 1 && choice <= ${#options[@]})); then
        return $((choice - 1))
    fi

    return 255
}

main_menu() {
    while true; do
        clear
        print_header "System Management Tool"

        select_option "Choose an option:" \
            "Check System Health" \
            "Backup Configuration" \
            "View Logs" \
            "Exit"

        case $? in
            0)
                echo "Running system health check..."
                sleep 1
                print_success "System healthy"
                ;;
            1)
                if confirm_action "Start backup?"; then
                    echo "Backing up..."
                    sleep 2
                    print_success "Backup complete"
                fi
                ;;
            2)
                echo "Recent log entries:"
                tail -5 /var/log/syslog 2>/dev/null || print_error "No log file"
                ;;
            3)
                print_info "Goodbye!"
                exit 0
                ;;
            255)
                print_error "Invalid option"
                ;;
        esac

        read -p "Press Enter to continue..."
    done
}

trap 'echo; print_warning "Interrupted"; exit 1' INT

main_menu
```

## Best Practices

### Script Design

- Always use `set -euo pipefail` for strict error handling
- Use functions to organize code into logical units
- Use `main` function pattern with `main "$@"` at the end
- Validate all inputs and arguments at the beginning of the script
- Provide a usage/help function for command-line interfaces
- Use meaningful exit codes (0 for success, 1-255 for errors)
- Implement cleanup actions with `trap`

### Error Handling

- Check exit codes of critical commands
- Use `||` for fallback on failure: `command || handle_error`
- Use `trap` for cleanup on exit and error signals
- Redirect error messages to stderr with `>&2`
- Use `-x` for debugging and `-n` for syntax checking
- Validate dependent commands are available before proceeding

### Security Practices

- Quote all variable expansions (`"$var"` not `$var`)
- Use `printf` instead of `echo` for predictable behavior
- Avoid `eval` at all costs (command injection risk)
- Use `read -r` to preserve backslashes in input
- Validate and sanitize all external input
- Use temporary files with `mktemp` not predictable paths
- Never store secrets in scripts; use environment variables or secret stores

### Performance Practices

- Use built-in Bash features instead of external commands where possible
- Avoid loops over large datasets; use `awk`, `sed`, or `find` with exec
- Use `while read` loops instead of `for` loops for file processing
- Use `$()` instead of backticks for command substitution
- Limit subshell creation for frequently executed code
- Use `printf` over `echo` in loops for better performance

## Common Mistakes

- **Not quoting variables**: Unquoted variables undergo word splitting and glob expansion, leading to bugs with filenames containing spaces.
- **Using `for` loops for file iteration**: For loops break with filenames containing spaces. Use `while IFS= read -r` with process substitution.
- **Forgetting `set -euo pipefail`: Without strict mode, scripts continue running after errors, causing cascading failures.
- **Not validating command existence**: Running commands that may not be installed causes cryptic errors. Use `command -v` to check.
- **Using `eval` for dynamic commands**: Eval executes arbitrary strings as commands, leading to injection vulnerabilities.
- **Hardcoding paths**: Hardcoded paths break when scripts are run from different directories. Use relative paths or detect the script's directory.
- **Not handling signals**: Without signal handlers, scripts leave temporary files and background processes when interrupted.
- **Using `cat` with piping unnecessarily**: `cat file | command` is a Useless Use of Cat (UUOC). Use `command < file` instead.
- **Not checking return codes**: Commands can fail silently. Always check exit codes or use `set -e`.
- **Assuming external tool availability**: Scripts should check for required tools and provide clear error messages if not found.

## Libraries

### Built-in Bash Features

| Feature | Usage |
|---------|-------|
| Brace Expansion | `{a,b,c}`, `{1..10}`, `{01..10}` |
| Globbing | `*.txt`, `**/*.log` (globstar) |
| Process Substitution | `<(command)`, `>(command)` |
| Here Documents | `cat << EOF`, `cat << 'EOF'` |
| Here Strings | `command <<< "$variable"` |
| Parameter Expansion | `${var:-default}`, `${var##prefix}` |
| Arithmetic Expansion | `$((expression))` |
| Regular Expressions | `[[ $str =~ pattern ]]` |

### External Tools Often Used in Scripts

| Tool | Purpose |
|------|---------|
| curl | HTTP requests and data transfer |
| jq | JSON processing |
| yq | YAML/JSON/XML processing |
| awk | Text processing and report generation |
| sed | Stream editor for text transformation |
| grep | Pattern search |
| find | File search and batch operations |
| xargs | Build and execute command lines |
| parallel | Execute jobs in parallel |
| rsync | File synchronization |
| ssh | Remote command execution |
| openssl | Cryptography and certificates |

## Design Principles

### Robustness

A well-written Bash script handles all edge cases: missing files, empty directories, unexpected input, network failures, and insufficient permissions. Every assumption should be validated, and every failure should produce a clear diagnostic message.

### Clarity

Scripts should be readable by other developers. Use descriptive variable names, comment complex logic, and break long commands into readable multi-line constructs. Prefer readability over clever one-liners.

### PORTABILITY

Write scripts that work across different Unix-like systems. Avoid Bash-specific features when they can be replaced with POSIX-compatible alternatives. Check for the availability of external tools before using them.

### Idempotency

Scripts should be safe to run multiple times. Creating a directory should check if it exists first. Writing configuration should handle the case where it already exists. Cleanup should handle already-cleaned state.

## Coding Standards

### Script Layout

```bash
#!/bin/bash
# 1. Shebang
set -euo pipefail

# 2. Constants and configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 3. Helper functions
log() { ... }
error() { ... }

# 4. Core functions
validate_input() { ... }
process_data() { ... }

# 5. Main function
main() { ... }

# 6. Execute main
main "$@"
```

### Naming Conventions

- Functions: `snake_case` (e.g., `get_file_size`, `validate_email`)
- Variables: `snake_case` for locals, `SNAKE_CASE` for constants
- Script files: `kebab-case.sh` (e.g., `deploy-app.sh`)
- Error codes: use named constants (`readonly ERR_FILE_NOT_FOUND=2`)

### Comment Style

```bash
# Single line comment

# Block comment explaining a complex section
# that spans multiple lines

# Function documentation
# Arguments:
#   $1: Source file path
#   $2: Destination directory
# Output:
#   Writes processed data to stdout
# Returns:
#   0 on success, 1 on failure
process_file() {
    ...
}
```
