# Primeira energização do PixGate

Use duas saídas de 12 Vcc reguladas com limitação de corrente.
Confira a tensão das fontes em vazio, na partida e sob carga.
J1 alimenta a lógica, com positivo no centro. J8.1 (+) alimenta o ramo da trava e
J8.2 (−) é o retorno. Os retornos se unem na placa. Se as saídas
compartilharem terra fora da placa, registre essa ligação e verifique
se ela não fecha um caminho paralelo para a corrente da carga.

J8 tem proteção por fusível, sem proteção ativa contra inversão. A
serigrafia identifica a polaridade. J2 se destina a solenoide de um
sentido. Confirme a orientação dos cabos com o multímetro antes de
energizar. Desligue as fontes para mudar as conexões.

1. **Lógica isolada.** Deixe J8, J2 e USB desconectados e confirme que
   R26 está ausente. Alimente somente J1 com 12 V regulados. Meça
   +12V após D1, +5V, +3V3 e EN em U2.3 com uma ponta de alta
   impedância. Registre a corrente em vazio no J1, com o rádio em
   repouso e em TX. Confira se o buck inicia e se EN se mantém dentro
   do limite de 6 V da TI. Observe RLY_GATE e o contato do relé no
   primeiro boot antes de conectar uma carga.
2. **Carga fantasma.** Com as fontes desligadas, conecte em J2 um
   resistor de potência de aproximadamente 2,4 Ω, nominal de pelo
   menos 60 W com a montagem e refrigeração indicadas pelo fabricante,
   ou uma lâmpada de 12 V com corrente compatível. O resistor dissipa
   60 W a 12 V e pode atingir temperatura elevada. A lâmpada pode
   exceder 5 A na partida a frio. Alimente J8 com a polaridade
   indicada e aplique um pulso de 3 s, com intervalo de pelo menos
   30 s entre inícios. Registre corrente de pico e de regime, queda
   de tensão em F3, no contato de K1, nas trilhas e nos terminais.
   Registre as temperaturas de F3, K1, bornes, trilhas e vias ao
   longo dos pulsos. Capture no osciloscópio a queda e o ripple
   pico a pico de +5V e +3V3 antes, durante e depois do pulso.
   Use referência local de GND para os rails e ponta diferencial
   para medir diretamente entre COM e NO no fechamento e na abertura.
   Observe se o contato abre após cada pulso e acompanhe a
   temperatura de K1 ao longo de vários pulsos. Interrompa se houver sobrecorrente,
   reinício da lógica, contato colado ou aquecimento anormal.
3. **Boot e reset.** Mantenha a carga fantasma. Confirme a ausência
   de pulsos de J2 e de acionamento de K1 ao ligar J1, no reset do
   ESP e ao desligar/religar as fontes em ordens diferentes.
   Repita após o ensaio de potência.
4. **Solenoide real em bancada.** Depois dos ensaios anteriores e
   da revisão da capacidade de K1, D7 e F3, repita com o solenoide
   representativo em condição controlada, com fonte limitada.
   Capture a tensão diferencial COM–NO e a corrente em um dos
   condutores de J2 no mesmo disparo do osciloscópio. Registre o
   pico, a corrente no instante da abertura, o transiente e o
   decaimento após o desligamento. Confirme que K1 abre em cada
   ciclo, registre temperatura e queda de contato ao longo dos
   pulsos e mantenha o intervalo mínimo de 30 s. A produção exige
   qualificação de comutação repetitiva com a carga representativa,
   incluindo D7 e F3.

Para cada ensaio, registre tensão e limitação das fontes, revisão e
lote da placa, lote de K1/F3/D7, temperatura ambiente, corrente, quedas,
ripple, temperaturas máximas e comportamento no boot e reset.

[Ficha do TPS54331, §§6.1 e 7.3.2](https://www.ti.com/lit/ds/symlink/tps54331.pdf) ·
[Checklist pré-fabricação](pre-fab-checklist.md)
