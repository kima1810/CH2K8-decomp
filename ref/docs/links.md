# Useful Links

Community tools, prior research, and reference projects for the College Hoops 2K8 decomp.
Check here before writing a new tool. Repos marked ⭐ are the most directly relevant.

Last updated: 2026-10-22

---

## 1. College Hoops 2K8 & 2K Sports

| Repo | Notes |
|---|---|
| ⭐ [ZMO34/CHoops-Extractor-Reborn](https://github.com/ZMO34/CHoops-Extractor-Reborn) | CH2K8 asset extraction tool. Local clone in `work/third_party/`. |
| [kima1810/CHoops-Extractor](https://github.com/kima1810/CHoops-Extractor) | Continuation of the original discontinued CHoops extractor, aimed at College Hoops 2K Reborn. |
| [kima1810/CH2K8-decomp](https://github.com/kima1810/CH2K8-decomp) | "A decompilation of College Hoops 2K8 (Xbox 360)". |
| [joseph-s-tan/College-Hoops-2K8-Tendency-Editor-Assistant](https://github.com/joseph-s-tan/College-Hoops-2K8-Tendency-Editor-Assistant) | Tool for editing CH2K8 player tendencies. |
| ⭐ [chipelway/apf](https://github.com/chipelway/apf) | All-Pro Football 2K8 decomp. Same 2K / Visual Concepts era and platform, so the closest sister project. |
| [cruuz/2k-football-mod-tools](https://github.com/cruuz/2k-football-mod-tools) | SoftdrinkTV mod editors for ESPN NFL 2K5 (Xbox) and All-Pro Football 2K8 (Xbox 360): uniforms, rosters, stats. |
| [cruuz/softdrink-2k28](https://github.com/cruuz/softdrink-2k28) | SoftdrinkTV 2K modding project. |
| [LeoArtaza/2k5_to_2k8](https://github.com/LeoArtaza/2k5_to_2k8) | Converts ESPN NFL 2K5 rosters into an APF 2K8 import format. |
| [anishchandra24/NHL2K9-Recompiled](https://github.com/anishchandra24/NHL2K8-Recompiled) | Recompilation of NHL 2K8 for XBOX 260 |

## 2. Xbox 360 Reverse-Engineering Tooling

### Recompilers & runtimes
| Repo | Notes |
|---|---|
| ⭐ [hedge-dev/XenonRecomp](https://github.com/hedge-dev/XenonRecomp) | Static recompiler that turns Xbox 360 PPC code into C++. Started the 360 recomp scene. |
| ⭐ [hedge-dev/XenosRecomp](https://github.com/hedge-dev/XenosRecomp) | Converts Xbox 360 (Xenos) shaders to HLSL. |
| ⭐ [rexglue/rexglue-sdk](https://github.com/rexglue/rexglue-sdk) | ReXGlue: Xbox 360 recompilation runtime and toolkit. Most newer ports are built on it. |
| [sp00nznet/360tools](https://github.com/sp00nznet/360tools) | All-in-one kit for statically recompiling 360 games to native PC. |
| [xdzleo/xenon-jumptables](https://github.com/xdzleo/xenon-jumptables) | Recovers Xenon PPC jump tables for XenonRecomp/ReXGlue. |
| [zer0ducksgiven/ReGPU](https://github.com/zer0ducksgiven/ReGPU) | Xenos GPU on Direct3D 12, for XenonRecomp ports. |
| [nate-santos/xbox360-recompilation-guide](https://github.com/nate-santos/xbox360-recompilation-guide) | Step-by-step strategy guide for recompiling a XEX to native C++. |

### Matching decomp toolchain
| Repo | Notes |
|---|---|
| ⭐ [rjkiv/jeff](https://github.com/rjkiv/jeff) | decomp-toolkit fork for Xbox 360 XEX: function boundaries, relocations, splits, objdiff/decomp.me integration. |
| [rjkiv/jeff-template](https://github.com/rjkiv/jeff-template) | Project template for Xbox 360 decomps that use jeff. |
| [encounter/decomp-toolkit](https://github.com/encounter/decomp-toolkit) | The GC/Wii toolkit jeff is based on. |
| [AleBello7276/360msvc-decomp](https://github.com/AleBello7276/360msvc-decomp) | Decompilation of the Xbox 360 compiler (MSVC for Xenon). |
| [AleBello7276/xkrnl-decomp](https://github.com/AleBello7276/xkrnl-decomp) | Xbox 360 kernel decompilation. |
| [francescobbo/X360Decompiler](https://github.com/francescobbo/X360Decompiler) | PowerPC decompiler focused on 360 XEX files. |

### Ghidra / IDA helpers
| Repo | Notes |
|---|---|
| [EveryoneEverybody/Xenon360](https://github.com/EveryoneEverybody/Xenon360) | Ghidra extension: XEX/XEXP loading, Xenon PPC/VMX128 analysis, import naming, PDB support. |
| [freeqaz/ghidra-xenon-extension](https://github.com/freeqaz/ghidra-xenon-extension) | Ghidra extension adding Xenon PPC + VMX128 instructions. |
| [xerootg/ghidra-vmx128](https://github.com/xerootg/ghidra-vmx128) | VMX128 extension for Ghidra's PowerPC SLEIGH. |
| [tomcl7/ghidra-fidb-xenonsdk](https://github.com/tomcl7/ghidra-fidb-xenonsdk) | Ghidra Function ID databases generated from Xbox 360 SDKs (auto-name SDK/CRT functions). |
| [tomcl7/x360-fidb-generator](https://github.com/tomcl7/x360-fidb-generator) | Generator for the FIDBs above. |
| [tomcl7/ghidra-x360-coff-loader](https://github.com/tomcl7/ghidra-x360-coff-loader) | Xbox 360 COFF loader for Ghidra. |
| [GoobyCorp/Xbox-360-Types](https://github.com/GoobyCorp/Xbox-360-Types) | Types for reversing 360 executables in IDA or Ghidra. |
| [murdoch3/Xbox360-Ghidra-Scripts](https://github.com/murdoch3/Xbox360-Ghidra-Scripts) | Assorted Ghidra scripts for 360 reversing. |
| [Goatman13/altivec2c](https://github.com/Goatman13/altivec2c) | IDA plugin that converts AltiVec instructions to C. |

### Emulators
| Repo | Notes |
|---|---|
| [xenia-canary/xenia-canary](https://github.com/xenia-canary/xenia-canary) | Actively maintained Xbox 360 emulator; useful for runtime checks and its kernel HLE source. |
| [xenia-project/xenia](https://github.com/xenia-project/xenia) | Original Xenia project. |

## 3. Xbox 360 Decompilation Projects (source-level / matching)

| Repo | Game |
|---|---|
| ⭐ [rjkiv/dc3-decomp](https://github.com/rjkiv/dc3-decomp) | Dance Central 3. Reference jeff-based matching decomp. |
| [freeqaz/rb3-xenon](https://github.com/freeqaz/rb3-xenon) | Rock Band 3 (MSVC X360 retail), engine shared with dc3-decomp. |
| [freeqaz/dc3-decomp](https://github.com/freeqaz/dc3-decomp) | AI-assisted fork of the Dance Central 3 decomp. |
| [dbalatoni13/nfsmw](https://github.com/dbalatoni13/nfsmw) | Need for Speed: Most Wanted. Multi-version, including an Xbox 360 prototype. |
| [SebaaMG/Kinect-Sports-Decomp](https://github.com/SebaaMG/Kinect-Sports-Decomp) | Kinect Sports (matching). |
| [LCERD/Minecraft-Xbox-360-Decompilation](https://github.com/LCERD/Minecraft-Xbox-360-Decompilation) | Minecraft: Xbox 360 Edition. |
| [surreptitiousresearch/halocea](https://github.com/surreptitiousresearch/halocea) | Halo: Combat Evolved Anniversary (360). |
| [kirklandsig/halo-mega-bloks-decompiled](https://github.com/kirklandsig/halo-mega-bloks-decompiled) | Cancelled Halo Mega Bloks game: decomp plus PC port. |
| [cyberheater/Xbox-360-Quake4-decomp](https://github.com/cyberheater/Xbox-360-Quake4-decomp) | Quake 4 (360). |
| [SplaatSites/the-simpsons-game](https://github.com/SplaatSites/the-simpsons-game) | The Simpsons Game (based on the 360 version). |
| [dpermuy/big-burger-bumpin-king](https://github.com/dpermuy/big-burger-bumpin-king) | Big Bumpin' (360). |

## 4. Xbox 360 Static Recompilation Ports

### Sports titles (closest in genre and structure)
| Repo | Game |
|---|---|
| [puckhead73/nhl-legacy-recomp](https://github.com/puckhead73/nhl-legacy-recomp) | NHL Legacy |
| [griby-man/bardown](https://github.com/griby-man/bardown) | NHL 14, with its own Vulkan renderer |
| [tpalko420-tech/nhl14-recomp](https://github.com/tpalko420-tech/nhl14-recomp) | NHL 14, including Be a GM reverse engineering |
| [GTTeancum/OpenJam](https://github.com/GTTeancum/OpenJam) | NBA JAM: On Fire Edition (XBLA) |
| [HossEz/fifa-world-cup-2014-recompiled](https://github.com/HossEz/fifa-world-cup-2014-recompiled) | 2014 FIFA World Cup Brazil |
| [nefariousjosiah/WWE-SVR2008-RECOMP](https://github.com/nefariousjosiah/WWE-SVR2008-RECOMP) | WWE SmackDown vs. Raw 2008 (same release year as CH2K8) |
| [nefariousjosiah/WWE-SVR2009-RECOMP](https://github.com/nefariousjosiah/WWE-SVR2009-RECOMP) | WWE SmackDown vs. Raw 2009 |
| [nefariousjosiah/WWE-SVR2010-RECOMP](https://github.com/nefariousjosiah/WWE-SVR2010-RECOMP) | WWE SmackDown vs. Raw 2010 |
| [shaneomac1337/SVR2011-Recomp](https://github.com/shaneomac1337/SVR2011-Recomp) | WWE SmackDown vs. Raw 2011 |
| [HollywoodAkeem/SVR07-Recomp](https://github.com/HollywoodAkeem/SVR07-Recomp) | WWE SmackDown vs. Raw 2007 |
| [shaneomac1337/WWE-AllStars-Recomp](https://github.com/shaneomac1337/WWE-AllStars-Recomp) | WWE All Stars |
| [theokyr/Project8Recomp](https://github.com/theokyr/Project8Recomp) | Tony Hawk's Project 8 |
| [cookingwithsimon/Skate1Recompiled](https://github.com/cookingwithsimon/Skate1Recompiled) | Skate |
| [christianortel/skate2-recompile-pc](https://github.com/christianortel/skate2-recompile-pc) | Skate 2 |

### Other notable ports (good references for runtime, graphics, and audio work)
| Repo | Game |
|---|---|
| ⭐ [hedge-dev/UnleashedRecomp](https://github.com/hedge-dev/UnleashedRecomp) | Sonic Unleashed. The flagship XenonRecomp port. |
| [sonicnext-dev/MarathonRecomp](https://github.com/sonicnext-dev/MarathonRecomp) | Sonic the Hedgehog (2006) |
| [SpeedBreakerProject/speedbreaker](https://github.com/SpeedBreakerProject/speedbreaker) | Need for Speed: Most Wanted (2005) |
| [florinp93/hells-gate-recomp](https://github.com/florinp93/hells-gate-recomp) | Dante's Inferno (ReXGlue) |
| [arcanite24/pinyon-shift](https://github.com/arcanite24/pinyon-shift) | Forza Horizon |
| [Dyotson/ForzaHorizon1-ReImagined](https://github.com/Dyotson/ForzaHorizon1-ReImagined) | Forza Horizon |
| [Alexbeav/fm4-recomp](https://github.com/Alexbeav/fm4-recomp) | Forza Motorsport 4 |
| [beatrixzy/PGR4-Recomp](https://github.com/beatrixzy/PGR4-Recomp) | Project Gotham Racing 4 |
| [goliathret/EdgeOfTimeRecomp](https://github.com/goliathret/EdgeOfTimeRecomp) | Spider-Man: Edge of Time |
| [LittleBitUA/DownpourRecomp](https://github.com/LittleBitUA/DownpourRecomp) | Silent Hill: Downpour |
| [LittleBitUA/DPRecomp](https://github.com/LittleBitUA/DPRecomp) | Deadly Premonition (native DX12 renderer) |
| [psxrestore/Condemned2Recomp](https://github.com/psxrestore/Condemned2Recomp) | Condemned 2: Bloodshot |
| [masterspike52/reNut](https://github.com/masterspike52/reNut) | Banjo-Kazooie: Nuts & Bolts |
| [sal063/AC6_recomp](https://github.com/sal063/AC6_recomp) | Ace Combat 6 |
| [birabittoh/NocturneRecomp](https://github.com/birabittoh/NocturneRecomp) | Castlevania: SotN (XBLA) |
| [OpenPortroid/ArmyOfTwoRecompilation](https://github.com/OpenPortroid/ArmyOfTwoRecompilation) | Army of Two (2008) |
| [santiquiroz/gears-of-war-2-pc-port](https://github.com/santiquiroz/gears-of-war-2-pc-port) | Gears of War 2 |
| [Dyotson/RecompiledHaloReach](https://github.com/Dyotson/RecompiledHaloReach) | Halo: Reach |
| [saulob/crackdown-xbox360-recompiled](https://github.com/saulob/crackdown-xbox360-recompiled) | Crackdown |
| [jxnplays/cod3-recomp](https://github.com/jxnplays/cod3-recomp) | Call of Duty 3 |
| [KeithKirenai/L4D-PC-Recomp](https://github.com/KeithKirenai/L4D-PC-Recomp) | Left 4 Dead |
| [UnknownLITE/LibertyRecomp](https://github.com/UnknownLITE/LibertyRecomp) | GTA IV |
| [wivi514/Dead_Rising_2_Case_Zero_Xenon_Recomp](https://github.com/wivi514/Dead_Rising_2_Case_Zero_Xenon_Recomp) | Dead Rising 2: Case Zero |
| [sp00nznet/ctxbla](https://github.com/sp00nznet/ctxbla) | Crazy Taxi (XBLA). Notes on XMA audio issues. |
| [sp00nznet/simpsonsarcade](https://github.com/sp00nznet/simpsonsarcade) | The Simpsons Arcade (XBLA) |

## 5. Catalogs & Lists

| Link | Notes |
|---|---|
| [BlueInterlude/awesome-recompilations](https://github.com/BlueInterlude/awesome-recompilations) | Curated list of N64Recomp and XenonRecomp projects. |
| [wangxiaoxiang5599/recompiled-games-list](https://github.com/wangxiaoxiang5599/recompiled-games-list) | Open list of recompilations, decomps, and runtimes. |
| [CrownParkComputing/Xbox360-Native-Ports](https://github.com/CrownParkComputing/Xbox360-Native-Ports) | Launchers for 360 titles recompiled to native Linux. |
| [justxor/awesome-decomp-games-ru](https://github.com/justxor/awesome-decomp-games-ru) | Catalog of decomps and recomps (Russian). |
| [heldgames.com recompiled games list](https://heldgames.com/guides/recompiled-games-list) | Web list of recompiled games. |
| [evoweb.uk: Xbox 360 Recompilations thread](https://evoweb.uk/threads/xbox-360-recompilations.106908/) | Forum thread tracking 360 recomps, including sports titles. |

## 6. General Decomp & File Format Resources

| Link | Notes |
|---|---|
| [Decompedia: intro to decomp](https://decomp.wiki/en/resources/decomp-intro) | Starting guide to decompilation. |
| [VelocityRa/awesome-game-file-format-reversing](https://github.com/VelocityRa/awesome-game-file-format-reversing/) | Tools and guides for reversing game file formats. |

## 7. PS3 Resources (original target, kept for reference)

| Link | Notes |
|---|---|
| [sp00nznet/ps3recomp](https://github.com/sp00nznet/ps3recomp) | PS3 static recompilation. |
| [PSX-Place: Project PS3 Decompilation](https://www.psx-place.com/threads/project-ps3-decompilation.32241/) | Forum thread on PS3 decompilation. |
