# Controle de Drone por Gestos

Este projeto implementa um sistema de reconhecimento de gestos offline para controlar um drone usando a câmera. O sistema utiliza MediaPipe para detecção de mãos e interpretação de gestos.

## Requisitos

- Python 3.8 ou superior
- OpenCV
- MediaPipe
- NumPy
- Câmera (webcam ou câmera do drone)

## Instalação

1. Clone este repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Como Usar

Execute o script principal:
```bash
python gesture_control.py
```

### Gestos Suportados

- ✋ Mão aberta (5 dedos): TAKEOFF (Decolar)
- ✊ Mão fechada: LAND (Pousar)
- ☝️ Dedo indicador:
  - Apontando para cima: UP (Subir)
  - Apontando para baixo: DOWN (Descer)
  - Apontando para direita: RIGHT (Direita)
  - Apontando para esquerda: LEFT (Esquerda)
- ✌️ Dedos em V (indicador e médio): FORWARD (Avançar)
- Outros gestos: HOVER (Pairar)

## Como Funciona

O sistema usa MediaPipe para detectar os pontos-chave (landmarks) da mão em tempo real. Estes pontos são analisados para determinar a posição dos dedos e interpretar os gestos correspondentes. O sistema é completamente offline e pode ser executado sem conexão com a internet.

## Personalização

Você pode adicionar novos gestos ou modificar os existentes editando o método `_interpret_gesture` na classe `GestureController`. O sistema usa 21 pontos de referência da mão para determinar a posição dos dedos e interpretar os gestos.