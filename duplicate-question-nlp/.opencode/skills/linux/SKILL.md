---
name: linux
description: Use when working with Linux systems. Covers shell commands, file system, process management, permissions, and system administration.
---

# Linux Skill

## Instructions

Linux is a family of open-source Unix-like operating systems based on the Linux kernel. It is the most widely used operating system for servers, cloud infrastructure, and development environments. This skill covers essential Linux command-line operations, file system management, process control, user and permission management, and system administration tasks.

### Shell Basics

The shell is the command-line interface to the Linux operating system. The most common shell is Bash (Bourne Again SHell), but others include Zsh, Fish, and Sh.

```bash
# Check current shell
echo $SHELL

# Check shell version
bash --version

# View available shells
cat /etc/shells
```

### Command Structure

Linux commands follow the pattern: `command [options] [arguments]`

```bash
# Basic structure
ls -la /home/user

# Long options
ls --all --human-readable

# Combining short options
ps aux
```

### Getting Help

```bash
# Manual page
man ls

# Quick help
ls --help

# Whatis summary
whatis ls

# Info documentation
info ls
```

### File System Hierarchy

| Directory | Purpose |
|-----------|---------|
| `/` | Root directory (top of the file system) |
| `/bin/` | Essential user command binaries |
| `/sbin/` | System administration binaries |
| `/etc/` | System configuration files |
| `/var/` | Variable data (logs, databases, temp) |
| `/tmp/` | Temporary files (cleared on reboot) |
| `/home/` | User home directories |
| `/root/` | Root user's home directory |
| `/usr/` | User system resources (binaries, libraries, documentation) |
| `/opt/` | Optional third-party software |
| `/proc/` | Virtual file system for process and kernel information |
| `/dev/` | Device files |
| `/mnt/` | Temporary mount points |
| `/media/` | Removable media mount points |

### File Operations

```bash
# List files
ls -la                      # Long format, all files
ls -lh                      # Human-readable sizes
ls -lt                      # Sort by modification time
ls -lS                      # Sort by file size

# File operations
cp source destination       # Copy
mv source destination       # Move/rename
rm file                     # Remove file
rm -rf directory            # Remove directory recursively
mkdir -p path/to/dir        # Create directory (with parents)
touch file                  # Create empty file or update timestamp

# File viewing
cat file                    # Display file content
less file                   # View file with scrolling
head -n 20 file             # First 20 lines
tail -n 20 file             # Last 20 lines
tail -f file                # Follow file (realtime)
```

## Examples

### Example 1: File Permissions and Ownership

```bash
# View permissions
ls -la
# -rwxr-xr-- 1 user group 1024 Jan 15 10:30 script.sh
# ^^^^^^^^^   ^^^^ ^^^^^
# |   |       |    +----- Group owner
# |   |       +---------- File owner
# |   +------------------ Permissions (owner/group/others)

# Change permissions (symbolic)
chmod u+x script.sh         # Add execute for owner
chmod g-w script.sh         # Remove write for group
chmod o+r script.sh         # Add read for others
chmod a+x script.sh         # Add execute for everyone

# Change permissions (octal)
# r=4, w=2, x=1
chmod 755 script.sh         # rwxr-xr-x (owner=rwx, group=rx, others=rx)
chmod 644 file.txt          # rw-r--r--
chmod 600 private.key       # rw-------
chmod 700 private_dir       # rwx------
chmod 777 public.sh         # AVOID: full access for everyone

# Change ownership
chown user:group file       # Change owner and group
chown -R user:group dir     # Recursive change
chgrp group file            # Change group only

# Special permissions
chmod u+s script.sh         # SUID: run as file owner
chmod g+s directory         # SGID: new files inherit group
chmod +t /tmp               # Sticky bit: only owner can delete
```

### Example 2: Process Management

