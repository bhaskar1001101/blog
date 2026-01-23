---
title: deeper into memory
date: 2026-01-23
type: rant
---


## Part 1: The Physics of Memory

### Why DRAM is DRAM

Every DRAM cell is fundamentally a capacitor and a transistor. That's it. The capacitor stores charge (1 or 0), the transistor gates access to it.

```text
        Word Line (row select)
            │
            ▼
        ┌───┴───┐
        │       │
Bit ────┤  FET  ├──── Capacitor ──── Ground
Line    │       │
        └───────┘     (stores bit)
```

The problem: capacitors leak. The charge drains away in milliseconds. So DRAM must be **refreshed**—every cell read, amplified, and rewritten—thousands of times per second. This refresh cycle:
- Consumes power (30-40% of DRAM power is refresh)
- Blocks access during refresh windows
- Gets worse as capacitors shrink (smaller = leakier)

The capacitor also limits density. You need physical space for that capacitor, and it needs to hold enough charge to be reliably sensed. This is why DRAM density scaling has slowed dramatically—we're hitting fundamental physics limits on how small you can make a capacitor that still works.

**Key insight**: DRAM is fast because capacitors charge/discharge quickly. But the capacitor is also the limiting factor for density and power.

### Why NAND is NAND

NAND flash uses a completely different approach: **floating-gate transistors**.

```text
        Control Gate
            │
      ══════╪══════  ← Oxide (insulator)
      ┌─────┴─────┐
      │  Floating │  ← Trapped electrons = data
      │   Gate    │
      └─────┬─────┘
      ══════╪══════  ← Tunnel oxide
            │
    Source ─┴─ Drain
```

To write: You apply a high voltage that forces electrons through the tunnel oxide into the floating gate. They get trapped there.

To read: You apply a lower voltage to the control gate. If electrons are trapped (bit = 0), the transistor's threshold voltage shifts and it won't conduct at the read voltage. If no electrons (bit = 1), it conducts normally.

To erase: You apply reverse high voltage, pulling electrons back out.

**Critical differences from DRAM**:

1. **No refresh needed**: Electrons stay trapped for years without power. This is why SSDs retain data when unplugged.

2. **Higher density**: No capacitor needed. You can stack cells vertically (3D NAND) because each cell is just a transistor with a modified gate structure.

3. **Slower writes**: Forcing electrons through oxide takes time (~100μs vs ~10ns for DRAM). The high voltage also damages the oxide slightly each time.

4. **Write endurance**: Each write cycle degrades the tunnel oxide. After 1,000-100,000 cycles (depending on cell type), the oxide can't reliably trap electrons anymore.

5. **Asymmetric performance**: Reads are much faster than writes, and erases are the slowest (must erase whole blocks).

### The Density Equation

Here's why NAND wins on density:

**DRAM cell size**: ~0.001-0.002 μm² per bit (at cutting-edge nodes)
- Limited by capacitor minimum size
- Planar structure (mostly 2D, with some trench/stack capacitor tricks)

**NAND cell size**: ~0.0001-0.0003 μm² per bit (effective, with 3D stacking)
- No capacitor
- Can stack 200+ layers vertically
- Multi-bit cells (TLC = 3 bits, QLC = 4 bits per cell)

This is why a single NAND die can hold 2TB while a DRAM die holds ~24GB. It's not incremental—it's an order of magnitude difference in density.

---

## Part 2: The Bandwidth Problem

### Why Memory Bandwidth Matters

Bandwidth = (data width) × (frequency) × (transfers per cycle)

Traditional DDR5:
- 64-bit data width (per channel)
- ~3200 MHz base clock
- 2 transfers per cycle (Double Data Rate)
- = ~51 GB/s per channel

A typical server has 8 channels = ~410 GB/s total memory bandwidth.

An H100 GPU has 80 billion transistors that want to do math. At peak throughput, those tensor cores can perform 1,979 TFLOPS of FP8 operations. If each operation needs even one byte of data, you'd need ~2000 TB/s of bandwidth. Obviously impossible—so GPUs rely on data reuse (the same weights get used across a batch), but even with reuse, memory bandwidth is the bottleneck.

### The Packaging Insight

Traditional memory architecture:

```text
┌─────────────┐          ┌─────────────┐
│     CPU     │◄────────►│    DRAM     │
│             │  DDR Bus │   (DIMM)    │
└─────────────┘  ~few cm └─────────────┘
```

That DDR bus is several centimeters of PCB traces. Each trace has:
- Capacitance (slows signal transitions)
- Inductance (causes reflections)
- Crosstalk with neighboring traces
- Power consumption proportional to (capacitance × voltage² × frequency)

