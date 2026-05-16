# SuRI-EDU: Sistema de Apoio Robótico Educacional com Robix + Arduino Mega

Projeto desenvolvido na disciplina de Robótica Industrial (Prof. Dr. Ronan Marcelo Martins), com foco no controle de um braço robótico do kit Robix por meio de software próprio em Python.

## Objetivo

Desenvolver uma interface para controle de servomotores do braço robótico com finalidade didática em laboratório, oferecendo alternativa ao software original do kit Robix.

## Funcionalidades principais

- Controle em tempo real por sliders;
- Envio de poses individuais;
- Gravação de poses ensinadas;
- Geração e execução de rotinas (interpretador de comandos);
- Salvamento de rotinas em arquivo `.txt`;
- Comunicação serial com Arduino Mega.

## Arquitetura (resumo)

- **Aplicação desktop (Python):**
  - `main.py`
  - `app.py`
  - `gui_components.py`
  - `serial_manager.py`
- **Firmware (Arduino):**
  - `Servo/Servo.ino`
- **Comunicação:**
  - Porta serial (notebook → Arduino Mega)

## Experimento realizado

Foi implementada e validada uma rotina de **pick-and-place**, em que o braço:

1. pega um objeto em uma posição inicial;
2. transporta para outra posição;
3. retorna o objeto à posição original.

A tarefa foi executada com sucesso em laboratório.

## Requisitos

- Python 3.x
- Arduino IDE (para upload de `Servo/Servo.ino`)
- Arduino Mega
- Kit Robix com servomotores
- Cabo USB

## Instalação (Python)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
```

> Se ainda não existir `requirements.txt`, gere com:
```bash
pip freeze > requirements.txt
```

## Execução

1. Carregue o firmware do Arduino em `Servo/Servo.ino`.
2. Conecte o Arduino Mega ao notebook.
3. Execute o software Python:

```bash
python main.py
```

4. Selecione a porta serial correta e inicie o controle.

> Dica: pressione F1 dentro do aplicativo para abrir o Manual do Operador do SuRI-EDU.

## Ajuda

- Manual completo em `HELP.md`.

## Estrutura do projeto

- `Servo/` → firmware Arduino
- `images/` → fotos do protótipo e da interface (sugerido)
- `results/` → logs e resultados de testes (sugerido)
- `article/` → rascunho do artigo para submissão (sugerido)

## Limitações atuais

- Testado em ambiente de laboratório com hardware específico;
- Dependência de configuração manual da porta serial;
- Ausência de validação automática de colisão/limites mecânicos.

## Autores

- Andrus227 e equipe da disciplina de Robótica Industrial.
