# Daily Paper Digest (Short Summary + Takeaway) — 2026-07-02

- Total papers: **8**
- LLM summarized: **8**
- Sorted by: **rule_score (desc)**

> Note: this digest is optimized for quick triage, highlighting the problem, approach, takeaway, and why it matters.


---

## Tensor Network Solvers for Ultra-large Tight-binding Hamiltonians: Algorithms and Applications

### Metadata

- **arXiv:** `2607.00991v1`
- **rule_score:** `7.0`
- **authors:** Tiago V. C. Antão, Anouar Moustaj, Yitao Sun, Jose L. Lado
- **categories:** cond-mat.str-el, cond-mat.mes-hall
- **pdf_path:** `data/pdfs/2026-07-02/7_Tensor Network Solvers for Ultra-large Tight-binding Hamiltonians Algorithms and Applications__2607.00991v1.pdf`
- **pdf_url:** https://arxiv.org/pdf/2607.00991v1
- **summarized_at:** `2026-07-02T10:11:33`

### Related topics

exciton:exciton · exciton:excitonic · quasicrystal:quasicrystal

### One-sentence summary

A unified tensor-network framework for solving ultra-large tight-binding models with up to billions of sites.

### Problem

Conventional tight-binding methods are limited by the polynomial scaling of matrix storage and diagonalization, making ultra-large systems like moiré superlattices and quasicrystals computationally inaccessible.

### Approach

Mapping lattice sites to a pseudospin chain and using Matrix Product Operators (MPO) with Quantics Tensor Cross Interpolation (QTCI), combined with the Kernel Polynomial Method (KPM) to evaluate observables without explicit diagonalization.

### Main takeaway

By exploiting the tensor-network compressibility of real-space structures, this method enables calculations for systems with billions of sites on standard hardware, covering band structures, topology, dynamics, and correlated physics.

### Why it matters

It provides an efficient and versatile open-source toolkit, TensorBinding.jl, for studying emerging condensed matter problems such as super-moiré structures, quasicrystals, and large-scale excitonic dynamics.

### Value assessment

- **Major advance**
- Significantly extends the computational scale of tight-binding models and integrates diverse functionalities from topology to correlated electronics with high practical utility.

### Paper type

Theory + Numerical

### Likely venue

- **Physical Review Research** `confidence=high`
- The paper details algorithmic implementation, extensive use cases, and an open-source package, aligning well with the journal's focus on computational physics and methodology.

### Keywords

- Tensor Networks
- Tight-binding
- Moiré Superlattices
- Quantics Tensor Cross Interpolation
- Large-scale Simulation


---

## Room temperature valley coherence in monolayer WSe2 mediated by chiral nematic liquid crystal

### Metadata

- **arXiv:** `2607.01098v1`
- **rule_score:** `6.0`
- **authors:** Hassan Lamsaadi, Andrea Balocchi, Aurélien Cuche, Hugo Lourenco Martins, Vincent Paillard, Sébastien Weber, Jean Marie Poumirol, Gonzague Agez
- **categories:** physics.optics
- **pdf_path:** `data/pdfs/2026-07-02/6_Room temperature valley coherence in monolayer WSe2 mediated by chiral nematic liquid crystal__2607.01098v1.pdf`
- **pdf_url:** https://arxiv.org/pdf/2607.01098v1
- **summarized_at:** `2026-07-02T10:12:08`

### Related topics

exciton:exciton · quantum_geometry:berry curvature

### One-sentence summary

This paper demonstrates room-temperature valley coherence in monolayer WSe2 mediated by chiral Bragg reflection from a chiral nematic liquid crystal substrate.

### Problem

Valley coherence in monolayer transition-metal dichalcogenides is extremely difficult to maintain at room temperature due to rapid dephasing and scattering, and existing photonic control methods typically require complex nanofabrication or cryogenic temperatures.

### Approach

Transferring monolayer WSe2 onto a chiral nematic liquid crystal thin film to utilize its helical structure for circularly polarized Bragg reflection, which mediates unidirectional optical coupling between K and K' valleys via spin-flip reflection in the near field.

### Main takeaway

Successfully observed a ~30% linear polarization component in the photoluminescence of monolayer WSe2 at room temperature, directly demonstrating valley coherence that can be controlled by rotating the sample.

### Why it matters

This approach bypasses the need for complex nanofabrication, offering a simple, scalable, and dynamically tunable route (via external stimuli like electric fields or temperature) for developing room-temperature valleytronic devices.

### Value assessment

