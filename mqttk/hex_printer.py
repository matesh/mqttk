"""
MQTTk - Lightweight graphical MQTT client and message analyser

Copyright (C) 2022  Máté Szabó

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

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
    for chunk_count in itertools.count(0):
        start = (chunk_size+1)*(chunk_count)
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
