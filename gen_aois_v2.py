#!/usr/bin/env python3
"""Generate two Studio 5000 AOI L5X files.
   ARRAY_TIMER - self-contained multi-channel software delay with internal timer
                 (formerly TIMED_DELAY, then ARRAY_DELAY)
   ARRAY_CTUD  - multi-channel up/down counter
                 (formerly INDEX_COUNTER)
   Rev 2.3:
     - AOIs renamed: TIMED_DELAY -> ARRAY_TIMER, INDEX_COUNTER -> ARRAY_CTUD
     - LIMITATIONS rung moved to rung 1 (2nd rung) in both AOIs for immediate
       visibility; all working rungs shifted +1 and cross-references updated.
   Rev 2.2:
     - T_TT output removed from ARRAY_TIMER (redundant TIMER.TT mirror).
     - C_CU / C_CD kept on ARRAY_CTUD (one-scan pulse diagnostics, zero memory cost).
   Rev 2.1:
     - AUTO_INC replaces USE_EXT_INC; EFF_INC exposed Read Only.
     - SEL() replaced with XIC/XIO branches throughout.
"""

import os

OUTPUT_DIR = r"C:\Users\cmanginu\Desktop\Custom_Programs\Updated_AOIs"
REV  = "1.0"
N    = 1050
NOW  = "2026-07-18T12:00:00.000Z"
EXP  = "Fri Jul 18 12:00:00 2026"
AUTH = r"ANT\cmanginu"
CTRL = "DSM5_CP01"
BOM  = "\ufeff"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def sz(n):    return "[" + ",".join(["0"]   * n) + "]"
def bz(n):    return "[" + ",".join(["2#0"] * n) + "]"
def elems(n): return "\n".join(f'<Element Index="[{i}]" Value="0"/>' for i in range(n))

def sys_params():
    return [
        '<Parameter Name="EnableIn" TagType="Base" DataType="BOOL" Usage="Input" '
        'Radix="Decimal" Required="false" Visible="false" ExternalAccess="Read Only">\n'
        '<Description>\n<![CDATA[Enable Input - System Defined Parameter]]>\n</Description>\n</Parameter>',
        '<Parameter Name="EnableOut" TagType="Base" DataType="BOOL" Usage="Output" '
        'Radix="Decimal" Required="false" Visible="false" ExternalAccess="Read Only">\n'
        '<Description>\n<![CDATA[Enable Output - System Defined Parameter]]>\n</Description>\n</Parameter>',
    ]

def _scalar_defaults(dtype, val):
    return (f'\n<DefaultData Format="L5K">\n<![CDATA[{val}]]>\n</DefaultData>\n'
            f'<DefaultData Format="Decorated">\n'
            f'<DataValue DataType="{dtype}" Radix="Decimal" Value="{val}"/>\n</DefaultData>')

def _param(name, dtype, usage, req, vis, ext, desc=None, default=None, constant=None):
    attrs = (f'Name="{name}" TagType="Base" DataType="{dtype}" Usage="{usage}" '
             f'Radix="Decimal" Required="{req}" Visible="{vis}" ExternalAccess="{ext}"')
    if constant is not None: attrs += f' Constant="{constant}"'
    body = ""
    if desc:    body += f'\n<Description>\n<![CDATA[{desc}]]>\n</Description>'
    if default is not None: body += _scalar_defaults(dtype, default)
    if not body: return f'<Parameter {attrs}/>'
    return f'<Parameter {attrs}>{body}\n</Parameter>'

def p_bool(name, usage, req, vis, ext, desc=None, default=0):
    return _param(name,"BOOL",usage,req,vis,ext,desc,default)
def p_dint(name, usage, req, vis, ext, desc=None, default=0):
    return _param(name,"DINT",usage,req,vis,ext,desc,default)
def p_int(name, usage, req, vis, ext, desc=None, default=0):
    return _param(name,"INT",usage,req,vis,ext,desc,default)
def p_inout_bool(name, req="true", vis="true"):
    attrs = (f'Name="{name}" TagType="Base" DataType="BOOL" Usage="InOut" '
             f'Radix="Decimal" Required="{req}" Visible="{vis}" Constant="false"')
    return f'<Parameter {attrs}/>'

