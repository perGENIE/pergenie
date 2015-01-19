import psutil

def is_up(ps_name):
    return True in [psutil.Process(pid).name() == ps_name for pid in psutil.get_pid_list()]
