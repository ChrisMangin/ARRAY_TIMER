<div align="center">

# ARRAY_TIMER
**Studio 5000 Add-On Instruction - Rev 1.0**

[![Studio 5000](https://img.shields.io/badge/Studio_5000-v32.04%2B-CC0000?style=flat-square)](https://github.com/ChrisMangin/ARRAY_TIMER)
[![Controller](https://img.shields.io/badge/Controller-ControlLogix%20%7C%20CompactLogix-0078D4?style=flat-square)](https://github.com/ChrisMangin/ARRAY_TIMER)
[![Channels](https://img.shields.io/badge/Channels-1050-22c55e?style=flat-square)](https://github.com/ChrisMangin/ARRAY_TIMER)
[![Memory Savings](https://img.shields.io/badge/Memory-~5x_smaller-f97316?style=flat-square)](https://github.com/ChrisMangin/ARRAY_TIMER)

</div>

---

Array-based multi-channel software timer with programmable delay. A single internal free-running TON drives up to **1,050 independent channels**, each with its own delay preset and done flag.

## Why This Exists

Standard Studio 5000 `TIMER` tags are large:

| Approach | 1,050 channels | Memory usage |
|----------|---------------|--------------|
| Native `TIMER` tags | 1,050 x 40 bytes | **42,000 bytes** |
| `ARRAY_TIMER` | Single AOI + arrays | **~8,500 bytes** |

**~5x smaller.** One instance of `ARRAY_TIMER` replaces 1,050 native TIMER tags driven by a single free-running internal TON.

---

## Parameters

| Parameter | Type | Direction | Description |
|-----------|------|-----------|-------------|
| `CM_Inc` | DINT | Input | Channel index (0-1049); used when `AUTO_INC = 0` |
| `AUTO_INC` | BOOL | Input | `0` = manual index; `1` = auto-cycle 0 to 1049 |
| `PRE_IN` | DINT | Input | Timer period in ms (shared by all channels; must be > 0) |
| `Cond_EN` | BOOL | Input | Rising edge starts delay; falling edge resets channel state |
| `Delay_PRE` | DINT | Input | Desired delay in ms (>= 0) |
| `T_DN` | BOOL | Output | One-scan pulse per timer period |
| `T_ACC` | DINT | Output | Live timer accumulator in ms |
| `Delay_DN` | BOOL | Output | `True` when delay has elapsed; held until `Cond_EN` drops |
| `CM_Fault` | BOOL | Output | Out-of-range index or `PRE_IN <= 0`; delay logic suspended |
| `EFF_INC` | DINT | Local (RO) | Active channel this scan - index your own arrays from other rungs |

---

## Rung Map

| Rung | Function |
|------|----------|
| 0 | Header / overview NOP |
| 1 | Limitations (channel count, delay range, sweep time) |
| 2 | Index resolution |
| 3 | Auto-increment |
| 4 | Preset sync |
| 5 | Free-running timer (TON) |
| 6 | `T_DN` output |
| 7 | `T_ACC` output |
| 8 | Fault check |
| 9 | Landing point calculation (one-shot on `Cond_EN` rise) |
| 10 | Reset on disable |
| 11 | Cycle countdown |
| 12 | Done flag |
| 13 | Output (`Delay_DN`) |

---

## How the Delay Works

On a `Cond_EN` rising edge, the AOI computes a landing point in the free-running timer cycle:

```
LANDING_PT = (T_ACC + Delay_PRE) MOD PRE_IN
COUNT      = floor((T_ACC + Delay_PRE) / PRE_IN)
```

`COUNT` decrements by one on every `T_DN` pulse. `Delay_DN` fires when `COUNT = 0` and `T_ACC >= LANDING_PT`.

---

## Expanding Channel Count

1. Increase array dimensions of `LANDING_PT`, `COUNT`, `FOUND`, `DN_FLAG`.
2. Update `CMP(EFF_INC > 1049)` in Rung 8.
3. Update `MOD 1050` in Rung 3.

---

## Requirements

- Studio 5000 / RSLogix 5000 **v32.04+**
- Any **ControlLogix** or **CompactLogix** controller

---

## Files

| File | Description |
|------|-------------|
| `ARRAY_TIMER.L5X` | AOI export - import directly into Studio 5000 |
| `gen_aois_v2.py` | Python generator script (regenerates both this AOI and ARRAY_CTUD) |

---

## Related

- [**ARRAY_CTUD**](https://github.com/ChrisMangin/ARRAY_CTUD) - same pattern applied to counters: 1,050 independent up/down counter channels, ~9x smaller than native COUNTER tags

---

## License

MIT - see [LICENSE](LICENSE).
