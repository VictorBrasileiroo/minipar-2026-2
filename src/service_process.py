"""Bounded subprocess I/O and ownership of the process tree (no global state)."""
from __future__ import annotations
import ctypes
import os
import signal
import subprocess
import threading
import time


def _windows_job(process):
    # The child starts suspended: it cannot spawn descendants before assignment.
    from ctypes import wintypes as w
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    class Basic(ctypes.Structure):
        _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                    ("flags", w.DWORD), ("min_ws", ctypes.c_size_t), ("max_ws", ctypes.c_size_t),
                    ("active", w.DWORD), ("affinity", ctypes.c_size_t), ("priority", w.DWORD), ("scheduling", w.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in ("read", "write", "other", "read_bytes", "write_bytes", "other_bytes")]
    class Extended(ctypes.Structure):
        _fields_ = [("basic", Basic), ("io", IO), ("process_memory", ctypes.c_size_t),
                    ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
    kernel.CreateJobObjectW.restype = w.HANDLE
    kernel.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
    kernel.CloseHandle.argtypes = [w.HANDLE]
    job = kernel.CreateJobObjectW(None, None)
    if not job: raise ctypes.WinError(ctypes.get_last_error())
    try:
        info = Extended()
        info.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.AssignProcessToJobObject(job, w.HANDLE(int(process._handle))):
            raise ctypes.WinError(ctypes.get_last_error())
        resume = ctypes.WinDLL("ntdll").NtResumeProcess
        resume.argtypes = [w.HANDLE]
        resume.restype = ctypes.c_long
        if resume(w.HANDLE(int(process._handle))) != 0: raise OSError("Cannot resume owned process")
    except BaseException:
        kernel.CloseHandle(job)
        raise
    return lambda: kernel.CloseHandle(job)


def run_bounded(command, *, cwd, stdin="", timeout=10, limit=1024 * 1024, env=None):
    """Drain both pipes concurrently; retain at most limit bytes per stream."""
    started = time.monotonic()
    process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=0x00000004 | 0x08000000 if os.name == "nt" else 0,
        start_new_session=os.name != "nt")
    close_job = None
    threads = []
    buffers = [bytearray(), bytearray()]
    truncated = [False, False]
    failures = []
    def read(pipe, index):
        try:
            while True:
                chunk = pipe.read(65536)
                if not chunk: break
                available = limit - len(buffers[index])
                buffers[index].extend(chunk[:available])
                if len(chunk) > available: truncated[index] = True
        except Exception as exc:
            failures.append(exc)
        finally:
            pipe.close()
    def write():
        try:
            process.stdin.write(stdin.encode("utf-8"))
            process.stdin.flush()
        except (BrokenPipeError, OSError): pass
        finally: process.stdin.close()
    def kill_tree():
        nonlocal close_job
        if os.name == "nt":
            if close_job:
                close_job()
                close_job = None
            elif process.poll() is None: process.kill()
        else:
            try: os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError: pass
    timed_out = False
    try:
        if os.name == "nt": close_job = _windows_job(process)
        for pipe, index in ((process.stdout, 0), (process.stderr, 1)):
            thread = threading.Thread(target=read, args=(pipe, index), daemon=True)
            thread.start(); threads.append(thread)
        thread = threading.Thread(target=write, daemon=True)
        thread.start(); threads.append(thread)
        try:
            process.wait(timeout=max(0.001, timeout - (time.monotonic() - started)))
        except subprocess.TimeoutExpired:
            timed_out = True
    finally:
        kill_tree()
        process.wait()
        for thread in threads: thread.join()
        for pipe in (process.stdin, process.stdout, process.stderr):
            if not pipe.closed: pipe.close()
    if failures: raise failures[0]
    def decode(data, index):
        # Replacement characters can expand the retained raw bytes by up to 3x.
        # Account for this second cut as well as the original bounded buffer.
        encoded = data.decode("utf-8", errors="replace").encode("utf-8")
        if len(encoded) > limit: truncated[index] = True
        # Drop an incomplete final UTF-8 sequence; normalize native CRLF to LF.
        return encoded[:limit].decode("utf-8", errors="ignore").replace("\r\n", "\n")
    stdout, stderr = decode(buffers[0], 0), decode(buffers[1], 1)
    return dict(returncode=None if timed_out else process.returncode, timed_out=timed_out,
        stdout=stdout, stderr=stderr, stdout_truncated=truncated[0],
        stderr_truncated=truncated[1], duration_ms=round((time.monotonic()-started)*1000))
