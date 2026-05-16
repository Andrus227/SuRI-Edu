# Manual do Operador - SuRI-EDU

## 1. Visão Geral

O SuRI-EDU é um supervisório educacional para controle do braço Robix com Arduino Mega. Ele integra interface desktop, comunicação serial e firmware no Arduino para executar movimentos. O sistema foi pensado para uso didático em laboratório, com fluxo simples e atalhos rápidos.

## 2. Primeiros Passos

1) Instale Python 3.x.
2) Crie e ative o ambiente virtual:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate
```

3) Instale dependências:

```bash
pip install -r requirements.txt
```

4) Grave o firmware no Arduino Mega:

- Abra `Servo/Servo.ino` na Arduino IDE.
- Selecione a placa e a porta correta.
- Clique em Upload.

5) Execute o aplicativo:

```bash
python main.py
```

6) Selecione a porta serial correta no topo direito e teste um comando simples.

## 3. Conexão Serial

- Abra o menu de portas no topo direito e selecione a porta do Arduino.
- Use "Atualizar..." se a porta não aparecer.
- O modo Monitor exibe pacotes no log para depuração.

Se aparecer "Nenhuma porta", verifique cabo USB, driver, permissão e Arduino ligado.

## 4. Teach Pendant (Sliders)

- Controle manual das juntas por sliders.
- Modo Tempo Real envia o comando durante o arraste; desligado envia ao soltar.
- "Enviar Pose" sincroniza o robô com a pose atual.
- "Salvar Ponto" grava pontos sequenciais e "Exportar" gera um método.

## 5. Editor de Código

O editor interpreta a Linguagem Robix com blocos `setup`, `loop` e `metodo`.

Comandos suportados:

- `MoveTo(M, A)`
- `MovePose(B, O, C, P, R, G)`
- `Wait(MS)`

Exemplo:

```text
setup:
    MoveTo(1, 90)
loop:
    MovePose(90, 90, 90, 90, 90, 90)
    Wait(1000)
```

O dicionário à direita mostra a sintaxe e parâmetros.

## 6. Painel de Execução

- Carregue um arquivo `.txt` e execute sem editar.
- Use F5 para abrir o painel e F9 para iniciar a rotina.
- Para editar, use o Editor (F4).

## 7. Atalhos e Operação

- F1: Manual
- F2: Menu
- F3: Teach Pendant
- F4: Editor
- F5: Painel
- F9: Executar rotina (Editor/Painel)
- Espaço: parada de emergência (não funciona dentro de campos de texto)
- Setas e Tab: navegação e ajuste fino dos motores no Teach Pendant

## 8. FAQ

**Posso usar sem Arduino?**
Sim, é possível testar a interface, mas não haverá movimento.

**Os motores não se mexem, o que fazer?**
Verifique conexão serial, porta correta e firmware gravado.

**Onde ficam as rotinas?**
Salve como `.txt` e abra no Editor ou no Painel.

## 9. Troubleshooting

- Erro de comunicação Serial: confirme porta correta e velocidade 115200.
- Nenhuma porta: verifique cabo, driver e reinicie o Arduino.
- Sintaxe não reconhecida: confirme MoveTo/MovePose/Wait e indentação.
- Recursão detectada: evite chamar método dentro dele mesmo.
- Parada inesperada: pressione Espaço apenas em situações de risco.

## 10. Suporte e Bugs

Antes de solicitar suporte, anote: versão do Python, sistema operacional, passos para reproduzir e o arquivo `.txt` utilizado. Inclua trechos do log exibido na parte inferior do aplicativo.

Contato: equipe do projeto/disciplinas listada no `README.md`.
