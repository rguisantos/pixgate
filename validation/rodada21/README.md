# Validação da rodada 21

`checks.txt` contém as saídas dos verificadores e da exportação.
`netlist-larguras-vias.txt` contém o diff por pad contra `2a5701e`,
a medição das trilhas e a identificação dos furos em pads soldáveis.
O último teste retorna 1 enquanto houver esses furos. O
`place-check.txt` contém a colocação antes e depois de cada item.
O relatório nativo do DRC está em
[`../drc/rodada21-drc.rpt`](../drc/rodada21-drc.rpt).

Reprodução na raiz do projeto, com o ambiente KiCad 9.0.2 configurado
por `tools/rebuild-kicad-env.sh` e `source tools/env.sh`. A comparação
de cobre exige também Shapely no mesmo Python que importa `pcbnew`.

```sh
git show 2a5701e:hardware/pixgate.kicad_pcb > /tmp/pixgate-r20.kicad_pcb
python3 hardware/net_audit.py
python3 hardware/check_sync.py
python3 hardware/check_pads.py
python3 tools/manual-routing/check_pad_freeze.py
python3 hardware/place_check.py
kicad-cli pcb drc --severity-all --all-track-errors --exit-code-violations hardware/pixgate.kicad_pcb
python3 validation/check_rodada21.py /tmp/pixgate-r20.kicad_pcb hardware/pixgate.kicad_pcb
python3 hardware/check_routing.py
bash hardware/validate_prefab.sh
bash hardware/export_gerbers.sh
```

Para as exclusões de montagem, conferir as colunas `Reference` de
`pixgate-BOM.csv` e `Ref` de `pixgate-pos.csv` em `hardware/fab/`.
