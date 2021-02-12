import argparse
import re

import nbformat

def convert(fname):
    nb = nbformat.read(fname, nbformat.NO_CONVERT)
    for cell in nb.cells:
        if cell.cell_type != 'code': continue
        m = re.match(r'^--export\n', cell.source)
        if not m: continue
        print(cell.source[len(m[0]):])
        print()

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Converts Lua notebook to *.lua file')
    p.add_argument(
        'notebook',
        help='path to notebook'
    )
    args = p.parse_args()
    convert(args.notebook)