```bash
# View processes
ps aux                      # All processes (BSD format)
ps -ef                      # All processes (standard format)
ps aux --sort=-%mem         # Sort by memory usage
ps aux --sort=-%cpu         # Sort by CPU usage

# Process tree
pstree
pstree -p                   # With PIDs

# Top-like monitoring
top                         # Interactive process viewer
htop                        # Enhanced version (may need install)
vmstat 2                    # System statistics every 2 seconds
iostat                      # I/O statistics
free -h                     # Memory usage

# Process management
kill PID                    # Send SIGTERM (graceful termination)
kill -9 PID                 # Send SIGKILL (force kill)
kill -15 PID                # Send SIGTERM (polite termination)
killall process_name        # Kill all processes by name
pkill pattern               # Kill processes matching pattern

# Background and foreground
command &                   # Run in background
nohup command &             # Run immune to hangups
fg                          # Bring to foreground
bg                          # Send to background
jobs                        # List background jobs

# Process priority
nice -n 10 command          # Run with lower priority
renice -n 5 -p PID          # Change priority of running process
```

### Example 3: Disk and Storage Management

```bash
# Disk usage
df -h                       # File system disk space usage (human-readable)
df -hT                      # Include file system type
du -sh directory            # Total size of directory
du -h --max-depth=1         # Size of immediate subdirectories
du -ah | sort -rh | head    # Largest files recursively

# Mount management
mount                       # Show all mounted file systems
mount /dev/sda1 /mnt        # Mount device to directory
umount /mnt                 # Unmount
mount -o remount,ro /       # Remount as read-only

# Disk partitioning
lsblk                       # List block devices
fdisk -l                    # List partition tables
parted /dev/sda print       # Detailed partition info

# Create and manage file systems
mkfs.ext4 /dev/sda1         # Create ext4 file system
mkfs.xfs /dev/sda2          # Create XFS file system
tune2fs -l /dev/sda1        # View ext4 file system info

# LVM management
pvcreate /dev/sda1          # Create physical volume
vgcreate vg_data /dev/sda1  # Create volume group
lvcreate -L 100G -n lv_data vg_data  # Create logical volume
lvextend -L +50G /dev/vg_data/lv_data  # Extend logical volume
```

### Example 4: Network Configuration

```bash
# Interface information
ip addr                     # Show IP addresses (modern)
ifconfig                    # Show IP addresses (legacy)
ip link                     # Show link layer info
ip route                    # Show routing table
netstat -tulpn              # Listening ports
ss -tulpn                   # Socket statistics (modern netstat)

# DNS and connectivity
ping -c 4 example.com       # Test connectivity
dig example.com ANY         # DNS lookup
nslookup example.com         # DNS lookup (legacy)
host example.com            # DNS lookup (simplified)
traceroute example.com      # Route tracing
mtr example.com             # Combined ping/traceroute

# Network configuration files
cat /etc/hosts              # Local hostname resolution
cat /etc/resolv.conf        # DNS resolver configuration
cat /etc/network/interfaces # Network interface config (Debian)
cat /etc/sysconfig/network-scripts/ifcfg-eth0  # Network config (RHEL)

# Firewall (iptables/nftables)
iptables -L -n -v           # List iptables rules
ufw status verbose          # UFW firewall status
firewall-cmd --list-all     # Firewalld status (RHEL)

# Network services
netstat -tulpn | grep LISTEN  # Services listening on ports
lsof -i :80                # Process using port 80
systemctl status nginx     # Check service status
```

### Example 5: User and Group Management

```bash
# User management
useradd -m -s /bin/bash username   # Create user with home
usermod -aG sudo username          # Add user to group
passwd username                     # Change password
userdel -r username                 # Delete user and home
chage -l username                   # View password expiry info

# Group management
groupadd groupname                 # Create group
groupdel groupname                 # Delete group
groups username                    # Show user's groups
gpasswd -a username groupname      # Add user to group
gpasswd -d username groupname      # Remove user from group

# User information
who                                 # Who is logged in
w                                   # Detailed user info
last                                # Login history
id username                         # User UID/GID info
finger username                     # User information

# Sudo configuration
visudo                              # Edit sudoers file
# /etc/sudoers entries:
# username ALL=(ALL) ALL            # Full sudo access
# %groupname ALL=(ALL) ALL          # Group sudo access
# username ALL=(ALL) NOPASSWD: ALL  # Passwordless sudo
```

