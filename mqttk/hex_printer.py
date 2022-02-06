import itertools

BEGIN_PRINTABLES = 33
END_PRINTABLES = 126


def hex_group_formatter(iterable):
    chunks = [iter(iterable)] * 4
    return '   '.join(
        ' '.join(format(x, '0>2x') for x in chunk)
        for chunk in itertools.zip_longest(*chunks, fillvalue=0))


def ascii_group_formatter(iterable):
    return ''.join(
        chr(x) if BEGIN_PRINTABLES <= x <= END_PRINTABLES else '.'
        for x in iterable)


def hex_viewer(message_data, chunk_size=16):
    header = hex_group_formatter(range(chunk_size))
    yield 'ADDRESS        {:<53}       ASCII'.format(header)
    yield ''
    template = '{:0>8x}       {:<53}       {}'
    for chunk_count in itertools.count(1):
        start = (chunk_size+1)*(chunk_count-1)
        finish = start + chunk_size
        if len(message_data) < finish:
            finish = len(message_data)
        chunk = message_data[start:finish]
        if not chunk:
            return
        yield template.format(
            chunk_count * chunk_size,
            hex_group_formatter(chunk),
            ascii_group_formatter(chunk))
