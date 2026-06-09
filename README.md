# MicroPython Unix Shell

A lightweight Unix-like shell implementation for MicroPython systems (e.g., Raspberry Pi Pico). This shell provides essential command-line tools for file management, user administration, environment configuration, and network control on embedded systems.

## Features

- **File System Operations**: Navigate, create, copy, move, and delete files and directories
- **User Management**: Create, delete, and switch between user accounts with password authentication
- **Environment Variables**: Set and manage shell environment variables
- **Network Interface Control**: Configure WiFi connectivity and network settings
- **System Information**: View system time, date, and version information
- **File Content Display**: Read and examine file contents
- **Disk Usage Monitoring**: Track storage usage across files and directories

## Installation

Place the shell module in your MicroPython project and import the shell class:

```python
from unix.cli import shell

# Create a shell instance
sh = shell()

# Run shell for a user
sh.run("admin")
```

## Documentation

- 📖 **[Interactive HTML Documentation](docs/index.html)** - Browse commands in a bash-like interface
- 📋 **[Manual Pages](micropython_unix_shell.man)** - Detailed manpage documentation

## Quick Start

The shell supports standard Unix commands. After logging in with a valid user account:

```
╭─[✔] (admin@Micro pico) [/]
╰─ $ pwd
/
╭─[✔] (admin@Micro pico) [/]
╰─ $ cd /home
╭─[✔] (admin@Micro pico) [/home]
╰─ $ ls
```

## Command Reference

### Navigation & File Listing

#### **pwd** - Print Working Directory
Returns the current working directory path.

```
$ pwd
/home/user
```

#### **cd** [path] - Change Directory
Navigate to a specified directory. If no path is provided, changes to the user's home directory.

```
$ cd /home
$ cd ..
$ cd ~
```

#### **ls** [path] - List Directory Contents
List files and directories in the specified path or current directory. Shows file size in KB.

```
$ ls
$ ls /home/user
```

### File Operations

#### **touch** file1 [file2 ...] - Create Files
Create one or more empty files.

```
$ touch myfile.txt
$ touch file1.txt file2.txt file3.txt
```

#### **type** file1 [file2 ...] - Display File Contents
Print the contents of one or more files to the console.

```
$ type myfile.txt
$ type file1.txt file2.txt
```

#### **mkdir** directory1 [directory2 ...] - Create Directories
Create one or more directories.

```
$ mkdir newdir
$ mkdir dir1 dir2 dir3
```

#### **cp** src1 [src2 ...] dest - Copy Files/Directories
Copy files or directories to a destination. Interactive prompts if destination exists.

```
$ cp file.txt /backup/
$ cp dir1 dir2 /backup/
```

#### **mv** src1 [src2 ...] dest - Move/Rename Files
Move or rename files and directories. Supports multiple sources.

```
$ mv oldname.txt newname.txt
$ mv file1.txt file2.txt /archive/
```

#### **rm** path1 [path2 ...] - Remove Files/Directories
Delete files or directories. Prompts before removing non-empty directories.

```
$ rm myfile.txt
$ rm directory/
```

#### **echo** [text] - Display Text
Print text to the console or redirect to a file.

```
$ echo "Hello, MicroPython!"
$ echo "Log entry" > /tmp/log.txt
$ echo "Append" >> /tmp/log.txt
```

### Disk & Storage

#### **du** [-v] path - Disk Usage
Calculate total disk space used by a file or directory. Use `-v` flag for verbose output.

```
$ du /home/user
/home/user size: 2.342 KB (2342 bytes)

$ du -v /home/user
  file1.txt 1.230 KB
  file2.txt 1.112 KB
/home/user size: 2.342 KB (2342 bytes)
```

### User Management

#### **useradd** username homedir - Add User
Create a new user account with a home directory. Requires admin privileges.

```
$ useradd john /home/john
```

#### **userdel** username - Delete User
Remove a user account and optionally delete their home directory. Requires admin privileges.

```
$ userdel john
```

#### **passwd** [username] - Set Password
Change password for the current user or specified user. Requires admin privileges for other users.

```
$ passwd
newpasswd> ****
confirm> ****
password updated

$ passwd john
[john] passwd: ****
```

#### **users** - List Users
Display all user accounts on the system.

```
$ users
admin
john
guest
```

#### **su** [username] - Switch User
Switch to another user account or admin if no user specified.

```
$ su
$ su john
```

### Environment Variables

