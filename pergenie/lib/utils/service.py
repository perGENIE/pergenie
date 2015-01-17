import psutil

def is_up(ps_name):
    return True in [ps.name in ps_name for ps in psutil.get_process_list()]