def inc_params():
    return [
        p_dint("CM_Inc","Input","false","true","Read/Write",
               "External channel index (0-1049).\n"
               "Only active when AUTO_INC = 0 (manual mode).", 0),
        p_bool("AUTO_INC","Input","false","true","Read/Write",
               "0 = manual mode: use CM_Inc as the channel index (default).\n"
               "1 = auto mode: AOI cycles INT_INC through 0-1049, one step per scan.\n"
               "    Read EFF_INC output to know which channel is active this scan.\n"
               "    Use EFF_INC to index your own trigger arrays if needed.", 0),
    ]

def lt_timer(pre=30000):
    return (f'<LocalTag Name="TIMER" DataType="TIMER" ExternalAccess="None">\n'
            f'<DefaultData Format="L5K">\n<![CDATA[[0,{pre},0]]]>\n</DefaultData>\n'
            f'<DefaultData Format="Decorated">\n<Structure DataType="TIMER">\n'
            f'<DataValueMember Name="PRE" DataType="DINT" Radix="Decimal" Value="{pre}"/>\n'
            f'<DataValueMember Name="ACC" DataType="DINT" Radix="Decimal" Value="0"/>\n'
            f'<DataValueMember Name="EN" DataType="BOOL" Value="0"/>\n'
            f'<DataValueMember Name="TT" DataType="BOOL" Value="0"/>\n'
            f'<DataValueMember Name="DN" DataType="BOOL" Value="0"/>\n'
            f'</Structure>\n</DefaultData>\n</LocalTag>')

def lt_scalar(name, dtype, radix="Decimal", val=0, ext="None"):
    return (f'<LocalTag Name="{name}" DataType="{dtype}" Radix="{radix}" ExternalAccess="{ext}">\n'
            f'<DefaultData Format="L5K">\n<![CDATA[{val}]]>\n</DefaultData>\n'
            f'<DefaultData Format="Decorated">\n'
            f'<DataValue DataType="{dtype}" Radix="{radix}" Value="{val}"/>\n'
            f'</DefaultData>\n</LocalTag>')

def lt_array(name, dtype, n, radix, l5k, ext="None"):
    return (f'<LocalTag Name="{name}" DataType="{dtype}" Dimensions="{n}" Radix="{radix}" ExternalAccess="{ext}">\n'
            f'<DefaultData Format="L5K">\n<![CDATA[{l5k}]]>\n</DefaultData>\n'
            f'<DefaultData Format="Decorated">\n'
            f'<Array DataType="{dtype}" Dimensions="{n}" Radix="{radix}">\n'
            f'{elems(n)}\n</Array>\n</DefaultData>\n</LocalTag>')

def inc_local_tags():
    return [
        lt_scalar("INT_INC","DINT", val=0, ext="Read/Write"),
        lt_scalar("EFF_INC","DINT", val=0, ext="Read Only"),
    ]

def inc_rungs(base):
    """Index resolution (base) and auto-increment (base+1) rungs."""
    r_sel = rung(base,
        "INDEX RESOLUTION\n"
        "  AUTO_INC = 0: EFF_INC = CM_Inc  (manual, you control the channel each scan)\n"
        "  AUTO_INC = 1: EFF_INC = INT_INC (auto-cycle, AOI steps through 0-1049)\n"
        "EFF_INC is Read Only -- read <instance>.EFF_INC from other rungs to know\n"
        "which channel is active and index your own trigger/condition arrays.",
        "[XIO(AUTO_INC)CPT(EFF_INC,CM_Inc),"
        "XIC(AUTO_INC)CPT(EFF_INC,INT_INC)];")

    r_inc = rung(base+1,
        "AUTO-INCREMENT\n"
        "When AUTO_INC = 1: advance INT_INC by 1 each scan, wrap at 1049.\n"
        "Full sweep of all 1050 channels takes 1050 scans.\n"
        "Note: if you increase the channel count, update the MOD value here to match.",
        f"XIC(AUTO_INC)CPT(INT_INC,(INT_INC + 1) MOD {N});")

    return [r_sel, r_inc]

def rung(num, comment, text):
    c = f'\n<Comment>\n<![CDATA[{comment}]]>\n</Comment>' if comment else ''
    return f'<Rung Number="{num}" Type="N">{c}\n<Text>\n<![CDATA[{text}]]>\n</Text>\n</Rung>'

