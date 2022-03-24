import functools
from datetime import datetime


def logexc(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Преобразуем в строку имена аргументов и их значения
        args_rep = [repr(arg) for arg in args]
        kwargs_rep = [f"{k}={v}" for k, v in kwargs.items()]
        sig = ", ".join(args_rep + kwargs_rep)
        # Определяем блок Try для кода, который будем логировать
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print("Time: ", datetime.now().strftime("%Y-%m-%d [%H:%M:%S]"))
            print("Arguments: ", sig)
            print("Error:\n")
            raise
    return wrapper



@logexc
def divint(list_args, dict_args):
    '''Программа делит мягкое на крупное'''
    res=[]
    divider = [v for k, v in dict_args.items()]
    for i in list_args:
        for j in divider:
            res.append(i/j)
    print(res)
    return res


divint([10,20,30],{'a':2,'b':0,'c':4})

