import dis
import pprint

#D.R.Y.
def get_instructions(future_class_attrs):
    sausepan = []
    for attr in future_class_attrs:
        try:
            result = dis.get_instructions(future_class_attrs[attr])
        except TypeError:
            pass
        else:
            for instr in result:
                if instr.opname == 'LOAD_GLOBAL':
                    if instr.argval not in sausepan:
                        # заполняем список методами, использующимися в функциях класса
                        sausepan.append(instr.argval)
                elif instr.opname == 'LOAD_METHOD':
                    if instr.argval not in sausepan:
                        # заполняем список атрибутами, использующимися в функциях класса
                        sausepan.append(instr.argval)
                elif instr.opname == 'LOAD_ATTR':
                    if instr.argval not in sausepan:
                        # заполняем список атрибутами, использующимися в функциях класса
                        sausepan.append(instr.argval)
    return sausepan

class CliSupervisor(type):
    # Вызывается для создания экземпляра класса, перед вызовом __init__
    def __init__(cls, future_class_name, future_class_parents, future_class_attrs):
        """
          Метод проверяет наличие атрибутов 'accept' и 'listen' из списка required_attributes.
          По умолчанию - ни один из искомых атрибутов не должен быть найден.
        """
        unwanted_methods = ['accept', 'listen', 'socket']
        wanted_methods_sender = ['create_message', 'create_exit_message', 'send_message']
        sausepan = get_instructions(future_class_attrs)
        # pprint(sausepan)
        meths_error = [arg for arg in unwanted_methods if arg in sausepan]
        if meths_error:
            print(f'Найдены неспецифичные для клиента функции!: {meths_error}')
            raise TypeError
        print('Non specific method check OK')
        if cls.__name__ == 'Client_sender':
            meths_missing = [arg for arg in wanted_methods_sender if arg not in sausepan]
            if meths_missing:
                print(f'Отсутствуют атрибуты и методы необходимые для обмена данными!: {meths_missing}')
                raise TypeError
            print('Methods missing check OK')
        elif cls.__name__ == 'Client_reader':
            if 'get_message' not in sausepan:
                print(f'Отсутствует метод get_message!')
                raise TypeError
            print('get_message missing check OK')

        super(CliSupervisor, cls).__init__(future_class_name,
                                             future_class_parents,
                                             future_class_attrs)

class ServSupervisor(type):
    def __init__(cls, future_class_name, future_class_parents, future_class_attrs):
        """
          Метод проверяет отсутствие вызова 'connect' в списке sausepan (кастрюля)
          всех функций и атрибутов AF_INET, SOCK_STREAM.
        """
        unwanted_arguments = 'connect'
        wanted_arguments = ['AF_INET', 'SOCK_STREAM']
        sausepan = get_instructions(future_class_attrs)
        if unwanted_arguments in sausepan:
            print(f'Найдена неспецифичная функция!: {unwanted_arguments}')
            raise TypeError
        print(f'unwanted_arguments check OK')
        attributes_for_warn = [arg for arg in wanted_arguments if arg not in sausepan]
        if attributes_for_warn:
            print(f'Отсутствуют атрибуты необходимые для обмена данными по TCP!: {attributes_for_warn}')
            raise TypeError
        print('wanted_arguments check OK')

        super(ServSupervisor, cls).__init__(future_class_name,
                                             future_class_parents,
                                             future_class_attrs)