def make_l5x(name, rev, desc, params, local_tags, rungs):
    p  = "\n".join(params)
    lt = "\n".join(local_tags)
    r  = "\n".join(rungs)
    return BOM + f"""\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<RSLogix5000Content SchemaRevision="1.0" SoftwareRevision="32.04" TargetName="{name}" TargetType="AddOnInstructionDefinition" TargetRevision="{rev} " ContainsContext="true" ExportDate="{EXP}" ExportOptions="References NoRawData L5KData DecoratedData Context Dependencies ForceProtectedEncoding AllProjDocTrans">
<Controller Use="Context" Name="{CTRL}">
<DataTypes Use="Context">
</DataTypes>
<AddOnInstructionDefinitions Use="Context">
<AddOnInstructionDefinition Use="Target" Name="{name}" Revision="{rev}" ExecutePrescan="false" ExecutePostscan="false" ExecuteEnableInFalse="false" CreatedDate="{NOW}" CreatedBy="{AUTH}" EditedDate="{NOW}" EditedBy="{AUTH}" SoftwareRevision="v32.04">
<Description>
<![CDATA[{desc}]]>
</Description>
<Parameters>
{p}
</Parameters>
<LocalTags>
{lt}
</LocalTags>
<Routines>
<Routine Name="Logic" Type="RLL">
<RLLContent>
{r}
</RLLContent>
</Routine>
</Routines>
</AddOnInstructionDefinition>
</AddOnInstructionDefinitions>
</Controller>
</RSLogix5000Content>"""

# ==============================================================================
# 1.  ARRAY_TIMER  Rev 1.0  (generator Rev 2.3)
#
# Rung map (14 rungs, 0-13):
#   0  - NOP header / overview
#   1  - LIMITATIONS NOP          <-- moved to rung 1 for immediate visibility
#   2  - INDEX RESOLUTION
#   3  - AUTO-INCREMENT
#   4  - PRESET SYNC
#   5  - FREE-RUNNING TIMER
#   6  - T_DN OUTPUT
#   7  - T_ACC OUTPUT
#   8  - FAULT CHECK
#   9  - LANDING POINT CALC
#  10  - RESET ON DISABLE
#  11  - CYCLE COUNTDOWN
#  12  - DONE FLAG
#  13  - OUTPUT
# ==============================================================================

