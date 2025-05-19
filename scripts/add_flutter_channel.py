import os
import re

SCRIPT_TAG = '\n<script src="/scripts/flutter.js"></script>\n'

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if '<a href="javascript:' not in content:
        return  # Ignora arquivos sem a referência

    # Regex para encontrar <body> seguido de <div class="...">
    pattern = re.compile(r'(<body>\s*)(<div class="[\w-]*">)', re.IGNORECASE)
    match = pattern.search(content)

    if match:
        # Insere o script entre <body> e <div>
        new_content = pattern.sub(r'\1' + SCRIPT_TAG + r'\2', content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Modificado: {file_path}')
    else:
        print(f'Sem correspondência para substituição: {file_path}')


def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                process_file(os.path.join(root, file))


if __name__ == "__main__":
    pasta_alvo = 'src/'
    process_directory(pasta_alvo)