- **Major advance**
- Proposed and experimentally verified a new scheme to induce room-temperature valley coherence in 2D materials using chiral optical feedback from liquid crystals, bypassing the need for complex microcavities.

### Paper type

Experimental + Numerical

### Likely venue

- **Nano Letters** `confidence=medium`
- The paper presents innovative experimental results combining 2D materials and liquid crystal photonics, suitable for high-level international journals in nanomaterials and photonics.

### Keywords

- Valley coherence
- Chiral liquid crystal
- Transition-metal dichalcogenide
- Room temperature valleytronics
- Bragg reflection


---

## Atom-selective spin-polarized transport in a charge-ordered altermagnet

### Metadata

- **arXiv:** `2607.00506v1`
- **rule_score:** `3.0`
- **authors:** Liu Yang, Yuan-Yuan Jiang, Xiao-Yan Guo, Yi-Dong Liu, Xian-Zhe Chen, Wen-Jian Lu, Yu-Ping Sun, Ming Li, Ding-Fu Shao
- **categories:** cond-mat.mtrl-sci, cond-mat.mes-hall
- **pdf_path:** `data/pdfs/2026-07-02/3_Atom-selective spin-polarized transport in a charge-ordered altermagnet__2607.00506v1.pdf`
- **pdf_url:** https://arxiv.org/pdf/2607.00506v1
- **summarized_at:** `2026-07-02T10:10:58`

### Related topics

altermagnetism:altermagnetic

### One-sentence summary

The study reveals a real-space atom-selective spin-polarized transport mechanism in a charge-ordered altermagnet.

### Problem

Spin-polarized transport in altermagnets is typically described in momentum space, but how to achieve efficient spin transport in systems with weak spin splitting near the Fermi level remains unclear.

### Approach

Combined first-principles calculations and quantum transport simulations to study the electronic structure and real-space transport pathways of the charge-ordered altermagnet Fe2PO5.

### Main takeaway

Electron and hole doping activate spin-polarized transport predominantly through Fe3+- and Fe2+-based real-space channels, respectively, generating a Néel spin current within a globally compensated charge current.

### Why it matters

It proposes a design principle for spintronic tunnel junctions based on real-space atomic channel matching, offering new routes for atomically controlled spin functionalities.

### Value assessment

- **Mechanism clarification**
- Clarifies how real-space charge order and magnetic stacking cooperatively dictate spin transport pathways, explaining strong spin polarization in systems with weak momentum-space spin splitting.

### Paper type

Theory + Numerical

### Likely venue

- **Physical Review Letters** `confidence=medium`
- The paper addresses fundamental spin transport physics in altermagnets and proposes a new device concept, which fits the journal's focus on physical mechanism innovation.

### Keywords

- Altermagnetism
- Spin-polarized transport
- Charge order
- Néel spin current
- Tunnel junction


---

## First-principles calculations of spin-split bands in chiral hybrid organic-inorganic perovskites ($R$/$S$-PEA)PbI$_3$ and ($R$/$S$-NEA)PbI$_3$

### Metadata

- **arXiv:** `2607.00933v1`
- **rule_score:** `3.0`
- **authors:** Tetsuya Furukawa, Kazushi Nakano, Youta Suzuki, Takumi Kaneko, Ayumi Ishii, Tetsuaki Itou
- **categories:** cond-mat.mtrl-sci
- **pdf_path:** `data/pdfs/2026-07-02/3_First-principles calculations of spin-split bands in chiral hybrid organic-inorganic perovskites ($R$$S$-PEA)PbI$_3$ and__2607.00933v1.pdf`
- **pdf_url:** https://arxiv.org/pdf/2607.00933v1
- **summarized_at:** `2026-07-02T10:11:17`

### Related topics

quantum_geometry:circular dichroism

### One-sentence summary

This work reveals the spin-split band structures of chiral hybrid perovskites and their correlation with structural chirality and circular dichroism using first-principles calculations and group theory.

### Problem

Clarifying the differences and microscopic mechanisms of spin-split band structures in 1D chiral hybrid perovskites (R/S-PEA)PbI3 and (R/S-NEA)PbI3.

### Approach

Combining first-principles density functional theory calculations including spin-orbit coupling with group-theoretical analysis of the nonsymmorphic space group P212121.

### Main takeaway

PEA- and NEA-based compounds with the same molecular handedness exhibit opposite spin textures, consistent with the opposite chiral distortions of inorganic octahedra and opposite circular dichroism signs.

### Why it matters

It establishes a theoretical foundation for understanding giant chiroptical responses in chiral hybrid perovskites and offers new design principles for spin-dependent devices.

### Value assessment

