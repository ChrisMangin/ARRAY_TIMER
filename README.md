# ARRAY_TIMER
**Studio 5000 Add-On Instruction (AOI) — Rev 1.0**

Array-based multi-channel software timer with programmable delay.  
A single internal free-running TON drives up to **1050 independent channels**, each with its own delay preset and done flag.

## Why this exists
Standard Studio 5000 `TIMER` tags cost **40 bytes each**.  
1050 TIMER tags = 42,000 bytes.  
`ARRAY_TIMER` stores all 1050 channels in arrays: **~8,500 bytes** — roughly **5× smaller**.

## Key parameters
| Parameter | Type | Direction | Description |
|-----------|------|-----------|-------------|
| `CM_Inc` | DINT | Input | Channel index (0–1049), used when `AUTO_INC = 0` |
| `AUTO_INC` | BOOL | Input | 0 = manual index via `CM_Inc`; 1 = auto-cycle 0→1049 |
| `PRE_IN` | DINT | Input | Timer period in ms (shared by all channels, must be > 0) |
| `Cond_EN` | BOOL | Input | Rising edge starts delay; falling edge resets channel state |
| `Delay_PRE` | DINT | Input | Desired delay in ms (≥ 0) |
| `T_DN` | BOOL | Output | One-scan pulse per timer period |
| `T_ACC` | DINT | Output | Live timer accumulator in ms |
| `Delay_DN` | BOOL | Output | True when delay has elapsed; held until `Cond_EN` drops |
| `CM_Fault` | BOOL | Output | Out-of-range index or `PRE_IN ≤ 0`; delay logic suspended |
| `EFF_INC` | DINT | Local (RO) | Active channel this scan — read from other rungs to index your own arrays |

## Rung map
| Rung | Function |
|------|----------|
| 0 | Header / overview NOP |
| 1 | **Limitations** (channel count, delay range, sweep time) |
| 2 | Index resolution |
| 3 | Auto-increment |
| 4 | Preset sync |
| 5 | Free-running timer (TON) |
| 6 | T_DN output |
| 7 | T_ACC output |
| 8 | Fault check |
| 9 | Landing point calculation (one-shot on `Cond_EN` rise) |
| 10 | Reset on disable |
| 11 | Cycle countdown |
| 12 | Done flag |
| 13 | Output (`Delay_DN`) |

## How the delay works
On `Cond_EN` rising edge:
```
LANDING_PT = (T_ACC + Delay_PRE) MOD PRE_IN
COUNT      = floor((T_ACC + Delay_PRE) / PRE_IN)
```
`COUNT` decrements once per `T_DN` pulse.  
`Delay_DN` fires when `COUNT = 0` AND `T_ACC ≥ LANDING_PT`.

## Expanding channel count
1. Increase dimensions of `LANDING_PT`, `COUNT`, `FOUND`, `DN_FLAG` arrays.
2. Update `CMP(EFF_INC > 1049)` in Rung 8.
3. Update `MOD 1050` in Rung 3.

## Requirements
- Studio 5000 / RSLogix 5000 v32.04+
- Controller: any ControlLogix / CompactLogix

## File
| File | Description |
|------|-------------|
| `ARRAY_TIMER.L5X` | AOI export — import directly into Studio 5000 |
| `gen_aois_v2.py` | Python generator script (regenerates both this AOI and ARRAY_CTUD) |