Longer traces = more capacitance = more power = lower max frequency = less bandwidth.

**HBM's insight**: What if we put memory **on the same package** as the processor, connected by microbumps instead of PCB traces?

```text
┌───────────────────────────────────────┐
│           Silicon Interposer          │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  │
│  │HBM  │  │HBM  │  │HBM  │  │ GPU │  │
│  │Stack│  │Stack│  │Stack│  │     │  │
│  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘  │
│     │        │        │        │      │
│  ═══╪════════╪════════╪════════╪═══  │ ← Metal layers in interposer
└─────┼────────┼────────┼────────┼─────┘
      │        │        │        │
   Microbumps (25-55 μm pitch)
```

Connection length goes from centimeters to millimeters. This enables:
- Much wider buses (1024+ bits vs 64 bits)
- Lower voltage swings (less power per bit)
- Higher frequencies (shorter traces = less capacitance)

---

## Part 3: HBM Architecture Deep Dive

### The Stack

An HBM stack consists of:

1. **Base logic die**: Memory controllers, PHY (physical interface), I/O circuits, ECC, power management
2. **DRAM dies**: 4, 8, 12, or 16 layers of actual memory
3. **TSVs**: Vertical connections through each die
4. **Microbumps**: Connections between die layers (~40μm pitch for current HBM)

```text
        ┌─────────────────┐
        │   DRAM Die 15   │  ← Top die (optional heat spreader above)
        ├─────────────────┤
        │   DRAM Die 14   │
        ├─────────────────┤
        │       ...       │
        ├─────────────────┤
        │   DRAM Die 1    │
        ├─────────────────┤
        │   DRAM Die 0    │
        ├═════════════════┤
        │  Base Logic Die │  ← Memory controller, PHY, test logic
        └────────┬────────┘
                 │
           Microbumps to interposer
```

### Through-Silicon Vias (TSVs)

TSVs are vertical holes etched through silicon, filled with copper (or tungsten), that carry signals between stacked dies.

Manufacturing process:
1. **Via etch**: Deep reactive ion etching (DRIE) creates holes ~5-10μm diameter, ~50-100μm deep
2. **Liner deposition**: Insulating oxide layer, then barrier metal (Ta/TaN)
3. **Copper fill**: Electroplating fills the via with copper
4. **CMP**: Chemical-mechanical polishing to planarize
5. **Backside reveal**: Thin the wafer from the back until TSVs are exposed
6. **Bonding**: Stack dies and connect TSVs with microbumps

Each HBM die has thousands of TSVs. The TSV pitch (spacing) limits how many signals you can route vertically. Current HBM uses ~40-55μm TSV pitch.

**Yield impact**: Every TSV is a potential failure point. A 12-high stack with 2000 TSVs per die means 24,000 potential defect sites. This is why HBM yields are lower than planar DRAM—one bad TSV can kill the whole stack.

### The Channel Architecture

HBM3E has 16 independent channels per stack:
- Each channel is 64 bits wide
- Each channel has independent command/address
- 16 × 64 = 1024-bit total interface width

HBM4 doubles this to 32 channels (2048-bit interface) by splitting each pseudo-channel into two independent channels.

Why independent channels matter: Memory controllers can issue commands to different channels simultaneously. With 16 channels, you can have 16 different memory operations in flight. This parallelism is what enables the crazy bandwidth numbers.

### The Base Logic Die (HBM4's Big Change)

Previous HBM generations used a relatively simple base die manufactured in older process nodes (~20-28nm). It handled:
- Memory PHY (serialization/deserialization)
- Refresh logic
- Built-in self-test (BIST)
- Some error correction

HBM4 changes this. The base die can now be manufactured at advanced logic nodes (potentially 5nm or below) by TSMC or Samsung Foundry. This enables:

1. **Custom functionality**: GPU vendors can add application-specific logic to the memory base die
2. **Compute-near-memory**: Simple operations (address calculation, scatter-gather) can happen in the base die
3. **Advanced ECC**: More sophisticated error correction without bandwidth overhead
4. **Security features**: Encryption, access control at the memory interface

This is the beginning of **processing-in-memory**—the boundary between "memory" and "compute" is blurring.

### Thermal Challenges

Power density in HBM is intense. Let's do the math:

- HBM3E stack: ~20-25W typical
- Stack footprint: ~7mm × 11mm = 77mm²
- Power density: ~260-325 W/cm²

For comparison, a CPU is typically 50-100 W/cm². HBM is 3-5x denser.