def gen_array_timer():
    params = sys_params() + inc_params() + [
        p_dint("PRE_IN","Input","true","true","Read/Write",
               "Timer period in milliseconds (must be > 0). Default: 30000 ms.\n"
               "Shared by all channels. Do not change while any Cond_EN is true.", 30000),
        p_bool("Cond_EN","Input","true","true","Read/Write",
               "Enable condition. Rising edge starts the delay for this channel.\n"
               "Falling edge resets all state for this channel.", 0),
        p_dint("Delay_PRE","Input","true","true","Read/Write",
               "Desired delay in milliseconds (>= 0).\n"
               "Delay_PRE = 0 fires within one timer period, not the same scan.", 0),
        p_bool("T_DN","Output","false","true","Read Only",
               "One-scan pulse each time the timer period completes.", 0),
        # T_TT removed -- redundant mirror of internal TIMER.TT.
        # Change TIMER local tag ExternalAccess to "Read Only" if HMI access is needed.
        p_dint("T_ACC","Output","false","true","Read Only",
               "Current timer accumulator in milliseconds.\n"
               "Useful for HMI display or ladder logic that needs the live timer value.", 0),
        p_bool("Delay_DN","Output","false","true","Read Only",
               "True when the delay has elapsed. Held true until Cond_EN goes false.", 0),
        p_bool("CM_Fault","Output","false","true","Read Only",
               "True when EFF_INC is out of range (0-1049) or PRE_IN <= 0.\n"
               "Delay logic suspended. Timer still runs.", 0),
    ]

    local_tags = inc_local_tags() + [
        lt_timer(30000),
        lt_array("LANDING_PT","DINT",N,"Decimal",sz(N)),
        lt_array("COUNT",     "DINT",N,"Decimal",sz(N)),
        lt_array("FOUND",     "BOOL",N,"Decimal",bz(N)),
        lt_array("DN_FLAG",   "BOOL",N,"Decimal",bz(N)),
    ]

    lim_rung = rung(1,
        "LIMITATIONS AND HOW TO INCREASE THEM\n"
        "\n"
        "--- CHANNEL COUNT (current: 1050, index 0-1049) ---\n"
        "To increase:\n"
        "  1. Increase Dimensions on all four arrays to the same new size:\n"
        "       LANDING_PT, COUNT, FOUND, DN_FLAG\n"
        "  2. In Rung 8 change CMP(EFF_INC > 1049) to CMP(EFF_INC > <size-1>).\n"
        "  3. In Rung 3 change MOD 1050 to MOD <new size>.\n"
        "\n"
        "--- TIMER PERIOD (PRE_IN, DINT, max ~24.8 days) ---\n"
        "No practical increase needed.\n"
        "For finer resolution reduce the controller task period.\n"
        "\n"
        "--- DELAY RANGE (Delay_PRE, DINT) ---\n"
        "Max = PRE_IN * 2,147,483,647 ms. No increase needed.\n"
        "\n"
        "--- AUTO MODE SWEEP TIME ---\n"
        "In AUTO_INC=1 mode, each channel is visited once every 1050 scans.\n"
        "At a 10ms task, full sweep = ~10.5 seconds.\n"
        "Reduce channel count or task period to increase sweep frequency.\n"
        "\n"
        "--- SCAN TIME ---\n"
        "Each call is O(1). Add one call per active channel per scan.",
        "NOP();")

    rungs = [
        rung(0,
             "ARRAY_TIMER  REV 1.0\n\n"
             "Self-contained multi-channel software delay.\n"
             "An internal free-running TON drives all delay channels.\n\n"
             "INDEX MODES (Rungs 2-3):\n"
             "  AUTO_INC = 0 (default): use CM_Inc -- you control the channel each scan\n"
             "  AUTO_INC = 1          : AOI cycles INT_INC 0->1049->0 each scan\n"
             "    Read <instance>.EFF_INC to know the active channel this scan.\n\n"
             "TIMER SECTION (Rungs 4-7): internal TON, period = PRE_IN ms.\n"
             "  T_DN: one-scan pulse per period.  T_ACC: live accumulator (ms).\n\n"
             "DELAY SECTION (Rungs 8-13):\n"
             "  On Cond_EN rising edge:\n"
             "    LANDING_PT = (T_ACC + Delay_PRE) MOD PRE_IN\n"
             "    COUNT      = floor((T_ACC + Delay_PRE) / PRE_IN)\n"
             "  COUNT decrements once per T_DN pulse.\n"
             "  Delay_DN fires when COUNT = 0 AND T_ACC >= LANDING_PT.\n\n"
             "NOTE: Change CM_Inc/INT_INC only while Cond_EN = 0.\n"
             "      PRE_IN must be > 0 and should not change mid-delay.",
             "NOP();"),
        lim_rung,
    ] + inc_rungs(2) + [

        # ── TIMER SECTION (rungs 4-7) ─────────────────────────────────────────
        rung(4,
             "PRESET SYNC\n"
             "Mirror PRE_IN into TIMER.PRE each scan.",
             "CMP(TIMER.PRE <> PRE_IN)CPT(TIMER.PRE,PRE_IN);"),
        rung(5,
             "FREE-RUNNING TIMER\n"
             "XIO(TIMER.DN) resets the TON one scan after DN fires,\n"
             "creating a continuous cycle at the PRE_IN period.",
             "CMP(TIMER.PRE = PRE_IN)XIO(TIMER.DN)TON(TIMER,?,?);"),
        rung(6,
             "T_DN OUTPUT\n"
             "One-scan pulse per period. Auto-clears next scan when timer resets.",
             "XIC(TIMER.DN)OTE(T_DN);"),
        rung(7,
             "T_ACC OUTPUT\n"
             "Mirror live timer accumulator to output parameter T_ACC.\n"
             "Use for HMI display or ladder comparisons against the current timer value.",
             "CPT(T_ACC,TIMER.ACC);"),

        # ── DELAY SECTION (rungs 8-13) ────────────────────────────────────────
        rung(8,
             "FAULT CHECK\n"
             "Suspend delay logic if EFF_INC is out of range or PRE_IN is zero.\n"
             "Timer section (Rungs 4-7) runs regardless.",
             "[CMP(EFF_INC < 0),CMP(EFF_INC > 1049),CMP(PRE_IN <= 0)]OTE(CM_Fault);"),
        rung(9,
             "LANDING POINT CALCULATION  (one-shot on Cond_EN rising edge)\n"
             "XIO(FOUND) prevents recalculation once latched.\n"
             "LANDING_PT = (T_ACC + Delay_PRE) MOD PRE_IN\n"
             "COUNT      = floor((T_ACC + Delay_PRE) / PRE_IN)\n"
             "CPT uses 64-bit intermediates for DINT -- no overflow risk.",
             "XIO(CM_Fault)XIC(Cond_EN)XIO(FOUND[EFF_INC])"
             "CPT(LANDING_PT[EFF_INC],(T_ACC + Delay_PRE) MOD PRE_IN)"
             "CPT(COUNT[EFF_INC],((T_ACC + Delay_PRE) - ((T_ACC + Delay_PRE) MOD PRE_IN)) / PRE_IN)"
             "OTL(FOUND[EFF_INC]);"),
        rung(10,
             "RESET ON DISABLE\n"
             "Clear all channel state when Cond_EN goes false.",
             "XIO(CM_Fault)XIO(Cond_EN)"
             "CPT(LANDING_PT[EFF_INC],0)"
             "CPT(COUNT[EFF_INC],0)"
             "OTU(FOUND[EFF_INC])"
             "OTU(DN_FLAG[EFF_INC]);"),
        rung(11,
             "CYCLE COUNTDOWN\n"
             "Decrement COUNT once per timer period (T_DN pulse).\n"
             "Stops at 0 -- no underflow.",
             "XIO(CM_Fault)XIC(FOUND[EFF_INC])CMP(COUNT[EFF_INC] > 0)XIC(T_DN)"
             "CPT(COUNT[EFF_INC],COUNT[EFF_INC] - 1);"),
        rung(12,
             "DONE FLAG\n"
             "Fire when COUNT = 0 AND T_ACC has reached the landing point.\n"
             "XIO(T_DN) blocks on the scan COUNT rolls to 0 (T_ACC = PRE_IN then).\n"
             "XIC(DN_FLAG) latch holds until Cond_EN drops.",
             "XIO(CM_Fault)XIC(FOUND[EFF_INC])XIO(T_DN)"
             "[CMP(COUNT[EFF_INC] = 0)CMP(T_ACC >= LANDING_PT[EFF_INC]),"
             "XIC(DN_FLAG[EFF_INC])]OTE(DN_FLAG[EFF_INC]);"),
        rung(13, "OUTPUT",
             "XIC(DN_FLAG[EFF_INC])OTE(Delay_DN);"),
    ]

    desc = ('Array-based multi-channel programmable delay. Up to 1050 independent channels\n'
            'driven by a single internal free-running TON.\n'
            'Outputs: T_DN (period pulse), T_ACC (live ms), Delay_DN.')
    return make_l5x("ARRAY_TIMER", REV, desc, params, local_tags, rungs)

