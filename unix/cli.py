import os
import utime
import json
import network
import sys
import hashlib

def critical(func):
    def wrapper(*args, **kwags):
        try: return func(*args, **kwags)
        except  Exception as e:
            try: args[0].stderr(e)
            except Exception: print(f"error ({func.__name__}) {e}")
        return 1
    return wrapper

class shell:
    class environ:
        def __init__(self):
            self.HOME = None
            self.PWD = os.getcwd()
            self.ADMIN = "admin"
            self.USER = ""
            self.HOST = "Micro pico"
            self.SHADOW_FILE = "/passwd"
            self.SUCCESS = "success"
            self.LAST_ERROR = self.SUCCESS
            self.INTERFACE = network.WLAN(network.STA_IF)
            self.LOGGED_IN = False
            self.STATUS_SUCCESS = "\033[32;1m✔\033[0m"
            self.STATUS_ERROR = "\033[31;1m✘\033[0m"
            self.HOME_ICON = " "
            self.PROMPT = "\n╭─[{LAST_STATUS}] (\033[31;1m{USER}@{HOST}\033[0m) [\033[34;1m{PWD}\033[0m]\n╰─ $ "
            self.VARIABLES = {}
            self.reset()
    
        def reset(self):
            self.VARIABLES = {
                "HOME": self.HOME,
                "USER": self.USER,
                "HOST": self.HOST,
                "LAST_ERROR": self.LAST_ERROR,
                "PROMPT": self.PROMPT,
                "STATUS_SUCCESS": self.STATUS_SUCCESS,
                "STATUS_ERROR": self.STATUS_ERROR
            }

        def update_error(self, error: str):
            self.LAST_ERROR = error
            self.VARIABLES.update({"LAST_ERROR": error})

        def get_last_status(self):
            success = self.STATUS_SUCCESS if "STATUS_SUCCESS" not in self.VARIABLES \
                      else self.VARIABLES["STATUS_SUCCESS"]
            error = self.STATUS_ERROR if "STATUS_ERROR" not in self.VARIABLES \
                      else self.VARIABLES["STATUS_ERROR"]
            if self.LAST_ERROR == self.SUCCESS: last_status = success
            else: last_status = error
            return last_status

        def __str__(self):
            string = ""
            for key, value in self.VARIABLES.items():
                if key == "PROMPT": value = str(value.encode())[2:-1]
                string += f"{key}={value}\n"
            return string

    def __init__(self):
        with open("/lib/unix/commands.json", "r") as f: self.commands = json.loads(f.read())
        self.env = self.environ()
        self.USER_CONFIGS = "/shell-config.json"
        self.USERS = list(self.get_users_config().keys())
        
    def get_users_config(self):
        if not self.isfile(self.USER_CONFIGS):
            config = {self.env.ADMIN: "/"}
            with open(self.USER_CONFIGS, 'w') as f:
                f.write(json.dumps(config))
        else:
            with open(self.USER_CONFIGS, 'r') as f:
                config = json.loads(f.read())
            if len(list(config.keys())) == 0:
                self.remove(self.USER_CONFIGS)
                config = self.get_users_config()
        return config
        
    def set_user_config(self, username: str, home: str):
        config = self.get_users_config()
        assert len(home) != 0 or self.isdir(home), "Home folder not found"
        if len(home) == 0:
            assert username in list(config.keys()), "user account not found"
            config.pop(username)
        else: config.update({username: home})
        with open(self.USER_CONFIGS, 'w') as f:
            f.write(json.dumps(config))
    
    @critical
    def run(self, user: str):
        self.login(user)
        while self.env.LOGGED_IN:
            try:
                cmd = self.stdin(self.get_prompt())
                # shell built in
                if len(cmd) == 0: pass
                elif cmd == "exit": break 
                elif cmd == "clear": self.stdout("\033[2J\033[H")
                elif cmd == "env": self.stdout(str(self.env))
                else: self.parser(cmd); continue
                self.env.update_error(self.env.SUCCESS)
            except KeyboardInterrupt: self.stderr("SIGINT")
        self.logout()

    def get_prompt(self):
        home_icon, home, pwd = self.env.HOME_ICON, self.env.HOME, self.env.PWD
        if pwd[:min([len(pwd), len(home)])] == home and home != "/": pwd = pwd.replace(home, home_icon)
        prompt = "$ "
        try:
            if "PROMPT" in self.env.VARIABLES:
                prompt = self.env.VARIABLES["PROMPT"].format(
                    USER=self.env.USER, PWD=pwd,
                    HOST=self.env.HOST, TIME=self.date(1),
                    DATE=self.date(2), LAST_STATUS=self.env.get_last_status())
        except Exception as e:
            self.stdout(f"\033[33;1m[Warning]: unset variable '{e}' in prompt\033[0m")
            self.env.VARIABLES.update({"PROMPT": prompt})
        return prompt

    def date(self, mode: int=0):
        tym = utime.localtime(utime.time())
        tm = f"{tym[3]}:{tym[4]}:{tym[5]}"
        if mode == 1: return tm
        dt = f"{tym[0]}-{tym[1]}-{tym[2]}"
        if mode == 2: return dt
        return f"{dt} {tm}"

    def get_passwd(self, user: str):
        assert user in self.USERS, "invalid user account"
        passwd_file = f"{self.env.SHADOW_FILE}.{user}.bin"
        if (self.env.USER == self.env.ADMIN and self.env.LOGGED_IN) or \
           (not self.isfile(passwd_file) and self.env.USER == user): return b""
        with open(passwd_file, "rb") as f: passwd_hash = f.read()
        assert hashlib.sha256(self.stdin(f"[{user}] passwd: ")).digest() == passwd_hash, \
        "Wrong password"
        return passwd_hash

    def set_passwd(self, user: str):
        old_passwd_hash = self.get_passwd(user)
        passwd = self.stdin(f"newpasswd> ")
        assert passwd == self.stdin(f"confirm> "), "password do not match"
        passwd_hash = hashlib.sha256(passwd).digest()
        passwd_file = f"{self.env.SHADOW_FILE}.{user}.bin"
        if len(old_passwd_hash) != 0 and passwd_hash == old_passwd_hash:
            self.stdout("password unchanged")
        else:
            with open(passwd_file, "wb") as f: f.write(passwd_hash)
            self.stdout("password updated")

    def tokenize(self, command: str):
        try: command = command.format(**self.env.VARIABLES)
        except Exception as e: assert False, f"variable '{e}' not set"
        if "'" not in command and "\"" not in command: return command.split()
        else:
            sub_commands = []
            sub_command = ""
            openned = ""
            for ch in command:
                if ch in ["\"", "'"]:
                    if not openned:
                        openned = ch
                        if len(sub_command) != 0:
                            sub_commands.append(sub_command.strip(" "))
                            sub_command = ""
                        continue 
                    else:
                        if openned == ch:
                            sub_commands.append(sub_command)
                            sub_command = ""
                            openned = ""
                            continue 
                elif ch == " " and not openned:
                    sub_commands.append(sub_command)
                    sub_command = ""
                    continue
                sub_command += ch
            assert not openned, f"quote> {openned} was never closed"
            if len(sub_command) != 0: sub_commands.append(sub_command)
            return  sub_commands

    @critical
    def parser(self, command: str):
        commands = self.commands
        sub_commands = self.tokenize(command)
        if sub_commands[0] == commands["pwd"][0]: self.stdout(self.env.PWD)
        elif sub_commands[0] == commands["uname"][0]: self.stdout(sys.version)
        elif sub_commands[0] == commands["date"][0]: self.stdout(self.date())
        elif sub_commands[0] == commands["cd"][0]:
            if len(sub_commands) != 2:
                assert len(sub_commands) == 1, "wrong usage"
                path = self.env.HOME
            else: path = self.get_path(sub_commands[1])
            assert not self.isfile(path), f"{path} is a file"
            assert self.isdir(path), "path does not exist"
            os.chdir(path)
            self.env.PWD = os.getcwd()
        elif sub_commands[0] == commands["ls"][0]:
            assert len(sub_commands) <= 2, "wrong usage"
            path = self.get_path(sub_commands[1] if len(sub_commands) > 1 else ".")
            assert not self.isfile(path), f"{path} is a file"
            assert self.isdir(path), "path does not exist"
            flist = os.listdir(path)
            folders = []
            files = []
            for p in flist:
                full_path = f"{path}/{p}"
                if not self.isfile(full_path):
                    p += "/"
                    folders.append(f"\033[34;1m {p:<30} 1.00  KB\033[0m")
                else:
                    size = round(self.disk_used(full_path) / 1000, 2)
                    files.append(f"\033[1m {p:<30} {size:<5} KB\033[0m")
            folders.extend(files)
            self.stdout("\n".join(folders))
        elif sub_commands[0] == commands["mkdir"][0]:
            assert len(sub_commands) >= 2, "No path specified"
            for path in [self.get_path(p) for p in sub_commands[1:]]:
                assert not self.isdir(path), "path exists"
                assert not self.isfile(path), f"{path} is a file"
                os.mkdir(path)
        elif sub_commands[0] == commands["mv"][0]:
            assert len(sub_commands) >= 3, f"Usage: {sub_commands[0]} <src1> <src1> ... <dest>"
            dest = self.get_path(sub_commands[-1])
            if len(sub_commands) == 3: self.move(self.get_path(sub_commands[1]), dest)
            else:
                for src in [self.get_path(p) for p in sub_commands[1:-1]]:
                    p = src.split("/")[-1] if "/" in src else src
                    self.move(src, f"{dest}/{p}")
        elif sub_commands[0] == commands["cp"][0]:
            assert len(sub_commands) >= 3, f"Usage: {sub_commands[0]} <src1> <src1> ... <dest>"
            dest = self.get_path(sub_commands[-1])
            if len(sub_commands) == 3: self.copy(self.get_path(sub_commands[1]), dest)
            else:
                for src in [self.get_path(p) for p in sub_commands[1:-1]]:
                    if src == self.get_path(sub_commands[1]): self.copy(src, dest)
                    else: self.copy(src, dest, "ab")
        elif sub_commands[0] == commands["rm"][0]:
            assert len(sub_commands) >= 2, "No path specified"
            for path in [self.get_path(p) for p in sub_commands[1:]]: self.remove(path)
        elif sub_commands[0] == commands["touch"][0]:
            assert len(sub_commands) >= 2, "No path specified"
            for path in [self.get_path(p) for p in sub_commands[1:]]:
                assert not self.isfile(path), f"{path} exists"
                with open(path, "w") as f: pass
        elif sub_commands[0] == commands["cat"][0]:
            assert len(sub_commands) >= 2, f"usage: {sub_commands[0]} <file1> <file2> ..."
            for path in [self.get_path(p) for p in sub_commands[1:]]:
                assert not self.isdir(path), f"{path} is a directory"
                assert self.isfile(path), f"{path} does not exist"
                self.stdout(f"\033[32;1mfile: {path}\033[0m")
                with open(path, 'r') as f:
                    while True:
                        text = f.read(3072)
                        if not text: break
                        self.stdout(text, end="")
        elif sub_commands[0] == commands["echo"][0]:
            assert len(sub_commands) >= 2, f"usage: {sub_commands[0]} <text>"
            text = " ".join(sub_commands[1:])
            if '>' in sub_commands or ">>" in sub_commands:
                target = ">>" if ">>" in sub_commands else ">"
                mode = "a" if target == ">>" else "w"
                assert target != sub_commands[-1], "no output file"
                string = " ".join(sub_commands[1:sub_commands.index(target)]) + "\n"
                path = self.get_path(sub_commands[sub_commands.index(target)+1])
                with open(path, mode) as f: f.write(string)
            else: self.stdout(text)
        elif sub_commands[0] == commands['man'][0]:
            assert len(sub_commands) <= 2, f"usage: {sub_commands[0]} [ |<command>]"
            out_format = "({command}) DESCRIPTION: {page}"
            if len(sub_commands) == 1:
                for command, page in [(val[0], val[1]) for key, val in commands.items()]:
                    self.stdout(out_format.format(command=command, page=page))
            else:
                man_pages = [(key, value[0]) for key, value in commands.items()]
                assert sub_commands[1] in [value for _, value in man_pages], "Command not found"
                key = [k for k, v in man_pages if v == sub_commands[1]][0]
                page = commands[key][1]
                self.stdout(out_format.format(command=sub_commands[1], page=page))
        elif sub_commands[0] == commands['ifconfig'][0]:
            assert len(sub_commands) <= 2, f"usage {sub_commands[0]} [ |up|down|close|scan|connect]"
            self.iface(*sub_commands)
        elif sub_commands[0] == commands['du'][0]:
            assert len(sub_commands) <= 3, f"usage {sub_commands[0]} [ |-v] <path>"
            if len(sub_commands) == 2:
                path = sub_commands[1]
                verbose = False
            else:
                assert sub_commands[1] == "-v", f"unknown flag '{sub_commands[1]}'"
                path = sub_commands[2]
                verbose = True
            path = self.get_path(path)
            assert self.isdir(path) or self.isfile(path), f"{path} does not exist"
            size = self.disk_used(path, verbose)
            self.stdout(f"{path} size: {round(size / 1024, 3)} KB ({size} bytes)")
        elif sub_commands[0] == commands['set'][0]:
            assert len(sub_commands) == 3, f"usage {sub_commands[0]} <name> <value>"
            self.env.VARIABLES.update({sub_commands[1]: sub_commands[2]})
        elif sub_commands[0] == commands['unset'][0]:
            assert len(sub_commands) >= 2, f"usage {sub_commands[0]} <name1> <name2> ..."
            for variable in sub_commands[1:]:
                assert variable in self.env.VARIABLES, f"variable '{variable}' not set"
                self.env.VARIABLES.pop(variable)
        elif sub_commands[0] == commands['reset'][0]: self.env.reset()
        elif sub_commands[0] == commands['passwd'][0]:
            assert len(sub_commands) <= 2, f"usage: {sub_commands[0]} <user account>"
            if len(sub_commands) == 1: self.set_passwd(self.env.USER)
            else: self.set_passwd(sub_commands[1])
        elif sub_commands[0] == commands['su'][0]:
            assert len(sub_commands) <= 2, f"usage {sub_commands[0]} <user account>"
            user = self.env.ADMIN if len(sub_commands) == 1 else sub_commands[1]
            sh = subshell(self.stdin, self.stdout, self.stderr)
            sh.run(user)
        elif sub_commands[0] == commands['useradd'][0]:
            self.useradd(sub_commands)
        elif sub_commands[0] == commands['userdel'][0]:
            self.userdel(sub_commands)
        elif sub_commands[0] == commands['users'][0]:
            assert len(sub_commands) == 1, f"{sub_commands[0]} takes no argument"
            self.stdout("\n".join(self.USERS))
        else: assert False, f"command '{sub_commands[0]}' not found"
        self.env.update_error(self.env.SUCCESS)
        return 0

    def iface(self, *sub_commands):
        if len(sub_commands) == 1:
            state = "\033[32;1mconnected\033[0m" if self.env.INTERFACE.isconnected() else "\033[31;1mnot connected\033[0m"
            self.stdout("\033[1m")
            for name, config in zip(["inet", "subnet", "gateway", "broadcast"], self.env.INTERFACE.ifconfig()):
                self.stdout(f"{name:<15}: {config}")
            self.stdout(f"\033[1mstate: {state}")
        elif len(sub_commands) == 2:
            self.get_passwd(self.env.USER)
            if sub_commands[1] == "scan":
                for index, netwk in enumerate(self.env.INTERFACE.scan()): self.stdout(f"{index+1}. {netwk[0].decode()}")
            elif sub_commands[1] == "close": self.env.INTERFACE.disconnect()
            elif sub_commands[1] in ["up", "down"]: self.env.INTERFACE.active(sub_commands[1])
            elif sub_commands[1] == "connect":
                nets = self.env.INTERFACE.scan()
                assert len(nets) != 0, "No Wifi intefaces in range"
                self.stdout(f"{'-'*10} available networks {'-'*10}")
                for index, netwk in enumerate(nets): self.stdout(f"{index+1}. {netwk[0].decode()}")
                ssid = ""
                self.stdout("Enter network index or [C]ancel")
                while len(ssid) == 0:
                    try:
                        i = self.stdin("\033[1mnetwork index> \033[0m")
                        if i.lower() == "c": return 
                        ssid = nets[int(i)-1][0].decode()
                    except Exception as e: pass
                passwd = self.stdin(f"\033[33;1m({ssid})\033[0m passwd> ")
                self.env.INTERFACE.connect(ssid, passwd)
                self.stdout("Wait for at most 15 seconds")
                i = 1
                while not self.env.INTERFACE.isconnected() and i < 15:
                    self.stdout(f"\rConnecting [{i}]", end="  ")
                    utime.sleep(1)
                    i += 1
                self.stdout("\n")
                assert self.env.INTERFACE.isconnected(), f"({ssid}) not connected"
                ip = self.env.INTERFACE.ifconfig()[0]
                self.stdout(f"({ssid}) ip: {ip}")
            else: assert False, "unknown subcommand"

    def move(self, src: str, dest: str):
        assert self.isdir(src) or self.isfile(src), "src path does not exist"
        if self.isdir(src):
            assert not self.isfile(dest), "cannot move <dir> to <file>"
            os.rename(src, dest)
        else:
            if self.isdir(dest):
                filename = src if "/" not in src else src.split("/")[-1]
                dest += f"/{filename}"
            os.rename(src, dest)
        self.stdout(f"moved {src} to {dest}")

    def copy(self, src: str, dest: str, mode: str="wb"):
        assert self.isdir(src) or self.isfile(src), "src path does not exist"
        if self.isdir(src):
            assert not self.isfile(dest), "cannot copy <dir> to <file>"
            if self.isdir(dest):
                dirname = src if "/" not in src else src.split("/")[-1]
                dest2 = f"{dest}/{dirname}"
                os.mkdir(dest2)
            else:
                os.mkdir(dest)
                dest2 = dest
            for file in os.listdir(src):
                self.copy(f"{src}/{file}", dest2)
            self.stdout(f"copied {src} -> {dest2}")
            return
        if self.isdir(dest):
            filename = src if "/" not in src else src.split("/")[-1]
            dest = f"{dest}/{filename}"
        
        if self.isfile(dest) and mode != "ab":
            cmd = self.stdin(f"\033[33;1mfile {dest} exists\033[0m [O]verrite, [A]ppend, [C]ancel >")
            if cmd.lower() == "o": mode = "wb"
            elif cmd.lower() == "a": mode = "ab"
            else:
                self.stdout("copy canceled")
                return
        copied_bytes = 0
        with open(src, "rb") as f:
            with open(dest, mode) as f2:
                while True:
                    chunk = f.read(4096)
                    if not chunk: break
                    f2.write(chunk)
                    copied_bytes += len(chunk)
        self.stdout(f"copied {src} -> {dest} {copied_bytes} bytes")
    
    def remove(self, path: str, recussive: bool=False):
        assert self.isdir(path) or self.isfile(path), "path does not exist"
        if self.isfile(path) or len(os.listdir(path)) == 0:
            os.remove(path)
        else:
            if not recussive:
                inp = self.stdin(f"\033[33;1m{path} is not empty, Continue?\033[0m [Y/n]")
                if inp.lower() == "n": return
            for file in os.listdir(path):
                self.remove(f"{path}/{file}", True)
            os.remove(path)
        self.stdout(f"deleted {path}")

    def disk_used(self, path: str, verbose: bool=False):
        if self.isfile(path):
            with open(path, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
        else:
            size = 1
            for file in os.listdir(path):
                p = f"{path}{file}" if path[-1] == "/" else f"{path}/{file}"
                size += self.disk_used(p, verbose)
        icon = " " if self.isfile(path) else " "
        if verbose: self.stdout(f"{icon}{path} \033[33;1m{round(size / 1024, 3)} KB\033[0m")
        return size

    def get_path(self, path: str):
        assert len(path.strip()) != 0, "No path specified"
        if path[0] != "/": path = f"{self.env.PWD}/{path}"
        while "//" in path: path = path.replace("//", "/", path.count("//"))
        if path[-1] == "/" and path != "/": path = path[:-1]
        directory = path if self.isdir(path) else path[:path.rfind("/")]
        filename = "" if directory == path else path[path.rfind("/")+1:]
        if "." in directory:
            assert self.isdir(directory), "path does not exist"
            os.chdir(directory)
            directory = os.getcwd()
            os.chdir(self.env.PWD)
        path = f"{directory}/{filename}" if len(filename) != 0 else directory
        assert path[:len(self.env.HOME)] == self.env.HOME or \
               self.env.USER == self.env.ADMIN, "access denied"
        return path
    
    def useradd(self, args: list):
        assert self.env.USER == self.env.ADMIN, "permission denied"
        assert len(args) == 3, f"usage {args[0]} <user account> <home folder>"
        user = args[1]
        home = args[2]
        assert user not in self.USERS, "user account exists"
        assert not self.isfile(home), "home cannot be a file"
        if not self.isdir(home): os.mkdir(home)
        self.set_user_config(user, home)
        self.USERS = list(self.get_users_config().keys())
    
    def userdel(self, args: list):
        assert self.env.USER == self.env.ADMIN, "permission denied"
        assert len(args) == 2, f"usage {args[0]} <user account>"
        user = args[1]
        assert user == self.env.ADMIN, "permission denied"
        assert user in self.USERS, "user account not found"
        config = self.get_users_config()
        home = config[user]
        if self.isdir(home):
            confirm = self.stdin(f"remove {user}'s home '{home}' [Y/n] ")
            if confirm.upper() == 'Y': self.remove(home)
        self.set_user_config(user, "")
        passwd_file = f"{self.env.SHADOW_FILE}.{user}.bin"
        if self.isfile(passwd_file): self.remove(passwd_file)
        self.USERS = list(self.get_users_config().keys())        

    def login(self, user: str):
        assert user in self.USERS, "user account not found"
        self.env.USER = user
        self.get_passwd(user)
        home = self.get_users_config()[user]
        assert not self.isfile(home), "confliction, home cannot be a file"
        if not self.isdir(home): os.mkdir(home)
        os.chdir(home)
        self.env.HOME = home
        self.env.PWD = os.getcwd()
        self.env.LOGGED_IN = True
        self.env.reset()

    def logout(self):
        self.stdout("exit")
        self.env.LOGGED_IN = False
        
    def stdin(self, *args, **kwargs):
        return input(*args, **kwargs)
    
    def stdout(self, *args, **kwargs):
        print(*args, **kwargs)
        
    def isfile(self, path: str):
        try:
            with open(path, "rb") as f: f.read(1)
            return True
        except Exception:
            return False
    
    def isdir(self, path: str):
        try:
            os.listdir(path)
            return True
        except Exception:
            return False

    def stderr(self, error: str):
        print(f"\033[31;1m[Error]: \033[0m{error}")
        self.env.update_error(error)


class subshell(shell):
    def __init__(self, stdin: shell.stdin, stdout: shell.stdout, stderr: shell.stderr):
        super().__init__()
        self.stdin = stdin
        self.stdout = stdout
        self._stderr = stderr

    def stderr(self, error: str):
        self.env.update_error(error)
        self._stderr(error)

    def logout(self):
        self.stdout("logout")
        self.env.LOGGED_IN = False

if __name__ == "__main__":
    shell().run("admin")
