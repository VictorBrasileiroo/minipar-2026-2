"""Prova nativa do retry de connect e da leitura completa do canal herdado."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from src.cpp_template import _CPP_HEADER


class ChannelTransportTest(unittest.TestCase):
    def test_delayed_listener_and_large_message(self):
        default_gpp = Path("C:/msys64/ucrt64/bin/g++.exe")
        cxx = os.environ.get("CXX") or (str(default_gpp) if default_gpp.is_file() else shutil.which("g++"))
        if not cxx:
            self.skipTest("G++ indisponível")
        env = dict(os.environ)
        env["PATH"] = str(Path(cxx).parent) + os.pathsep + env.get("PATH", "")
        source = _CPP_HEADER + r'''
int main() {
#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return 2;
#endif
    // Reserva uma porta efemera e a libera antes do teste do canal.
    MiniParSocket probe = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = 0;
    if (bind(probe, (sockaddr*)&addr, sizeof(addr)) != 0) return 3;
#ifdef _WIN32
    int len = sizeof(addr);
#else
    socklen_t len = sizeof(addr);
#endif
    if (getsockname(probe, (sockaddr*)&addr, &len) != 0) return 4;
    int port = ntohs(addr.sin_port);
    CLOSE_SOCK(probe);

    MiniParChannel channel("127.0.0.1", port);
    std::string expected(10000, 'x');
    std::vector<std::string> received;
    std::thread server([&] {
        std::this_thread::sleep_for(std::chrono::milliseconds(350));
        for (int i = 0; i < 3; ++i) {
            received.push_back(channel.receiveData());
            std::this_thread::sleep_for(std::chrono::milliseconds(25));
        }
    });
    channel.sendData(expected); // A primeira tentativa ocorre antes do listen.
    channel.sendData("second");
    channel.sendData("third");
    server.join();
    if (received != std::vector<std::string>{expected, "second", "third"}) return 5;
    auto started = std::chrono::steady_clock::now();
    bool failed = false;
    try { channel.sendData("without listener"); }
    catch (const std::runtime_error&) { failed = true; }
    if (!failed || std::chrono::steady_clock::now() - started > std::chrono::seconds(7)) return 6;
#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as folder:
            cpp = Path(folder) / "channel.cpp"
            exe = Path(folder) / ("channel.exe" if os.name == "nt" else "channel")
            cpp.write_text(source, encoding="utf-8")
            command = [cxx, "-std=c++20", "-O2", "-pthread", str(cpp), "-o", str(exe)]
            if os.name == "nt":
                command.append("-lws2_32")
            build = subprocess.run(command, capture_output=True, text=True, timeout=60, env=env)
            self.assertEqual(build.returncode, 0, f"exit={build.returncode}: {build.stderr}")
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=15, env=env)
            self.assertEqual(run.returncode, 0, run.stderr)


if __name__ == "__main__":
    unittest.main()