# ==============================================================================
# 2.  ARRAY_CTUD  Rev 1.0  (generator Rev 2.3)
#
# Rung map (11 rungs, 0-10):
#   0  - NOP header / overview
#   1  - LIMITATIONS NOP          <-- moved to rung 1 for immediate visibility
#   2  - INDEX RESOLUTION
#   3  - AUTO-INCREMENT
#   4  - FAULT CHECK
#   5  - PRESET SYNC
#   6  - RESET
#   7  - COUNT UP  (edge-triggered, OTE C_CU)
#   8  - COUNT DOWN (edge-triggered, OTE C_CD)
#   9  - DONE (C_DN)
#  10  - ACCUMULATOR OUTPUT (C_ACC)
# ==============================================================================

def gen_array_ctud():
    params = sys_params() + inc_params() + [
        p_int("PRE","Input","true","true","Read/Write",
              "Count preset (INT, max 32767). C_DN fires when ACC = PRE.", 0),
        p_bool("CTU","Input","true","true","Read/Write",
               "Count Up trigger. Edge-triggered: one increment per rising edge.\n"
               "Blocked when ACC >= PRE.", 0),
        p_bool("CTD","Input","true","true","Read/Write",
               "Count Down trigger. Edge-triggered: one decrement per rising edge.\n"
               "Blocked when ACC = 0.", 0),
        p_bool("DN_0","Input","false","true","Read/Write",
               "When true, C_DN also fires when ACC = 0 (count-down done).", 0),
        p_inout_bool("RES","true","true"),
        p_int("RESET_TO","Input","false","true","Read/Write",
              "Value to reset the accumulator to when RES fires. Default: 0.", 0),
        p_bool("C_DN","Output","false","true","Read Only",
               "Done: true when ACC = PRE, or ACC = 0 with DN_0 set.", 0),
        p_bool("C_CU","Output","false","true","Read Only",
               "Count-Up pulse: one scan wide per rising edge of CTU.\n"
               "Useful for diagnostics and one-shot downstream logic.", 0),
        p_bool("C_CD","Output","false","true","Read Only",
               "Count-Down pulse: one scan wide per rising edge of CTD.\n"
               "Useful for diagnostics and one-shot downstream logic.", 0),
        p_int("C_ACC","Output","false","true","Read Only",
              "Accumulator value for the currently active channel (EFF_INC).", 0),
        p_bool("CM_Fault","Output","false","true","Read Only",
               "True when EFF_INC is out of range (0-1049). All logic suspended.", 0),
    ]

    local_tags = inc_local_tags() + [
        lt_scalar("COUNT_PRE","INT"),
        lt_array("COUNT_ACC","INT", N,"Decimal",sz(N)),
        lt_array("CTU_ONS",  "BOOL",N,"Decimal",bz(N)),
        lt_array("CTD_ONS",  "BOOL",N,"Decimal",bz(N)),
    ]

    lim_rung = rung(1,
        "LIMITATIONS AND HOW TO INCREASE THEM\n"
        "\n"
        "--- CHANNEL COUNT (current: 1050, index 0-1049) ---\n"
        "To increase:\n"
        "  1. Increase Dimensions on all three arrays to the same new size:\n"
        "       COUNT_ACC, CTU_ONS, CTD_ONS\n"
        "  2. In Rung 4 change CMP(EFF_INC > 1049) to CMP(EFF_INC > <size-1>).\n"
        "  3. In Rung 3 change MOD 1050 to MOD <new size>.\n"
        "\n"
        "--- ACCUMULATOR / PRESET RANGE (current: INT, 0-32767) ---\n"
        "To increase to DINT (0-2,147,483,647):\n"
        "  Change PRE, RESET_TO, C_ACC params and COUNT_PRE, COUNT_ACC\n"
        "  local tags from INT to DINT. Memory: 2 bytes/ch -> 4 bytes/ch.\n"
        "\n"
        "--- AUTO MODE SWEEP TIME ---\n"
        "In AUTO_INC=1 mode each channel is visited once every 1050 scans.\n"
        "At a 10ms task, full sweep = ~10.5 seconds.\n"
        "\n"
        "--- MEMORY vs STANDARD COUNTER TAGS ---\n"
        "Standard COUNTER: 12 bytes each. 1050 tags = 12,600 bytes.\n"
        "This AOI at 1050 channels (INT): ~3,400 bytes. ~9x smaller.\n"
        "\n"
        "--- SCAN TIME ---\n"
        "Each call is O(1). Add one call per active channel per scan.",
        "NOP();")

    rungs = [
        rung(0,
             "ARRAY_CTUD  REV 1.0\n\n"
             "Array-based multi-channel up/down counter.\n"
             "INT accumulator (0-32767). Up to 1050 independent channels.\n\n"
             "INDEX MODES (Rungs 2-3):\n"
             "  AUTO_INC = 0 (default): use CM_Inc -- you control the channel each scan\n"
             "  AUTO_INC = 1          : AOI cycles INT_INC 0->1049->0 each scan\n"
             "    Read <instance>.EFF_INC to know the active channel this scan.\n"
             "    Example: XIC(CTU_ARRAY[MY_CTR.EFF_INC]) -> CTU input\n\n"
             "CTU and CTD are EDGE-TRIGGERED (rising edge only).\n"
             "One count per edge regardless of how long the bit is held.\n\n"
             "C_CU / C_CD are one-scan-wide output pulses matching each count event.\n"
             "Use them for diagnostics or to trigger downstream one-shot logic.\n\n"
             "SIDE EFFECT: AOI clears the caller's RES bit after executing reset.\n"
             "RESET_TO sets the reset value (default 0).\n\n"
             "NOTE: Change CM_Inc/INT_INC only while CTU = 0 and CTD = 0.",
             "NOP();"),
        lim_rung,
    ] + inc_rungs(2) + [

        rung(4,
             "FAULT CHECK\n"
             "Suspend all indexed logic if EFF_INC is out of range.",
             "[CMP(EFF_INC < 0),CMP(EFF_INC > 1049)]OTE(CM_Fault);"),

        rung(5,
             "PRESET SYNC\n"
             "Mirror scalar PRE into COUNT_PRE each scan.",
             "CMP(COUNT_PRE <> PRE)CPT(COUNT_PRE,PRE);"),

        rung(6,
             "RESET\n"
             "On RES rising edge: reset ACC to RESET_TO, clear RES via OTU.",
             "XIO(CM_Fault)XIC(RES)"
             "CPT(COUNT_ACC[EFF_INC],RESET_TO)"
             "OTU(RES);"),

        rung(7,
             "COUNT UP  (edge-triggered)\n"
             "ONS ensures exactly one increment per CTU rising edge.\n"
             "Blocked when ACC >= COUNT_PRE.\n"
             "C_CU fires one scan wide -- use for diagnostics or downstream one-shots.",
             "XIO(CM_Fault)CMP(COUNT_ACC[EFF_INC] < COUNT_PRE)"
             "XIC(CTU)ONS(CTU_ONS[EFF_INC])"
             "CPT(COUNT_ACC[EFF_INC],COUNT_ACC[EFF_INC] + 1)OTE(C_CU);"),

        rung(8,
             "COUNT DOWN  (edge-triggered)\n"
             "ONS ensures exactly one decrement per CTD rising edge.\n"
             "Blocked when ACC = 0.\n"
             "C_CD fires one scan wide -- use for diagnostics or downstream one-shots.",
             "XIO(CM_Fault)CMP(COUNT_ACC[EFF_INC] > 0)"
             "XIC(CTD)ONS(CTD_ONS[EFF_INC])"
             "CPT(COUNT_ACC[EFF_INC],COUNT_ACC[EFF_INC] - 1)OTE(C_CD);"),

        rung(9,
             "DONE\n"
             "C_DN fires when ACC = COUNT_PRE, or ACC = 0 with DN_0 set.",
             "XIO(CM_Fault)"
             "[CMP(COUNT_ACC[EFF_INC] = COUNT_PRE),"
             "CMP(COUNT_ACC[EFF_INC] = 0)XIC(DN_0)]OTE(C_DN);"),

        rung(10,
             "ACCUMULATOR OUTPUT\n"
             "Mirror the active channel accumulator to scalar C_ACC.",
             "XIO(CM_Fault)CPT(C_ACC,COUNT_ACC[EFF_INC]);"),
    ]

    desc = ('Array-based multi-channel up/down counter. INT ACC/PRE (0-32767).\n'
            'Up to 1050 independent channels. Manual or auto-cycling index.\n'
            'Outputs: C_DN, C_CU (up pulse), C_CD (down pulse), C_ACC.')
    return make_l5x("ARRAY_CTUD", REV, desc, params, local_tags, rungs)

# ── write files ────────────────────────────────────────────────────────────────

files = {
    "ARRAY_TIMER.L5X": gen_array_timer(),
    "ARRAY_CTUD.L5X":  gen_array_ctud(),
}

for fname, content in files.items():
    path = os.path.join(OUTPUT_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    size_kb = os.path.getsize(path) // 1024
    non_ascii = [(i, ch) for i, ch in enumerate(content) if ord(ch) > 127 and ch != '\ufeff']
    print(f"  wrote {fname}  ({size_kb} KB)  non-ASCII: {len(non_ascii)}")

print("Done.")