- **Mechanism clarification**
- It clarifies the structural mediator for chirality transfer from molecules to electronic spin textures and explains the impact of nonsymmorphic symmetry on band degeneracies.

### Paper type

Theoretical + Computational

### Likely venue

- **Physical Review B** `confidence=high`
- The paper features detailed first-principles calculations and rigorous group-theoretical derivations, which strongly aligns with the journal's scope.

### Keywords

- chiral perovskites
- spin-orbit coupling
- spin splitting
- first-principles calculations
- group theory


---

## Magnon-polaron mediated spin Seebeck effect in altermagnets

### Metadata

- **arXiv:** `2607.00993v1`
- **rule_score:** `3.0`
- **authors:** Ilia Moghayer, Ritesh Das, Yaroslav M. Blanter
- **categories:** cond-mat.mes-hall
- **pdf_path:** `data/pdfs/2026-07-02/3_Magnon-polaron mediated spin Seebeck effect in altermagnets__2607.00993v1.pdf`
- **pdf_url:** https://arxiv.org/pdf/2607.00993v1
- **summarized_at:** `2026-07-02T10:11:43`

### Related topics

altermagnetism:altermagnetic

### One-sentence summary

This paper proposes using the anisotropic resonance peaks of magnon-polaron mediated spin Seebeck effect to experimentally identify altermagnets.

### Problem

Due to vanishing net magnetization, the unique magnetic order of altermagnets is difficult to directly confirm using conventional magnetometry or neutron scattering.

### Approach

Based on a tight-binding model of altermagnets, the authors calculated the spin Seebeck coefficient under a magnetic field using Boltzmann transport theory, incorporating magnetoelastic coupling and phonon dispersions.

### Main takeaway

The spin Seebeck effect in altermagnets exhibits strong directional anisotropy, where the magnon-polaron resonance peaks appear at different magnetic field strengths along different directions, distinct from antiferromagnets.

### Why it matters

This work provides a sensitive transport-based probe to distinguish altermagnets from antiferromagnets (such as MnF2) and lays the foundation for designing stray-field-free spin caloritronic devices.

### Value assessment

- **Major advance**
- Proposes a feasible experimental scheme to identify altermagnetic order using the anisotropy of magnon-phonon hybridization resonance peaks.

### Paper type

Theoretical + Numerical

### Likely venue

- **Physical Review Letters** `confidence=high`
- Altermagnetism is a highly active topic in condensed matter physics, and this study provides a general and highly feasible experimental detection scheme.

### Keywords

- Altermagnets
- Spin Seebeck effect
- Magnon-polarons
- Magnetoelastic coupling
- Spin transport


---

## Exceptional points in dissipative coupling polaron-polaritons

### Metadata

- **arXiv:** `2607.00994v1`
- **rule_score:** `3.0`
- **authors:** A. J. Vega-Carmona, D. A. Mendoza, A. Camacho-Guardian, M. A. Bastarrachea-Magnani
- **categories:** cond-mat.mes-hall, cond-mat.quant-gas, quant-ph
- **pdf_path:** `data/pdfs/2026-07-02/3_Exceptional points in dissipative coupling polaron-polaritons__2607.00994v1.pdf`
- **pdf_url:** https://arxiv.org/pdf/2607.00994v1
- **summarized_at:** `2026-07-02T10:11:53`

### Related topics

exciton:exciton · exciton:excitonic · exciton:polariton · exciton:exciton-polariton · exciton:biexciton

### One-sentence summary

Investigates the effect of dissipative light-matter coupling on strongly interacting polaron-polaritons, revealing the emergence and control of anomalous dispersions and exceptional points.

### Problem

Explores how many-body correlations and non-Hermitian coupling jointly shape the spectrum and exceptional points of polaron-polaritons.

### Approach

Uses finite-temperature Green's function formalism and ladder approximation to theoretically calculate the self-energy and spectral functions of polaron-polaritons with dissipative coupling and decay.

### Main takeaway

Dissipative coupling and relative decay rates induce level attraction, negative effective mass, and tunable, coexisting exceptional points across different polaron-polariton branches.

### Why it matters

Provides new insights for exploring the intersection of non-Hermitian physics and strongly correlated many-body physics in tunable light-matter quasiparticle platforms.

### Value assessment

- **Mechanism clarification**
- Clarifies the mechanism generating anomalous dispersions and exceptional points in polaron-polaritons under the joint effect of dissipative coupling and many-body interactions.

### Paper type

Theoretical

### Likely venue

- **Physical Review B** `confidence=high`
- Theoretical calculations on many-body effects of polaritons in semiconductor microcavities, highly fitting the journal's scope.

