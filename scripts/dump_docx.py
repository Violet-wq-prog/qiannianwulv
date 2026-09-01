# -*- coding: utf-8 -*-
"""Dump docx paragraphs + tables with indices, for targeted in-place edits."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")

from docx import Document

def dump(path):
    doc = Document(path)
    print(f"===== {path} =====")
    body = doc.element.body
    p_idx = 0
    t_idx = 0
    for child in body.iterchildren():
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            texts = ''.join(node.text or '' for node in child.iter() if node.tag.split('}')[-1] == 't')
            print(f"[P{p_idx}] {texts}")
            p_idx += 1
        elif tag == 'tbl':
            print(f"[TABLE {t_idx}]")
            for row in child.iter():
                if row.tag.split('}')[-1] == 'tr':
                    cells = []
                    for tc in row.iter():
                        if tc.tag.split('}')[-1] == 'tc':
                            t = ''.join(n.text or '' for n in tc.iter() if n.tag.split('}')[-1] == 't')
                            cells.append(t)
                    print("  | " + " | ".join(cells))
            print(f"[/TABLE {t_idx}]")
            t_idx += 1

if __name__ == "__main__":
    dump(sys.argv[1])
