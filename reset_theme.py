import os

# 1. Reset config.toml to pure black and white
with open('.streamlit/config.toml', 'w', encoding='utf-8') as f:
    f.write('''[theme]
primaryColor="#1E88E5"
backgroundColor="#000000"
secondaryBackgroundColor="#111111"
textColor="#FFFFFF"
font="sans serif"
''')

# 2. Strip all CSS from utils.py to return to native Streamlit look
with open('utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('def apply_custom_theme():')
if idx != -1:
    content = content[:idx]

new_css = '''def apply_custom_theme():
    pass
'''

with open('utils.py', 'w', encoding='utf-8') as f:
    f.write(content + new_css)