And it's sitting next to a GPU that might be 700W in a 800mm² die (~87 W/cm²). The combined system has severe thermal management challenges.

Current solutions:
- High-performance thermal interface materials (TIMs)
- Vapor chambers in the heatsink
- Direct liquid cooling to cold plates
- Careful airflow/coolant channel design

The 775μm stack height limit that JEDEC specified for HBM4 16-Hi is partly thermal—taller stacks trap more heat in the center.

---

## Part 4: HBF Architecture Deep Dive

### From 3D NAND to HBF

3D NAND already stacks memory cells vertically, but within a single die:

```text
3D NAND Die Cross-Section:

    ┌─ String of cells (vertical) ─┐
    │                               │
    ▼                               ▼
   ═══  Word Line 320 (control gate)
    │
   ═══  Word Line 319
    │
   ...  (hundreds of layers)
    │
   ═══  Word Line 1
    │
   ═══  Word Line 0
    │
   ─┴─  Bit Line Contact
```

A single SK hynix 321-layer die achieves 2TB with QLC (4 bits per cell):
- 321 word line layers
- Dense cell pitch in X/Y
- QLC encoding

HBF then stacks multiple 3D NAND dies (each already ~300 layers internally) into an HBM-like package:

```text
HBF Stack:

┌─────────────────┐
│ 3D NAND Die 15  │  ← Each die is ~300 internal layers
├─────────────────┤
│ 3D NAND Die 14  │
├─────────────────┤
│      ...        │
├─────────────────┤
│ 3D NAND Die 0   │
├═════════════════┤
│ Base Logic Die  │  ← NAND controller, ECC, wear leveling
└────────┬────────┘
         │
     To interposer
```

Total layers if using 321-layer NAND in 16-Hi stack: **5,136 effective layers**

That's where the density comes from. Each NAND die is already a skyscraper; HBF stacks skyscrapers.

### Sandisk's CBA Technology

CBA = CMOS directly Bonded to Array

Traditional 3D NAND has peripheral logic (decoders, sense amplifiers, I/O) on the same die as the memory array. This "peripheral under cell" or "peripheral beside cell" approach wastes area.

CBA bonds two separate wafers:
1. **Array wafer**: Pure memory cells, optimized for density
2. **CMOS wafer**: Control logic, optimized for speed/power

They're manufactured separately (different process optimizations), then bonded face-to-face with hybrid bonding. This allows:
- Higher memory density (no peripheral logic taking space)
- Faster logic (advanced CMOS node)
- Better yield (smaller dies, independent optimization)

For HBF specifically, CBA enables putting sophisticated controllers directly under the memory array, minimizing the distance signals travel.

### The Bandwidth Challenge

NAND is intrinsically slower than DRAM for random access. A typical SSD achieves ~7 GB/s via NVMe PCIe 4.0. How does HBF reach 1.6 TB/s?

**Parallelism**:
- Traditional SSD: 4-8 NAND channels
- HBF: 32+ channels (matching HBM4 architecture)
- Each channel is 64 bits wide
- Aggregate: 32 × 64 = 2048 bits per access

**Shorter path**:
- SSD goes through: NAND → Controller → PCIe → CPU
- HBF goes through: NAND → Base die → Interposer → GPU
- Latency reduction from microseconds to hundreds of nanoseconds

**Optimized access patterns**:
- Large sequential reads (model weight loading)
- Read bandwidth prioritized over write
- Interleaving across many independent dies

The 2.2% performance gap vs HBM on inference comes from:
- Model weights are read once, reused many times (amortizes slower NAND access)
- Large batch sizes hide latency
- Inference is fundamentally read-heavy

### Write Endurance Reality

100,000 P/E (program/erase) cycles sounds limiting, but let's do the math:

Assume 512GB HBF stack, 100,000 cycle endurance:
- Total bytes writable: 512GB × 100,000 = 51.2 PB (petabytes)

For inference workloads:
- Model weights: written once at deployment, read billions of times
- KV cache: This is the tricky part—writes happen during inference

If KV cache is 10GB and you write it fully for each inference:
- 51.2 PB ÷ 10 GB = 5.12 billion inferences before wear-out
- At 100 inferences/second: ~1,624 years

Even pessimistic assumptions give multi-year lifetime for inference workloads.

For **training**: Writes happen on every backward pass. A 405B parameter model updated with FP16 gradients:
- ~810 GB of writes per training step
- 51.2 PB ÷ 810 GB = ~63,000 training steps before wear-out
- Real training runs do millions of steps

This is why HBF is not for training.

---