#### **set** name value - Set Variable
Create or modify an environment variable.

```
$ set MYVAR "hello world"
$ set PROMPT "[{USER}]> "
```

#### **unset** name1 [name2 ...] - Remove Variables
Remove one or more environment variables.

```
$ unset MYVAR
$ unset VAR1 VAR2 VAR3
```

#### **env** - Display Environment
Show all current environment variables and their values. Built-in command.

```
$ env
```

#### **reset** - Reset Environment
Restore all environment variables to their default values.

```
$ reset
```

### Network Interface

#### **net** [action] - Network Configuration
Control WiFi interface. Actions: `up`, `down`, `scan`, `connect`, `close`

**View current network config:**
```
$ net
inet      : 192.168.1.100
subnet    : 255.255.255.0
gateway   : 192.168.1.1
broadcast : 192.168.1.255
state: connected
```

**Enable/Disable interface:**
```
$ net up
$ net down
```

**Scan for networks:**
```
$ net scan
1. HomeNetwork
2. GuestWiFi
3. OpenNetwork
```

**Connect to network:**
```
$ net connect
---------- available networks ----------
1. HomeNetwork
2. GuestWiFi
3. OpenNetwork
Enter network index or [C]ancel
network index> 1
(HomeNetwork) passwd> ****
Wait for at most 15 seconds
Connecting [1]
(HomeNetwork) ip: 192.168.1.100
```

**Disconnect:**
```
$ net close
```

### System Information

#### **date** - Display Date/Time
Show current system date and time.

```
$ date
2026-06-09 14:30:45
```

#### **uname** - System Information
Display MicroPython version and system information.

```
$ uname
MicroPython x.x.x on platform
```

### Help & Documentation

#### **man** [command] - Manual Pages
Display help for a specific command or all commands.

```
$ man
(pwd) DESCRIPTION: return present working directory
(echo) DESCRIPTION: echos the specified text
...

$ man ls
(ls) DESCRIPTION: lists the directories and files in pwd
```

### Shell Built-in Commands

#### **clear** - Clear Screen
Clear the terminal display.

```
$ clear
```

#### **exit** - Exit Shell
Logout and terminate the shell session.

```
$ exit
```

## Environment Variables

### Default Variables

- `HOME` - User's home directory
- `USER` - Current logged-in user
- `HOST` - System hostname (default: "Micro pico")
- `PWD` - Current working directory
- `LAST_ERROR` - Last command error message
- `PROMPT` - Custom prompt format

### Custom Prompt Format

Customize the shell prompt using format variables:

```
$ set PROMPT "[{USER}@{HOST}] {PWD}> "
$ set PROMPT "{DATE} [{USER}]> "
```

Available placeholders: `{USER}`, `{HOST}`, `{PWD}`, `{DATE}`, `{TIME}`, `{LAST_STATUS}`

## File Structure

```
unix/
├── __init__.py          # Package initialization
├── cli.py               # Main shell implementation
└── commands.json        # Command definitions
```

## Configuration Files

- `/shell-config.json` - User account configuration
- `/passwd.{username}.bin` - Hashed password files (SHA256)

## User Permissions

- **Admin user** (`admin`): Full system access, can manage users, modify all files
- **Regular users**: Limited to their home directory and shared system directories

## Error Handling

The shell implements robust error handling with status indicators:

- ✔ (Green) - Last command succeeded
- ✘ (Red) - Last command failed

Errors are caught and displayed without terminating the shell session.

## MicroPython Platform

This shell is optimized for MicroPython systems including:
- Raspberry Pi Pico
- ESP32
- Other compatible MicroPython boards

## Keyboard Shortcuts

- `Ctrl+C` - Send interrupt signal (SIGINT)

## Examples

### Create a project directory structure:
```
$ mkdir /projects
$ cd /projects
$ mkdir python node javascript
$ ls
```

### Backup files:
```
$ mkdir /backup
$ cp /important/file.txt /backup/
$ cp /important/data/ /backup/
```

### Create a simple log file:
```
$ echo "System started" > /var/log.txt
$ echo "User logged in" >> /var/log.txt
$ cat /var/log.txt
```

### Set up a new user:
```
$ useradd alice /home/alice
$ passwd alice
[alice] passwd: ****
$ su alice
```

## Limitations

- No pipe operations (`|`)
- No command chaining with `;` (except shell built-ins)
- Password stored as SHA256 binary hash
- Relative path support limited to simple cases

## License

See LICENSE file in the repository.
