import os, platform, socket, json


class ServerAnswer:
    def __init__(self):
        self.data = None
        self.timeout: bool = True

    def set(self, data):
        self.data = data

    def get(self):
        return self.data

    def set_timeout(self, value: bool):
        self.timeout = value

    def get_timeout(self) -> bool:
        return self.timeout


class Server:
    def __init__(self, dirname: str, connection_passwords: list, port: int):
        self.port: int = port
        self.dirname: str = dirname
        self.connection_passwords: str = connection_passwords
        self.create()

    def write_log(self, message):
        print("[Server] " + str(message))

    def read_message(self, cl):
        bytes_limit = 4096
        chunk_size = 1024
        data = b""
        while 1:
            rec = cl.recv(chunk_size)
            data += rec
            if len(rec) < chunk_size:
                try:
                    message = json.loads(data.decode())
                except:
                    self.write_log("disconnected. Cause: smaller than chunk size, but no json!")
                    cl.close()
                    return False
                else:
                    break
            if len(data) > bytes_limit:
                try:
                    message = json.loads(data.decode())
                except:
                    self.write_log("disconnected. Cause: bytes limit!")
                    cl.close()
                    return False
                else:
                    break
            try:
                message = json.loads(data.decode())
            except:
                continue
            else:
                break
        if type(message) != list:
            self.write_log("disconnected. Cause: no list!")
            cl.close()
            return False
        return message

    def create(self):
        soc: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.bind(("0.0.0.0", self.port))
        soc.listen(1)
        self.write_log(f"Server started on port {self.port}")
        while 1:
            try:
                states = {}
                cl, addr = soc.accept()
                cl.settimeout(5)
                self.write_log("connected!")
                while 1:
                    message = self.read_message(cl)
                    if not message:
                        break
                    answ = ServerAnswer()
                    disconnect = self.message(message, answ, states)
                    answer = answ.get()
                    if answ.get_timeout():
                        cl.settimeout(5)
                    else:
                        cl.settimeout(None)
                    if answer != None:
                        if type(answer) == bytes:
                            cl.send(answer)
                        else:
                            cl.send(json.dumps(answer).encode())
                    if disconnect:
                        cl.close()
                        self.write_log("disconnected!")
            except Exception as ex:
                print(ex)
                cl.close()
                self.write_log("disconnected!")

    def message(self, msg: list, answer: ServerAnswer, states: dict) -> bool:
        if "verified" not in states.keys() or not states["verified"]:
            answer.set_timeout(False)
            states["verified"] = False
            if msg[0] == "connect":
                if len(self.connection_passwords) > 0:
                    answer.set(["enter_password", len(self.connection_passwords)])
                    return False
                else:
                    states["verified"] = True
                    answer.set(["success"])
                    return False
            elif msg[0] == "password":
                if len(self.connection_passwords) > 0:
                    if len(msg[1:]) != len(self.connection_passwords):
                        answer.set(["fail", "invalid password"])
                    for u in zip(msg[1:], self.connection_passwords):
                        if u[0] != u[1]:
                            answer.set(["fail", "invalid password"])
                            break
                    else:
                        states["verified"] = True
                        answer.set(["success"])
                    return False
                else:
                    states["verified"] = True
                    answer.set(["success"])
                    return False
            else:
                answer.set(["fail", "unknown command"])
                return True
        else:
            answer.set_timeout(False)
            if msg[0] == "folder":
                if msg[1] != ".":
                    try:
                        path = msg[1].replace("\\", "/").split("/")
                        if not os.path.exists(self.dirname):
                            answer.set(["fail", "not exists"])
                            return False
                        pl = self.dirname.replace("\\", "/") + ""
                        if pl.endswith("/"):
                            pl = pl[:-1]
                        for u in path:
                            if u not in os.listdir(pl) or not os.path.isdir(os.path.join(pl, u)):
                                answer.set(["fail", "not exists"])
                                return False
                            pl += "/" + u
                        folders = [u for u in os.listdir(pl) if os.path.isdir(os.path.join(pl, u))]
                        files = [u for u in os.listdir(pl) if os.path.isfile(os.path.join(pl, u))]
                        answer.set(["success", folders, files])
                    except Exception as ex:
                        answer.set(["fail", str(ex)])
                else:
                    try:
                        folders = [u for u in os.listdir(self.dirname) if os.path.isdir(os.path.join(self.dirname, u))]
                        files = [u for u in os.listdir(self.dirname) if os.path.isfile(os.path.join(self.dirname, u))]
                        answer.set(["success", folders, files])
                    except Exception as ex:
                        answer.set(["fail", str(ex)])
                return False
            elif msg[0] == "file":
                try:
                    path = msg[1].replace("\\", "/").split("/")
                    if not os.path.exists(self.dirname):
                        answer.set(["fail", "not exists"])
                        return False
                    pl = self.dirname.replace("\\", "/") + ""
                    if pl.endswith("/"):
                        pl = pl[:-1]
                    for u in path[:-1]:
                        if u not in os.listdir(pl) or not os.path.isdir(os.path.join(pl, u)):
                            answer.set(["fail", "not exists"])
                            return False
                        pl += "/" + u
                    if path[-1] not in os.listdir(pl) or not os.path.isfile(os.path.join(pl, path[-1])):
                        answer.set(["fail", "not exists"])
                        return False
                    with open(os.path.join(pl, path[-1]), "rb") as r:
                        answer.set(["success", str(r.read())])
                except Exception as ex:
                    answer.set(["fail", str(ex)])
                return False
            else:
                answer.set(["fail", "unknown command"])
                return True


