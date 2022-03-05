
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