## Part 5: Manufacturing and Economics

### The Interposer Problem

Both HBM and HBF require silicon interposers (or equivalent). The interposer is a passive silicon die that provides:
- Dense metal interconnects between chips
- Microbump landing pads
- Power/ground distribution
- Sometimes embedded passives (capacitors, inductors)

Interposers are big and expensive:
- An H100's interposer is ~2,500 mm² (larger than any single chip on it)
- Made on older process nodes (65nm) but requires many metal layers
- Uses expensive lithography for fine-pitch routing (~1μm line/space)

**TSMC's CoWoS** (Chip-on-Wafer-on-Substrate):
- Industry standard for HBM + GPU integration
- Capacity-constrained through 2026
- ~$5,000-10,000 per interposer (estimated)

**Intel's EMIB** (Embedded Multi-die Interconnect Bridge):
- Smaller bridge dies embedded in organic substrate
- Lower cost but also lower interconnect density
- Used in Ponte Vecchio and Gaudi

The interposer shortage is real. TSMC announced a new fab specifically for CoWoS capacity, but it won't be fully online until 2027.

### The HBM Cost Structure

Approximate cost breakdown for HBM3E 24GB stack:
- DRAM wafer: ~$3,000-4,000 (for the dies that go into one stack)
- TSV processing: ~$500-1,000
- Stacking/bonding: ~$300-500
- Test: ~$200-400
- Yield loss: ~$500-1,000

Total: ~$4,500-7,000 per stack (at volume)

For comparison, 24GB of commodity DDR5 costs ~$60-80 retail. HBM is 50-100x more expensive per gigabyte.

### Why This Won't Change Soon

The cost premium comes from:
1. **Process complexity**: TSVs, wafer thinning, precision bonding
2. **Yield**: Multi-die stacks multiply defect probability
3. **Test**: Must test at multiple stages (known-good-die strategy)
4. **Equipment**: Specialized tools for bonding, not general-purpose

These are fundamental to 3D stacking, not manufacturing inefficiency. Costs will decrease with volume and learning, but HBM will always be significantly more expensive than planar DRAM.

HBF will likely be cheaper per GB than HBM because:
- NAND is inherently denser (less wafer area per bit)
- NAND manufacturing is more mature than HBM stacking
- Lower precision requirements (NAND is more tolerant of variation)

Sandisk's claim of "similar cost per stack" with 8x capacity implies ~8x better cost per GB.

---

## Part 6: System-Level Implications

### Memory Hierarchy 2.0

The traditional hierarchy:
```text
Registers (B) → L1 (KB) → L2 (MB) → L3 (MB) → DRAM (GB) → SSD (TB)
  ~1 cycle      ~4 cyc    ~12 cyc   ~40 cyc   ~100 cyc    ~10,000 cyc
```

With HBM + HBF on-package:
```text
Registers → L1 → L2 → HBM → HBF
  ~1 cyc   ~4   ~12   ~50   ~200-500 cyc (estimated)
```

The gap between HBM and HBF is much smaller than DRAM to SSD. This enables software to treat them more uniformly—no need for explicit "load from storage" steps.

### Implications for Model Architecture

Current LLM architectures are constrained by HBM capacity:
- Context length limited by KV cache memory
- Model size limited by weight storage
- Batch size limited by activation memory

With HBF providing 8-16x capacity:
- Context lengths of 1M+ tokens become feasible
- 1T+ parameter models fit on single nodes
- New architectures optimized for read-heavy access patterns

Mixture of Experts (MoE) is particularly interesting. In MoE, most experts are dormant on any given forward pass. Perfect for HBF:
- Dormant expert weights sit in HBF (cold storage)
- Active experts cached in HBM (hot storage)
- Router decides which experts to activate, triggers HBF→HBM prefetch

### Implications for Edge AI

Current edge AI constraints:
- Smartphone: ~8-12GB shared DRAM, ~100 GB/s bandwidth
- Laptop: ~16-64GB DRAM, ~100-200 GB/s bandwidth
- Limited to ~7B parameter models realistically

With HBF:
- 512GB-1TB capacity in similar power envelope
- >1 TB/s bandwidth to local compute
- 70B-400B parameter models on edge devices

This changes what "edge" means. A phone with HBF could run models currently requiring datacenter hardware.

### Implications for Ethereum

You mentioned Nimbus and the architecture sketch. Let me get specific:

**Current Ethereum full node bottleneck**: The Merkle Patricia Trie stores all account state. Every state access requires:
1. Hash the key to get path
2. Traverse trie nodes (typically 6-8 levels)
3. Each level requires loading a node from storage
4. Hash each node to verify integrity

