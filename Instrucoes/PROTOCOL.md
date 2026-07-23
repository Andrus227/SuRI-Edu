# Protocolo Serial Do SuRI-EDU

## Transporte E Enquadramento

- Serial a 115200 baud, 8 bits, sem paridade e 1 stop bit (8N1);
- Quadros ASCII delimitados por `<` e `>`;
- O `>` é o terminador lógico do quadro;
- O supervisório não adiciona CR/LF aos comandos;
- As respostas do Arduino usam `Serial.println` e são seguidas por `\r\n`; receptores devem ignorar bytes fora dos delimitadores;
- O conteúdo entre delimitadores pode ter no máximo 31 bytes;
- Um novo `<` antes de `>` descarta o fragmento anterior e reinicia o enquadramento;
- Quadros vazios, excedentes ou malformados são descartados sem resposta `ERR`.

O firmware lê a UART durante a interpolação, sem `delay()`. Não há timeout para um fragmento incompleto, mas o próximo `<` ressincroniza o parser.

## Regras Lexicais

O protocolo diferencia maiúsculas de minúsculas. `STOP` e `ACK` devem estar em maiúsculas. Campos numéricos contêm apenas `[0-9]+`, sem sinal, espaço ou caracteres adicionais. O protocolo atual não usa caracteres UTF-8 fora de ASCII.

## Movimento

Formato:

```text
<motor,angulo>
```

- `motor`: inteiro decimal de 1 a 6;
- `angulo`: inteiro decimal de 0 a 180;
- exemplo: `<2,135>`.

Os dois campos devem estar presentes. Por exemplo, `<1,>`, `<1,-5>`, `<1,90,2>` e `<7,90>` são inválidos e não alteram os alvos.

Um movimento válido não produz ACK. Um retorno completo da API de escrita significa apenas estado comandado no supervisório; não confirma entrega ao Arduino, processamento ou posição física.

`MovePose` pertence à linguagem da aplicação, não ao protocolo serial. Ele é expandido em até seis quadros `<motor,angulo>` independentes e não é atômico.

O ângulo do quadro é um destino, não um passo instantâneo. Para todos os movimentos recebidos, o firmware calcula independentemente em cada motor um perfil triangular ou trapezoidal limitado por velocidade e aceleração. A atualização ocorre sem `delay()`, preservando a recepção serial durante aceleração, cruzeiro e frenagem. Código Robix, Teach Pendant e biblioteca de métodos usam esse mesmo comportamento sem transmitir degraus intermediários.

Parâmetros atuais do firmware:

- atualização do perfil: 10 ms;
- velocidade máxima: 1 grau a cada 15 ms;
- aceleração: 0,00025 grau/ms²;
- intervalo decorrido considerado em uma atualização: no máximo 50 ms.

Esses parâmetros são parte da implementação do movimento, não do formato do quadro. Um firmware antigo pode aceitar o mesmo protocolo e ainda usar interpolação de velocidade constante.

## Parada Controlada

Solicitação identificada:

```text
<STOP,id>
```

Confirmação:

```text
<ACK,STOP,id>
```

`id` é um inteiro decimal canônico de 1 a 2.147.483.647, sem zeros à esquerda. O supervisório gera IDs crescentes, reiniciando em 1 após o limite, e aceita somente o ACK com o identificador pendente. O firmware valida e devolve o ID, mas não controla sua monotonicidade.

O firmware também aceita o formato legado `<STOP>` e responde `<ACK,STOP>`. A GUI atual sempre usa o formato identificado e não faz fallback automático para firmware antigo.

Ao processar um STOP válido, o firmware copia `posicaoAtual` para `posicaoAlvo` nos seis motores e mantém os objetos `Servo` anexados. A trajetória anterior não é retomada. O firmware continua solicitando o último PWM, mas não mede nem garante torque físico, posição ou capacidade de sustentação.

O STOP também zera imediatamente a velocidade calculada. Ele não usa rampa de desaceleração, pois prolongar deliberadamente a trajetória seria incompatível com a intenção de parada.

## Ordem E Limites Da Parada

O supervisório cancela sua fila de execução e escreve o STOP sem colocá-lo na fila de comandos da rotina. Isso é prioridade local, não prioridade no transporte.

A comunicação serial é FIFO. Bytes já entregues ao driver, USB ou UART permanecem à frente do STOP. Falhas de comunicação também podem impedir seu processamento, portanto não há garantia de latência máxima.

`<ACK,STOP,id>` confirma somente que o firmware processou logicamente aquele STOP. Não confirma posição física, ausência de inércia, torque, alimentação ou integridade mecânica. O recurso não substitui uma parada de emergência física, cabeada e independente.

## Estados E Prazos Do Supervisório

- `requested`: usuário solicitou parada;
- `command_sent`: todos os bytes de `<STOP,id>` foram aceitos pela API serial;
- `controller_interrupted`: o ACK correspondente foi recebido;
- `send_failed`: conexão ausente, exceção, timeout ou escrita parcial;
- `no_confirmation`: ACK não recebido no prazo.

Prazos atuais:

- timeout de escrita: 0,1 segundo;
- espera após abrir a porta, para reset do Arduino: 1,5 segundo;
- espera pelo ACK de STOP: 1 segundo;
- consulta do ACK: a cada 50 ms.

Após falha ou falta de confirmação, uma nova solicitação STOP recebe outro ID. Uma conexão e todo STOP invalidam o estado comandado dos movimentos.

Na parada normal, o supervisório consulta o ACK por até 1 segundo. Ao iniciar outra rotina durante uma execução, ele solicita STOP, cancela a consulta anterior e começa o novo código sem esperar a confirmação. Ao fechar a aplicação, também tenta enviar STOP e desconecta sem aguardar ACK. Esses fluxos são best-effort e não aumentam as garantias físicas descritas acima. Trocas de tela, inclusive para Exemplos com `F6`, seguem o fluxo normal de parada da interface.

## Inicialização Do Firmware

No `setup`, o Arduino anexa os servos nos pinos 8 a 13 e solicita 90 graus para todos. Abrir a serial normalmente reinicia a placa e pode produzir esse movimento antes de qualquer quadro do supervisório.

Como não há leitura da posição física inicial, esse primeiro movimento para 90 graus não pode usar um perfil baseado na posição real. A suavização global aplica-se aos alvos recebidos depois da inicialização.

Os limites de 0 a 180 são apenas a faixa geral do protocolo. Não existem limites mecânicos por junta, prevenção de colisão, leitura de corrente ou fim de curso.

## Compatibilidade E Evolução

O formato de movimento `<motor,angulo>` foi preservado. Evoluções recomendadas:

1. versionar e negociar o protocolo;
2. adicionar IDs, ACK e `ERR` aos movimentos;
3. transmitir telemetria de posição;
4. implementar heartbeat, timeout de montagem no firmware e recuperação de conexão;
5. descartar respostas antigas por sessão;
6. integrar sensores quando posição física confirmada for necessária.
