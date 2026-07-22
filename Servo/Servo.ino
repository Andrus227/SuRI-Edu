#include <Servo.h>

// SuRI-EDU - Firmware para controle do braço Robix
// Definição dos pinos PWM (Ajuste para as portas reais do seu Arduino)
const int pinosMotores[6] = {8,9,10,11,12,13};
Servo motores[6];

// Arrays de estado para a Interpolação Matemática
float posicaoAtual[6] = {90.0, 90.0, 90.0, 90.0, 90.0, 90.0};
float posicaoAlvo[6]  = {90.0, 90.0, 90.0, 90.0, 90.0, 90.0};

// Variáveis para controle de tempo "Multitarefa" (Sem usar delay!)
unsigned long ultimoTempo[6] = {0, 0, 0, 0, 0, 0};

// --- CONFIGURAÇÃO DA VELOCIDADE DO ROBÔ ---
// Tempo em milissegundos que o motor leva para andar 1 grau.
// 15ms = Rápido e suave | 30ms = Lento para processos precisos
const int VELOCIDADE_MS = 15; 

// Buffer de um quadro: até 31 caracteres entre '<' e '>'.
const byte numChars = 32;
char receivedChars[numChars];
bool newData = false;

void setup() {
  Serial.begin(115200); // Mesma velocidade cravada no Python
  
  // Inicializa os 6 motores na posição de descanso (90 graus)
  for (int i = 0; i < 6; i++) {
    motores[i].attach(pinosMotores[i]);
    motores[i].write(90); 
  }
}

void loop() {
  // 1. Ouve a porta Serial constantemente
  receberComandoSerial();
  
  // 2. Se recebeu um pacote completo (ex: <1,180>), atualiza o Alvo
  if (newData) {
    processarComando();
    newData = false;
  }
  
  // 3. Atualiza a posição de todos os motores suavemente (em Background)
  atualizarMotoresSuavemente();
}

// =================================================================
// FUNÇÕES DE ENGENHARIA (NÃO PRECISA ALTERAR)
// =================================================================

// Lê a serial procurando o início '<' e o fim '>' do pacote.
// Um novo '<' ressincroniza a recepção; quadros excedentes são descartados.
void receberComandoSerial() {
  static bool recvInProgress = false;
  static bool frameOverflow = false;
  static byte ndx = 0;
  char startMarker = '<';
  char endMarker = '>';
  char rc;
  
  while (Serial.available() > 0 && newData == false) {
    rc = Serial.read();
    
    if (rc == startMarker) {
      recvInProgress = true;
      frameOverflow = false;
      ndx = 0;
    } else if (recvInProgress == true) {
      if (rc == endMarker) {
        if (!frameOverflow && ndx > 0) {
          receivedChars[ndx] = '\0';
          newData = true;
        }
        recvInProgress = false;
        frameOverflow = false;
        ndx = 0;
      } else if (!frameOverflow && ndx < numChars - 1) {
        receivedChars[ndx++] = rc;
      } else {
        frameOverflow = true;
      }
    }
  }
}

bool contemSomenteDigitos(const char *texto) {
  if (texto[0] == '\0') {
    return false;
  }
  for (byte i = 0; texto[i] != '\0'; i++) {
    if (texto[i] < '0' || texto[i] > '9') {
      return false;
    }
  }
  return true;
}

bool idParadaValido(const char *texto) {
  if (!contemSomenteDigitos(texto) || texto[0] == '0') {
    return false;
  }
  byte tamanho = strlen(texto);
  return tamanho < 10 || (tamanho == 10 && strcmp(texto, "2147483647") <= 0);
}

// Processa <Motor,Angulo> e o comando de parada <STOP>.
void processarComando() {
  if (strcmp(receivedChars, "STOP") == 0 || strncmp(receivedChars, "STOP,", 5) == 0) {
    char *idParada = NULL;
    if (receivedChars[4] == ',') {
      idParada = receivedChars + 5;
      if (!idParadaValido(idParada)) {
        return;
      }
    }

    // Congela os alvos e mantém os servos anexados; torque físico não é medido.
    for (int i = 0; i < 6; i++) {
      posicaoAlvo[i] = posicaoAtual[i];
    }
    if (idParada == NULL) {
      Serial.println("<ACK,STOP>");
    } else {
      Serial.print("<ACK,STOP,");
      Serial.print(idParada);
      Serial.println(">");
    }
    return;
  }

  char *separador = strchr(receivedChars, ',');
  if (separador == NULL) {
    return;
  }
  *separador = '\0';
  if (strchr(separador + 1, ',') != NULL ||
      !contemSomenteDigitos(receivedChars) ||
      !contemSomenteDigitos(separador + 1)) {
    return;
  }

  char *fimMotor;
  char *fimAngulo;
  long motorRecebido = strtol(receivedChars, &fimMotor, 10);
  long anguloRecebido = strtol(separador + 1, &fimAngulo, 10);
  if (*fimMotor != '\0' || *fimAngulo != '\0') {
    return;
  }
  
  // Validação da faixa do protocolo; não substitui limites mecânicos de segurança.
  if (motorRecebido >= 1 && motorRecebido <= 6 && anguloRecebido >= 0 && anguloRecebido <= 180) {
    int indice = motorRecebido - 1; // Converte ID 1-6 para Indice de Array 0-5
    posicaoAlvo[indice] = anguloRecebido; // Define o novo alvo!
  }
}

// Faz a mágica da interpolação baseada em tempo
void atualizarMotoresSuavemente() {
  unsigned long tempoAtual = millis();
  
  for (int i = 0; i < 6; i++) {
    // Se o motor ainda não chegou na posição alvo
    if (posicaoAtual[i] != posicaoAlvo[i]) {
      
      // Checa se já passou o tempo (VELOCIDADE_MS) para dar o próximo 'passo'
      if (tempoAtual - ultimoTempo[i] >= VELOCIDADE_MS) {
        ultimoTempo[i] = tempoAtual;
        
        // Decide a direção do movimento
        if (posicaoAtual[i] < posicaoAlvo[i]) {
          posicaoAtual[i]++; // Sobe 1 grau
        } else {
          posicaoAtual[i]--; // Desce 1 grau
        }
        
        // Envia o sinal físico para o hardware
        motores[i].write((int)posicaoAtual[i]);

      }
    }
  }
}