def clear():
    sys: str = str(platform.system())
    if sys == "Windows":
        os.system("CLS")
    else:
        os.system("clear")


def starter_menu():
    clear()
    print("What do you like do?")
    print("1. Create server")
    print("2. Create client")
    print()
    try:
        num: int = int(input("Enter number: "))
        if num < 1 or num > 2:
            print("Invalid number")
            return starter_menu()
    except:
        print("Invalid number")
        return starter_menu()

    if num == 1:
        create_server()
    elif num == 2:
        create_client()


def create_server():
    while 1:
        port: str = input("Enter port: ")
        if not port.isdigit():
            print("Port must be numeric!")
            continue
        if int(port) < 22 or int(port) > 65353:
            print("The port must be in the range: 22-65353")
            continue
        break
    while 1:
        dirname: str = input("Enter directory path: ")
        if not os.path.exists(dirname) or not os.path.isdir(dirname):
            print("Directory not found!")
            continue
        break
    passwords = []
    while 1:
        a = input("Enter password #" + str(len(passwords) + 1) + ": ")
        if a == "" or a == " ":
            break
        passwords.append(a)
    Server(dirname, passwords, int(port))


def client_recv(soc: socket.socket):
    data = b""
    while 1:
        data += soc.recv(1024*1024)
        try:
            message = json.loads(data.decode())
        except:
            continue
        else:
            break
    return message