### Example 6: Package Management

```bash
# Debian/Ubuntu (APT)
apt update                    # Update package index
apt upgrade                   # Upgrade all packages
apt install package           # Install package
apt remove package            # Remove package
apt purge package             # Remove package and configs
apt autoremove                # Remove unused dependencies
dpkg -l                       # List installed packages
dpkg -i package.deb           # Install local .deb file

# RHEL/CentOS/Fedora (DNF/YUM)
dnf update                    # Update all packages
dnf install package           # Install package
dnf remove package            # Remove package
dnf groupinstall "Group Name" # Install package group
rpm -qa                       # List all installed RPMs
rpm -ivh package.rpm          # Install local RPM

# Arch Linux (Pacman)
pacman -Syu                   # Full system update
pacman -S package             # Install package
pacman -Rns package           # Remove package (with dependencies)

# Snap and Flatpak
snap install package          # Install snap package
flatpak install package       # Install flatpak package
```

### Example 7: System Monitoring and Logs

```bash
# System information
uname -a                    # Kernel version and system info
lsb_release -a              # Distribution release info
cat /etc/os-release         # OS identification
lscpu                       # CPU information
lsmem                       # Memory layout
lspci                       # PCI devices
lsusb                       # USB devices
dmesg | tail                # Kernel ring buffer (recent messages)

# System monitoring
uptime                      # System uptime and load average
top                         # Real-time process view
htop                        # Enhanced top (if installed)
nmon                        # Performance monitor
dstat                       # Versatile resource statistics
sar -u 2 5                  # CPU stats every 2s, 5 times
sar -r                      # Memory statistics

# Log management
journalctl                  # View systemd logs
journalctl -u service       # Logs for specific service
journalctl -f               # Follow logs (like tail -f)
journalctl --since "1 hour ago"  # Logs from last hour
cat /var/log/syslog         # System log (Debian)
cat /var/log/messages       # System log (RHEL)
cat /var/log/auth.log       # Authentication log
tail -f /var/log/nginx/access.log  # Follow web server log

# Disk I/O monitoring
iostat -x 2                 # Extended I/O stats every 2s
iotop                       # I/O usage by process
pidstat -d 2                # I/O stats by process

# Network monitoring
nethogs                     # Bandwidth per process
iftop                       # Bandwidth per connection
nload                       # Network traffic visualization
bmon                        # Bandwidth monitoring
```

## Best Practices

### System Administration

- Always use `sudo` for administrative tasks; avoid logging in as root
- Use a configuration management tool (Ansible, Puppet, Chef) for multi-server setups
- Keep the system updated with security patches
- Set up centralized logging (rsyslog, syslog-ng, or ELK stack)
- Use cron or systemd timers for scheduled tasks
- Monitor disk space and set up alerts for low space
- Use SSH key authentication instead of passwords
- Regularly review system logs for anomalies

### File System Practices

- Use LVM for flexible disk management
- Partition disks with separate `/var`, `/home`, and `/tmp` for security and isolation
- Set noexec on `/tmp` to prevent code execution
- Use quotas to limit user disk usage
- Regularly check file system integrity with `fsck`
- Use `chattr +i` to protect critical configuration files

### Security Practices

- Disable root SSH login (`PermitRootLogin no`)
- Use non-standard SSH port to reduce brute-force attacks
- Implement fail2ban for brute-force protection
- Enable and configure a firewall (ufw, firewalld, iptables)
- Use SELinux or AppArmor for mandatory access control
- Regularly audit user accounts and remove inactive ones
- Set umask to 027 or 077 for restrictive default permissions
- Encrypt sensitive data with LUKS or eCryptfs

## Common Mistakes

