#!/usr/bin/env python3
"""Allow employee IDs in the pinned Open WebUI sign-in form."""

from pathlib import Path
import sys


path = Path(sys.argv[1])
source = path.read_text()
changes = (
    ("{$i18n.t('Email')}</label", "{mode === 'signin' ? 'Mã nhân viên hoặc Email' : $i18n.t('Email')}</label"),
    ('type="email"', "type={mode === 'signin' ? 'text' : 'email'}"),
    ('autocomplete="email"', "autocomplete={mode === 'signin' ? 'username' : 'email'}"),
    ("placeholder={$i18n.t('Enter Your Email')}", "placeholder={mode === 'signin' ? 'Nhập mã nhân viên (VD: HP0001) hoặc Email' : $i18n.t('Enter Your Email')}"),
)

for old, new in changes:
    if old in source:
        if source.count(old) != 1:
            raise SystemExit(f"Expected one match for {old!r}, found {source.count(old)}")
        source = source.replace(old, new)
    elif new not in source:
        raise SystemExit(f"Neither original nor patched text found: {old!r}")

path.write_text(source)