### Keywords

- polaron-polaritons
- exceptional points
- non-Hermitian physics
- dissipative coupling
- many-body correlations


---

## Observation of Flat Bands in Type-II Weyl Semimetal TaRhTe$_{4}$

### Metadata

- **arXiv:** `2607.01186v1`
- **rule_score:** `3.0`
- **authors:** Harry Rankin, Tyler J. Slade, Benjamin Schrunk, Yevhen Kushnirenko, Andrew Eaton, K. U. R. R. S. Rathnayaka, Maxwell Doyle, Lin-Lin Wang, Paul C. Canfield, Adam Kaminski
- **categories:** cond-mat.mtrl-sci, cond-mat.str-el
- **pdf_path:** `data/pdfs/2026-07-02/3_Observation of Flat Bands in Type-II Weyl Semimetal TaRhTe$_{4}$__2607.01186v1.pdf`
- **pdf_url:** https://arxiv.org/pdf/2607.01186v1
- **summarized_at:** `2026-07-02T10:12:16`

### Related topics

moire:twisted bilayer

### One-sentence summary

Observation of flat bands near the Fermi level in the noncentrosymmetric type-II Weyl semimetal TaRhTe4 using ARPES.

### Problem

Finding and observing flat bands that coexist with topological states in nonmagnetic bulk Weyl semimetals.

### Approach

Combining flux-growth of single crystals, angle-resolved photoemission spectroscopy (ARPES), and density functional theory (DFT) calculations.

### Main takeaway

Experimentally observed flat bands located approximately 4 meV below the Fermi level on a specific surface termination of TaRhTe4, which were not predicted by DFT.

### Why it matters

This material provides a new platform to study the coexistence and interaction of topological properties and strongly correlated electronic states (flat bands) in a nonmagnetic bulk system.

### Value assessment

- **Major advance**
- First experimental observation of unpredicted flat bands near the Fermi level in a nonmagnetic bulk type-II Weyl semimetal.

### Paper type

Experiment + Theory

### Likely venue

- **Physical Review Letters** `confidence=high`
- The first observation of a unique electronic structure (coexistence of flat bands and Weyl fermions) in a novel topological material fits the scope of the journal.

### Keywords

- TaRhTe4
- Weyl semimetal
- Flat bands
- ARPES


---

## Generation of strongly localized skin solitons in non-Hermitian waveguide arrays with the Kerr effect

### Metadata

- **arXiv:** `2607.00618v1`
- **rule_score:** `2.0`
- **authors:** Chong Hou, Boris A. Malomed, Qin Zhou
- **categories:** physics.optics
- **pdf_path:** `data/pdfs/2026-07-02/2_Generation of strongly localized skin solitons in non-Hermitian waveguide arrays with the Kerr effect__2607.00618v1.pdf`
- **pdf_url:** https://arxiv.org/pdf/2607.00618v1
- **summarized_at:** `2026-07-02T10:11:08`

### Related topics

soliton:soliton

### One-sentence summary

Investigates the soliton dynamics and localization mechanisms driven by the interplay of Kerr nonlinearity and non-Hermitian skin effect in non-reciprocal waveguide arrays.

### Problem

Explores how the non-Hermitian skin effect and Kerr nonlinearity jointly affect the generation, propagation dynamics, and stationary modes of optical solitons under different excitation conditions.

### Approach

Analyzes the nonlinear Hatano-Nelson model using symbolic regression, continuum approximation perturbation theory, and numerical Newton-Raphson methods.

### Main takeaway

The non-Hermitian skin effect acts as a boundary compression mechanism in the nonlinear regime, driving bulk modes to contract toward the edge and evolve into strongly localized skin solitons.

### Why it matters

Successfully extends the non-Hermitian skin effect to the nonlinear regime, providing theoretical guidance for designing topological lasers and integrated photonic devices.

### Value assessment

- **Mechanism clarification**
- Clarifies the competitive and cooperative mechanisms between non-reciprocal coupling and self-focusing nonlinearity in soliton formation and boundary dynamics.

### Paper type

Theoretical and numerical

### Likely venue

- **Physical Review B** `confidence=high`
- The study deeply explores non-Hermitian topological physics and nonlinear lattice dynamics, which fits well within the scope of this journal.

### Keywords

- 非埃尔米特皮肤效应 (Non-Hermitian skin effect)
- Kerr非线性 (Kerr nonlinearity)
- Hatano-Nelson模型 (Hatano-Nelson model)
- 皮肤孤子 (Skin solitons)
- 波导阵列 (Waveguide arrays)