- **Running commands as root unnecessarily**: Use sudo for specific commands instead of logging in as root. Root can unintentionally damage the system.
- **Using `rm -rf` carelessly**: A single typo in `rm -rf` can destroy the entire system. Double-check paths, use `--preserve-root` flag.
- **Ignoring file permissions**: Setting 777 permissions on files is a security risk. Use the principle of least privilege.
- **Not using `sudo` with commands that need elevated privileges**: Commands like `kill`, `mount`, and `chmod` need root for certain operations.
- **Overlooking log files**: System logs contain crucial information about errors, security events, and performance issues.
- **Accidentally filling up disk**: Monitor disk space with `df -h` and set up alerts. Logs can quickly fill partitions.
- **Modifying configuration files without backups**: Always back up configuration files before editing. Use version control for critical configs.
- **Using deprecated commands**: Some commands (ifconfig, netstat, route) have been replaced by the `ip` suite. Learn modern alternatives.
- **Running untrusted scripts**: Always review shell scripts and commands before executing them with root privileges.
- **Not securing SSH**: Default SSH configuration is permissive. Disable root login, use key authentication, and change the default port.

## Libraries

### Essential Linux Commands

| Category | Commands |
|----------|----------|
| File Operations | ls, cp, mv, rm, mkdir, touch, find, locate |
| File Viewing | cat, less, more, head, tail, nl, od, hexdump |
| Text Processing | grep, sed, awk, cut, sort, uniq, tr, wc |
| Permissions | chmod, chown, chgrp, umask, lsattr, chattr |
| Process Management | ps, top, htop, kill, killall, nice, renice |
| Disk Management | df, du, fdisk, parted, mount, umount, lsblk |
| Network | ip, ss, ping, dig, curl, wget, netcat |
| Package Management | apt, dnf, pacman, dpkg, rpm |
| System Info | uname, lscpu, lsmem, lspci, dmidecode |
| Monitoring | sar, iostat, vmstat, dstat, journalctl |
| Compression | tar, gzip, bzip2, xz, zip, unzip |
| Archiving | tar, cpio, rsync |

### Development Tools

| Tool | Purpose |
|------|---------|
| gcc/clang | C/C++ compilers |
| make | Build automation |
| gdb | Debugger |
| strace | System call tracer |
| ltrace | Library call tracer |
| valgrind | Memory debugging |
| perf | Performance analysis |
| gprof | Profiling tool |
| objdump | Object file analysis |
| nm | Symbol listing |

## Design Principles

### Simplicity and Composability

Linux tools follow the Unix philosophy: do one thing well and work together through pipes and streams. Commands should be simple, focused, and composable. Prefer pipelines of simple commands over complex monolithic scripts.

### File System as Universal Interface

Everything in Linux is a file or can be treated as one. Processes, devices, sockets, and kernel parameters all have file system representations in `/proc`, `/sys`, and `/dev`. This provides a consistent interface for management and monitoring.

### Least Privilege

Users and processes should have only the permissions necessary to perform their tasks. Never run services as root. Use dedicated system users for services, and apply the principle of least privilege to file permissions, process capabilities, and network access.

### Automation and Idempotency

System administration tasks should be automated and idempotent (producing the same result regardless of how many times they run). Use scripts, configuration management tools, and infrastructure-as-code to ensure consistent, repeatable operations.

## Coding Standards

### Shell Script Style

```bash
#!/bin/bash
# Shebang at top
# -e: exit on error
# -u: treat unset variables as errors
# -o pipefail: pipeline fails if any command fails
set -euo pipefail

# Constants in uppercase
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="/var/log/myapp.log"

# Functions use snake_case
check_prerequisites() {
    local required_cmd="$1"
    if ! command -v "$required_cmd" &> /dev/null; then
        echo "Error: $required_cmd not found" >&2
        exit 1
    fi
}

main() {
    check_prerequisites "curl"
    # Main logic
}

main "$@"
```

### File Naming

- Configuration files: lowercase with `.conf` extension
- Scripts: lowercase with `.sh` extension for shell scripts
- Log files: lowercase with `.log` extension
- Directories: lowercase, descriptive names
- Use hyphens for word separation in file names