def create_client():
    while 1:
        ip: str = input("Enter ip address: ")
        splited: list = ip.split(":")
        port: int = 5416
        if len(splited) > 1:
            ip = splited[0]
            if splited[1].isdigit():
                if int(port) < 22 or int(port) > 65353:
                    print("The port must be in the range: 22-65353")
                else:
                    port = int(splited[1])
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            soc.connect((ip, port))
        except:
            print("Server not found!")
            continue
        else:
            break
    soc.send(json.dumps(["connect"]).encode())
    passwords_size = 0
    while 1:
        msg = client_recv(soc)
        if msg[0] == "success":
            break
        elif msg[0] == "enter_password" or msg[0] == "fail":
            if msg[0] == "fail":
                print(msg[1])
            else:
                passwords_size = msg[1]
                print("There are " + str(passwords_size) + " passwords")
            passwords = []
            for u in range(passwords_size):
                passwords.append(input("Enter password #" + str(u + 1) + ": "))
            soc.send(json.dumps(["password", *passwords]).encode())
    print("Entered succeful!")
    print()
    current_folder = ""
    while 1:
        command = input("$> ")
        if command == "help":
            print("ls")
            print("cd <folder path>")
            print("pwd")
            print("download <folder or file path>")
            print("disconnect")
            print("exit")
        elif command == "pwd":
            if current_folder == "":
                print("Path: .")
            else:
                print("Path: ./"+current_folder)
        elif command == "ls":
            if current_folder == "":
                soc.send(json.dumps(["folder", "."]).encode())
            else:
                soc.send(json.dumps(["folder", current_folder]).encode())
            msg = client_recv(soc)
            if msg[0] == "success":
                if len(msg) > 1 and len(msg[1]) > 0:
                    print("? Folders:")
                    print("\n".join(msg[1]))
                if len(msg) > 2 and len(msg[2]) > 0:
                    print("? Files:")
                    print("\n".join(msg[2]))
                if len(msg) < 2:
                    print("Nothing here")
            else:
                print(msg[1])
        elif command.split(" ")[0] == "cd":
            fold = " ".join(command.split(" ")[1:])
            if fold == "..":
                current_folder = "/".join(current_folder.split("/")[:-1])
            else:
                if current_folder == "":
                    soc.send(json.dumps(["folder", "."]).encode())
                else:
                    soc.send(json.dumps(["folder", current_folder]).encode())
                sr = client_recv(soc)
                if sr[0] == "success":
                    folders = sr[1]
                    if fold in folders:
                        if current_folder == "":
                            current_folder = fold
                        else:
                            current_folder = "/".join(current_folder.split("/")+[fold])
                    else:
                        print("Folder not found")
                else:
                    print(sr[1])
        elif command.split(" ")[0] == "download":
            if command.split(" ")[1] != ".":
                downname = " ".join(command.split(" ")[1:])
                if current_folder == "":
                    path = downname+""
                else:
                    path = current_folder+"/"+downname
                if current_folder == "":
                    soc.send(json.dumps(["folder", "."]).encode())
                else:
                    soc.send(json.dumps(["folder", current_folder]).encode())
                sr = client_recv(soc)
                if sr[0] == "success":
                    if downname in sr[1]:
                        iter_download(soc, path, downname)
                    elif downname in sr[2]:
                        soc.send(json.dumps(["file", path]).encode())
                        print("Downloading...")
                        rec = client_recv(soc)
                        if rec[0] == "success":
                            with open(downname, "wb") as r:
                                r.write(eval(rec[1]))
                            print("Downloaded!")
                        else:
                            print(rec[1])
                    else:
                        print("Not found!")
                else:
                    print(sr[1])
            else:
                os.mkdir("Download")
                soc.send(json.dumps(["folder", "."]).encode())
                rec = client_recv(soc)
                if len(rec) > 1:
                    for u in rec[1]:
                        iter_download(soc, u, "Download/" + u)
                    if len(rec) > 2:
                        for u in rec[2]:
                            soc.send(json.dumps(["file", u]).encode())
                            print("Downloading " + u + "...")
                            rec = client_recv(soc)
                            if rec[0] == "success":
                                with open("Download/" + u, "wb") as r:
                                    r.write(eval(rec[1]))
                                print("Downloaded!")
                            else:
                                print(rec[1])
        elif command == "disconnect":
            soc.close()
            clear()
            starter_menu()
        elif command == "exit":
            soc.close()
            os.abort()
        else:
            print("Unknown command")


def iter_download(cl: socket.socket, path: str, save_to: str):
    os.mkdir(save_to)
    cl.send(json.dumps(["folder", path]).encode())
    rec = client_recv(cl)
    if len(rec) > 1:
        for u in rec[1]:
            iter_download(cl, path + "/" + u, save_to + "/" + u)
        if len(rec) > 2:
            for u in rec[2]:
                cl.send(json.dumps(["file", path + "/" + u]).encode())
                print("Downloading " + u + "...")
                rec = client_recv(cl)
                if rec[0] == "success":
                    with open(save_to + "/" + u, "wb") as r:
                        r.write(eval(rec[1]))
                    print("Downloaded!")
                else:
                    print(rec[1])


if __name__ == '__main__':
    starter_menu()