On NVMe SSD: ~50-100 μs per state access (with caching)
On HBM: ~100-200 ns per state access
On HBF: ~500-1000 ns per state access (estimated)

That's a 50-100x improvement over SSD for HBF, 250-500x for HBM.

With the hybrid architecture:
- Hot state (recently accessed accounts, active contracts) in HBM
- Full state in HBF
- Trie traversal happens at memory speed, not storage speed

This could enable:
- Full archive nodes on consumer hardware
- Real-time state analysis
- Much faster sync times
- New client architectures (your EL/CL split)

---

## Part 7: The Manufacturing Roadmap

### HBM Evolution

**HBM3E (Current, 2024-2025)**:
- 8-12 Hi stacks
- 24-36 GB per stack
- 1.2-1.6 TB/s per stack
- 1024-bit interface

**HBM4 (2025-2026)**:
- 12-16 Hi stacks
- 36-48 GB per stack
- 2-3 TB/s per stack
- 2048-bit interface
- Custom base logic die

**HBM4E (2027-2028)**:
- 16-24 Hi stacks (hybrid bonding enables thinner layers)
- 64-96 GB per stack
- 4+ TB/s per stack
- Further logic integration

**HBM5 (2029+)**:
- Possibly moving to hybrid bonding throughout (not just base die)
- Compute-in-memory features in DRAM layers themselves
- Integration with photonic interconnects?

### HBF Evolution

**Gen 1 (2026-2027)**:
- 16-Hi stack
- 512 GB per stack
- 1.6 TB/s read bandwidth
- HBM4 form factor compatible

**Gen 2 (2027-2028)**:
- Improved NAND (400+ layers)
- 1 TB per stack
- 2+ TB/s read bandwidth
- Better write endurance (advanced wear leveling)

**Gen 3 (2029+)**:
- PLC (5-bit) NAND possible
- 1.5-2 TB per stack
- 3.2+ TB/s read bandwidth
- Compute-in-storage features

### The Hybrid Bonding Transition

Current stacking uses microbumps (~40μm pitch). Hybrid bonding eliminates bumps entirely—copper pads bond directly to copper pads through thermocompression.

Advantages:
- Much finer pitch (~1-10μm vs 40μm)
- More connections per area (>10x density)
- Better thermal transfer (metal-to-metal)
- More robust mechanically

Challenges:
- Extreme surface flatness required (<1nm variation)
- Contamination sensitivity (single particle can cause void)
- Alignment precision (~100nm)
- New equipment and processes needed

Samsung is developing 3D DRAM using hybrid bonding—stacking DRAM cells vertically like NAND, but with DRAM cells. This could eventually provide DRAM-like performance with NAND-like density.

---

## Part 8: What To Build

Given all this, here's what I'd focus on if I were designing systems today:

### Near-Term (Available Now)

1. **HBM-attached FPGAs** for memory-bound workloads
   - Alveo U55C/U280 for prototyping
   - Direct HBM access from programmable logic
   - Test architectures before committing to ASIC

2. **Memory-aware software architectures**
   - Profile actual memory access patterns
   - Design data structures for spatial locality
   - Prepare for tiered memory (hot/cold separation)

### Medium-Term (2-3 Years)

3. **Hybrid HBM+HBF system design**
   - Define caching policies between tiers
   - Build software that can migrate data transparently
   - Benchmark real workloads on early HBF samples

4. **Edge inference platforms**
   - Design boards that can accommodate HBF packages
   - Thermal solutions for HBF + compute
   - Software stacks for large models on edge

### Long-Term (5+ Years)

5. **Custom silicon with integrated memory**
   - Application-specific base dies for HBM4+
   - Compute elements in memory controllers
   - Novel architectures only possible with new memory

6. **New memory technologies**
   - Watch MRAM, ReRAM, PCM for potential HBM/HBF successors
   - Photonic memory interconnects
   - Neuromorphic memory-compute integration

---

## The Conclusion

For years, we designed systems assuming:
- Memory is separate from compute
- Memory is uniform (one type, one access pattern)
- The bottleneck is compute, not data movement

All three assumptions are breaking:
- Memory and compute are merging (base dies, PIM)
- Memory is heterogeneous (registers → cache → HBM → HBF → SSD)
- Data movement dominates energy and time budgets

The architectures that win will be those designed around data locality and movement, not raw FLOPS. Compute is now distributed throughout the memory hierarchy, not a CPU/GPU talking to remote DRAM.

Just put the CPU inside the RAM, its not that hard.