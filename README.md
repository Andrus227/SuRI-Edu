# SuRI-EDU: Sistema de Apoio Robótico Educacional

Projeto da disciplina de Robótica Industrial, orientada pelo Prof. Dr. Ronan Marcelo Martins, para controle didático de um braço Robix com Arduino Mega e uma aplicação desktop em Python.

## Funcionalidades

- Controle de seis servomotores pelo Teach Pendant;
- Modo em tempo real e preparação de poses offline;
- Gravação, edição e execução de rotinas na Linguagem Robix;
- Comandos `MoveTo`, `MovePose` e `Wait`;
- Parada controlada pelo botão STOP ou, durante uma rotina, pela barra de espaço;
- Comunicação serial e interpolação não bloqueante no Arduino;
- Manual integrado acessível por F1.

`MovePose` é uma operação lógica expandida em até seis quadros de movimento. São transmitidos os motores cujo estado comandado esteja desconhecido ou seja diferente do alvo. O estado torna-se desconhecido na inicialização, em toda tentativa de conexão e após um STOP.

## Estrutura

- `main.py`: inicialização da aplicação;
- `suri_edu/app.py`: telas, navegação e execução cancelável das rotinas;
- `suri_edu/motor_controller.py`: validação, transmissão e estado dos motores;
- `suri_edu/robix_language.py`: parser e geração de rotinas Robix;
- `suri_edu/serial_manager.py`: conexão e enquadramento serial;
- `suri_edu/gui_components.py`: editor e componentes reutilizáveis;
- `suri_edu/help_content.py`: conteúdo da ajuda integrada;
- `Instrucoes/HELP.md`: Manual do Operador;
- `Instrucoes/PROTOCOL.md`: contrato entre supervisório e firmware;
- `Servo/Servo.ino`: firmware do Arduino Mega;
- `tests/`: testes unitários e de contrato.

## Requisitos

- Python 3.10 ou superior;
- Arduino IDE para gravar `Servo/Servo.ino`;
- Arduino Mega, braço Robix, fonte adequada aos servos e cabo USB;
- Windows, Linux ou macOS compatível com Tk e as dependências Python.

Em algumas distribuições Linux, pode ser necessário instalar Tk, suporte a ambientes virtuais e configurar a permissão da porta serial, por exemplo pelos pacotes `python3-tk` e `python3-venv` e pelo grupo `dialout`. Drivers USB também podem ser necessários conforme a placa.

## Instalação

Execute os comandos a partir da raiz do repositório.

1. Crie o ambiente virtual:

```bash
python -m venv .venv
```

2. Ative o ambiente conforme o terminal.

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Prompt de Comando:

```bat
.venv\Scripts\activate.bat
```

Git Bash:

```bash
source .venv/Scripts/activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

3. Instale as dependências de execução:

```bash
python -m pip install -r requirements.txt
```

Para desenvolver e testar, use `python -m pip install -r requirements-dev.txt`. Esse arquivo já inclui `requirements.txt`.

## Firmware E Conexão

1. Confira os pinos 8 a 13 definidos em `Servo/Servo.ino` e adapte-os à montagem.
2. Use alimentação dimensionada para os servos e terra comum com o Arduino. Não presuma que a alimentação USB seja adequada para seis servos.
3. Selecione Arduino Mega e a porta correta na Arduino IDE e grave o firmware.
4. Mantenha o braço fixado e sua área livre antes de conectar ou abrir a serial.
5. Execute `python main.py` e selecione a porta no topo da aplicação.

A aplicação e o firmware usam comunicação serial a 115200 baud.

> **Atenção:** ao iniciar, o firmware anexa os seis servos e solicita 90 graus. Abrir a porta serial normalmente reinicia o Arduino e pode repetir esse movimento. Confira a montagem antes de conectar.

Sem Arduino, a interface, o editor e a gravação de poses podem ser usados em modo offline. Tentativas de transmissão falham e não são registradas como estado comandado.

## Linguagem Robix

```text
metodo Inicio:
    MovePose(90, 90, 90, 90, 90, 90)

setup:
    Inicio

loop:
    MoveTo(1, 120)
    Wait(1000)
    MoveTo(1, 60)
    Wait(1000)
```

- `MoveTo(M, A)`: motor de 1 a 6 e ângulo de 0 a 180;
- `MovePose(B, O, C, P, R, G)`: seis ângulos de 0 a 180;
- `Wait(MS)`: espera em milissegundos;
- `setup`: executado uma vez;
- `loop`: repetido indefinidamente até uma parada controlada, troca de tela ou encerramento;
- `metodo Nome`: bloco reutilizável, chamado pelo nome sem parênteses.

Por compatibilidade com rotinas antigas, o reconhecimento de comandos é permissivo e localiza chamadas mesmo com texto antes ou depois delas. Para desativar uma linha, use `//`; apenas acrescentar outro texto pode não impedir o movimento.

Arquivos de rotina usam texto UTF-8 com extensão `.txt`. Consulte a gramática e o comportamento de erros no [Manual do Operador](Instrucoes/HELP.md).

## Operação Segura

Durante uma rotina, espaço e STOP cancelam os callbacks e comandos locais ainda não executados. O botão STOP também pode ser usado fora de uma rotina para interromper uma interpolação manual. A aplicação invalida o estado comandado, tenta escrever `<STOP,id>` e, se a escrita for completa, aguarda por até 1 segundo o `<ACK,STOP,id>` correspondente.

O firmware congela os alvos na última etapa interpolada, mantém os servos anexados e continua solicitando o último PWM. Isso não mede nem garante posição, torque físico ou capacidade de sustentação. O transporte serial é FIFO: bytes anteriores permanecem à frente do STOP, portanto não há garantia de latência máxima.

Trocar de tela durante uma rotina solicita STOP. Iniciar outra rotina ou fechar a aplicação durante uma execução envia STOP de forma best-effort, mas esses fluxos não aguardam a confirmação antes de continuar ou encerrar.

> **Limitação de segurança:** a parada depende do computador, aplicação, cabo, porta serial, firmware e alimentação. Ela não substitui uma parada de emergência física, cabeada e independente do software.

## Estado Dos Motores

- **Desejado:** ângulo solicitado pelo operador ou pela rotina;
- **Comandado:** ângulo cujo quadro inteiro foi aceito pela API serial;
- **Confirmado:** ângulo informado por telemetria ou sensor.

Não há ACK de movimento nem sensor de posição nesta versão. O estado confirmado permanece desconhecido e a posição física não deve ser inferida dos sliders.

## Testes E Qualidade

```bash
python -m pytest --cov=. --cov-report=term-missing
python -m ruff check .
python -m ruff format --check .
```

## Limitações E Próximos Passos

- Definir limites mecânicos por junta e prevenção de colisões;
- Adicionar ACK de movimento e telemetria contínua;
- Versionar o protocolo, adicionar heartbeat e recuperação automática;
- Integrar sensores para posição física confiável;
- Criar visualização esquemática ou 3D;
- Distinguir visualmente posições desejada, comandada e confirmada.

## Documentação

- Manual completo: [`Instrucoes/HELP.md`](Instrucoes/HELP.md)
- Protocolo serial: [`Instrucoes/PROTOCOL.md`](Instrucoes/PROTOCOL.md)
- Repositório: https://github.com/Andrus227/SuRI-Edu

## Contato E Autoria

André Victor Lucio, `andrelucio.ifmt@gmail.com`

Andrus227 e equipe da disciplina de Robótica Industrial.
