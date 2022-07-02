from functools import partial


def validate_int(d, i, P, s, S, v, V, W):
    try:
        int(S)
    except Exception:
        return False
    return True


def validate_name(name, name_list):
    if name not in name_list:
        return name

    template = name + " {}"
    index = 1
    while template.format(index) in name_list:
        index += 1
    return template.format(index)


def clear_combobox_selection(*_, combobox_instance):
    current_selection = combobox_instance.get()
    combobox_instance.set("")
    combobox_instance.set(current_selection)


def get_clear_combobox_selection_function(combobox_instance):
    return partial(clear_combobox_selection, combobox_instance=combobox_instance)
