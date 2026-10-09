# College Hoops 2K8 — PlayStation 3 Game Data and File Format Reference

**Platform:** PlayStation 3  
**Game:** *College Hoops 2K8*  
**Reference date:** October 9, 2026  
**Scope:** Observed game asset organization, binary containers, textures, scene geometry, audio records, roster data, and associated file structures.

## 1. Evidence and terminology

This reference consolidates observations from the supplied PS3 game-file inventory, standard-IFF study, paired-IFF/CDF study, court-scene study, and vanilla/custom roster data. Numeric values and layouts describe the **examined PS3 samples**, not necessarily every regional release or every file bearing a similar name.

- **Observed:** value, byte layout, count, name, or relationship documented in the examined files.
- **Structurally established:** relationship supported by sample pointer resolution, bounds checks, or consistent repeated records.
- **Not identified:** a field exists and its byte representation is known, but its gameplay or rendering meaning has not been established.

All hexadecimal offsets below are byte offsets unless specified otherwise. `BE` means big-endian; `LE` means little-endian; `u8`, `u16`, `u32`, and `s32` denote unsigned or signed integers of the indicated width. Relative offsets are measured from the beginning of the structure or pointer field named in context.

---

## 2. PS3 game archive organization

### 2.1 Split archive files

Game content is present in split archive parts under `PS3_GAME/USRDIR`, including the part named `0A`. The archive metadata contains part descriptors and a table of contents (TOC) locating individual entries within the concatenated logical address space of the parts.

| Structure | Offset or size | Observed representation |
|---|---|---|
| Archive magic | Header `+0x00`, u32 BE | `0xAA00B3BF` |
| Alignment | Header `+0x04`, u32 BE | Multiplier for TOC offset and size units |
| Archive part count | Header `+0x08`, u32 BE | Number of part descriptors |
| Reserved field | Header `+0x0C`, u32 BE | Zero in documented samples |
| Entry count | Header `+0x10`, u32 BE | Number of TOC records |
| Reserved field | Header `+0x14`, u32 BE | Zero in documented samples |
| Part descriptor | 16 bytes each | Describes a physical archive part |
| Part descriptor `+0x00` | u32 BE | Part size in units of `0x800` bytes |
| Part descriptor `+0x08..+0x0F` | 8 bytes | Archive part filename in UTF-16BE |
| TOC entry | 16 bytes each | One stored asset |
| TOC entry `+0x00` | u32 BE | Filename hash |
| TOC entry `+0x04` | u32 BE | Entry's logical offset, in alignment units |
| TOC entry `+0x08` | u32 BE | Unidentified word |
| TOC entry `+0x0C` | u32 BE | Stored length, in alignment units |

The archive's logical offsets span the parts in sequence. An entry may cross a physical part boundary. Documented TOC records include stored-length values that exceed the interval before the next entry; those fields therefore cannot universally be assumed to equal a safe, standalone entry extent.

For known canonical asset names, the documented name-hash relationship is the CRC32 of the uppercase ASCII filename, with case-insensitive filename treatment. Some outer archive hashes remain unnamed in the historical asset listing.

### 2.2 Outer and inner identities

The archive TOC identifies **outer assets** such as `ua256.iff`, `s212.iff`, and `global.iff`. A standard IFF may separately contain an **internal name table** identifying files such as `unif` of type `TXTR` or `floor` of type `SCNE`.

These identity layers are independent. A valid outer IFF may lack an internal name table; the examined `ua256.iff` and `s212.iff` are examples.

### 2.3 Documented asset families

| Name pattern or example | Associated game content |
|---|---|
| `uh###.iff` | Home gameplay uniform |
| `ua###.iff` | Away gameplay uniform |
| `ux###.iff` | Alternate gameplay uniform; sparse among teams |
| `seluh###.iff` | Home uniform team-selection/menu asset |
| `selua###.iff` | Away uniform team-selection/menu asset |
| `selux###.iff` | Alternate uniform team-selection/menu asset |
| `s###.iff` | Stadium, arena, court |
| `m###.iff` | Model/mascot asset family |
| `h####.iff` | Head-model asset family |
| `coach###.iff` | Coach-associated assets |
| `roster_english.iff` | Base roster database containing `ROST` |
| `frontend.iff`, `frontend_sync.iff` | Frontend/presentation assets |
| `global.iff`, `gamedata.iff`, `gamedataextra.iff` | Large shared asset and presentation packages |
| `loading.iff`, `online.iff`, `legacy.iff` | Menu and presentation packages |
| `playercreate.iff`, `facegen.iff` | Player-related presentation and character assets |
| `studio.iff`, `studio_preview.iff`, `studio_pontiac.iff`, `weeklyshow.iff` | Studio and broadcast/presentation assets |
| `dornas.iff`, `statefarm.iff`, `jukebox.iff` | Advertising, presentation, and jukebox packages |
| `teamselectlogo.iff` / `teamselectlogo.cdf` | Team-selection logo texture bank |
| `arenapics.iff` / `arenapics.cdf` | Arena-picture bank |
| `overlaycache.iff` / `overlaycache.cdf` | Overlay cache bank |
| `gameintro_drums.iff` / `.cdf` | Intro percussion audio bank |
| `gameintro_playerspeech.iff` / `.cdf` | Intro speech audio bank |
| `cwd-*.iff` / `.cdf` | Crowd-sound banks |

The file inventory underlying the June 2026 compilation counted the following named families:

| File family | Inventory count |
|---|---:|
| Home gameplay uniforms (`uh`) | 452 |
| Away gameplay uniforms (`ua`) | 452 |
| Alternate gameplay uniforms (`ux`) | 81 |
| Home selection uniforms (`seluh`) | 452 |
| Away selection uniforms (`selua`) | 452 |
| Alternate selection uniforms (`selux`) | 81 |
| Stadiums/courts (`s`) | 384 |
| Model/mascot (`m`) | 101 |
| Head (`h`) | 84 |
| Coach (`coach`) | 50 |
| CDF payload-bank files | 37 |
| Numerically named or unresolved IFFs | 640 |

These are counts in that inventory, not universal game-engine capacity limits. In particular, the alternate-uniform families are not present for every team. Uniforms used during gameplay and their corresponding selection/menu representations are separate game assets.

---

## 3. Standard PS3 IFF container — `0xFF3BEF94`

### 3.1 General organization

The standard standalone PS3 IFF family appears in uniforms, arenas, scene assets, UI/presentation banks, and the base roster.

```text
[0x20-byte IFF header]
[0x20-byte block descriptors × blockCount]
[4-byte file-record pointers × fileCount]
[variable-length file records]
[stored data blocks, usually compressed]
[optional AA171516 internal name table]
[optional trailing bytes or zero padding]
```

The top-level header, descriptors, file pointers, and records are big-endian. The optional internal name-table body uses little-endian integers and UTF-16LE strings.

### 3.2 Main header

| Offset | Encoding | Observed content |
|---|---|---|
| `0x00` | u32 BE | Magic `0xFF3BEF94` |
| `0x04` | u32 BE | `headerSize`, start of first stored block |
| `0x08` | u32 BE | `fileLength`, end of stored block area |
| `0x0C` | u32 BE | Zero |
| `0x10` | u32 BE | Block count |
| `0x14` | u32 BE | Constant 13 in examined files |
| `0x18` | u32 BE | Internal file-record count |
| `0x1C` | u32 BE | Observed `0x20 × blockCount + 0x05` |

For all 37 standard IFF samples in the format study:

```text
fileRecordSize = 0x0C + 0x04 × offsetCount

headerSize = 0x20
           + 0x20 × blockCount
           + 0x04 × fileCount
           + sum(fileRecordSize)
```

The first stored block began at `headerSize`; the maximum stored-block endpoint equaled `fileLength`. `fileLength` excludes any subsequent name table and trailing padding, so it is not necessarily the filesystem length of the IFF.

### 3.3 Block descriptor (`0x20` bytes)

| Relative offset | Field |
|---|---|
| `+0x00` | Block name/hash, u32 BE |
| `+0x04` | Block type/hash, u32 BE |
| `+0x08` | Unidentified block property, values 16/32/128 observed |
| `+0x0C` | Logical/uncompressed block length |
| `+0x10` | Unidentified property, often matches compression-wrapper parameter |
| `+0x14` | Absolute stored-block start within the IFF |
| `+0x18` | Stored/compressed block length |
| `+0x1C` | Indexed flag; zero in documented samples |

Common block identifiers are `0xBB05A9C1`, `0x411536D5`, and `0x76CBC6E7`. They identify blocks/banks and should not be confused with internal subfile type hashes. The 37-file study found **73 blocks**, of which **72 were compressed** and **one was uncompressed**. Observed block counts were 1, 2, and 3.

### 3.4 File-record pointers and logical subfiles

The file-record pointer table follows the block descriptors. Each pointer is a BE u32 relative to the position of that pointer word:

```text
fileRecordAbsoluteOffset = pointerWordOffset + pointerValue - 1
```

Each file record has the following layout:

| Relative offset | Field |
|---|---|
| `+0x00` | Internal asset ID/name hash, u32 BE |
| `+0x04` | Internal subfile type hash, u32 BE |
| `+0x08` | Number of block-offset entries, u32 BE |
| `+0x0C...` | One u32 BE logical offset for each block slot |

`0xFFFFFFFF` marks an absent block slot rather than a real offset. For a particular decompressed block, the byte length associated with a record is delimited by the next **greater valid** offset in that block, or by the block's logical end for the final slice. Records may have several block slots, and a record does not necessarily occupy every block.

### 3.5 Compressed block stream

Most compressed IFF blocks begin with `0x0E4837C3`, followed by a five-word BE header:

| Relative offset | Representation |
|---|---|
| `+0x00` | Magic `0x0E4837C3` |
| `+0x04` | Uncompressed length |
| `+0x08` | Stored length, including 0x14-byte header |
| `+0x0C` | Additional parameter/unknown word |
| `+0x10` | Back-reference shift parameter |
| `+0x14...` | Compressed stream |

The documented H7A-style token organization uses flag bits from least to most significant within each flag byte. A zero bit denotes a literal byte; a one bit denotes a two-byte big-endian back-reference token. For shift value `s`:

```text
distance = token & ((1 << s) - 1)
copyLength = (token >> s) + 3
```

The back-reference copies from the previously decoded output. This behavior describes the investigated compression stream; the wider semantics of the additional parameter word are not established.

### 3.6 Optional internal name table — `0xAA171516`

When present, the internal name table begins at the IFF's `fileLength` offset:

| Field | Representation |
|---|---|
| Name-table magic | `0xAA171516` in BE |
| Body size and internal pointers | LE u32 |
| Names and type strings | UTF-16LE |
| Relative pointer convention | `target = pointerFieldOffset + pointerValue - 1` |

It associates internal asset IDs with names and type labels. **35 of 37** standard IFFs in the sample contained this table. The two valid missing-name-table cases were `ua256.iff` and `s212.iff`.

### 3.7 Observed internal type hashes

These labels are found in the game data; some labels' deeper semantics remain unidentified.

| Type string | Type hash | Type string | Type hash |
|---|---|---|---|
| `TXTR` | `0x5C369069` | `SCNE` | `0xE26C9B5D` |
| `LAYT` | `0x86A1AC9E` | `ROST` | `0xC61649B2` |
| `AUDO` | `0x1AEDDA1F` | `NAME` | `0x68B693B2` |
| `CDAN` | `0xA7701F00` | `FGCT` | `0x5DBCCA93` |
| `Singl` | `0x60900D71` | `FxTwe` | `0xB69815A5` |
| `AUSB` | `0x61DF2234` | `MRKS` | `0xC6ED33A2` |
| `SPCI` | `0x4014B412` | `SHAP` | `0x047C8C98` |
| `AOSS` | `0x1ADE2460` | `FRFG` | `0xBE981E93` |
| `SCOS` | `0x0FA31F4D` | `AMCR` | `0x249FD2C9` |
| `Clth` | `0xE1124F13` | `STRG` | `0xF37C12D9` |
| `UnAD` | `0x070D3D6B` | `UNLK` | `0x1A511857` |
| `PRIV` | `0x26C22AED` | `HTAJ` | `0x6B3AFF68` |
| `SKEL` | `0x7657AB8A` | `BLRB` | `0x79862464` |

In the sample subfile inventory, named types included **664 TXTR**, **429 SCNE**, **216 LAYT**, **179 FGCT**, **41 Singl**, **26 AUDO**, **24 CDAN**, and **24 FxTwe** records. These are sample counts rather than complete game-wide totals.

### 3.8 Documented standalone IFF examples

| IFF | Blocks | Internal records | Notable recorded contents |
|---|---:|---:|---|
| `ua256.iff` | 2 | 11 | Nine TXTR and two NAME by type hash; internal name table absent |
| `uh256.iff` | 2 | 11 | Nine TXTR, two NAME |
| `ux256.iff` | 2 | 11 | Nine TXTR, two NAME |
| `selua256.iff` | 2 | 5 | Four TXTR, one NAME |
| `seluh256.iff` | 2 | 5 | Four TXTR, one NAME |
| `selux256.iff` | 2 | 5 | Four TXTR, one NAME |
| `s000.iff` | 2 | 11 | Eight CDAN, two SCNE, one TXTR |
| `s211.iff` | 2 | 11 | Eight CDAN, two SCNE, one TXTR |
| `s212.iff` | 2 | 12 | Nine CDAN hashes, two SCNE hashes, one TXTR hash; internal name table absent |
| `s213.iff` | 2 | 11 | Eight CDAN, two SCNE, one TXTR |
| `frontend.iff` | 3 | 102 | SCNE, TXTR, LAYT, MRKS, AUDO, PRIV |
| `global.iff` | 3 | 603 | Shared TXTR, SCNE, LAYT, AUDO and many other types |
| `gamedata.iff` | 2 | 262 | TXTR, SCNE, LAYT, SCOS, AOSS, AMCR, AUSB, Singl |
| `online.iff` | 2 | 94 | LAYT, SCNE, TXTR |
| `legacy.iff` | 2 | 143 | SCNE, LAYT, TXTR |
| `playercreate.iff` | 2 | 62 | Singl, TXTR, SCNE, LAYT |
| `studio.iff` | 2 | 179 | 178 FGCT, one SCNE |
| `roster_english.iff` | 1 | 1 | One ROST |
| `weeklyshow.iff` | 2 | 39 | 20 SCNE, 19 LAYT |
| `jukebox.iff` | 2 | 32 | TXTR, SCNE, LAYT, STRG |
| `dornas.iff` | 2 | 36 | 36 TXTR |

---

## 4. Paired IFF/CDF containers — `0xF0985030`

### 4.1 Paired structure

The second major IFF family is a metadata file paired with an external `.cdf` physical payload bank. The IFF begins with `0xF0985030`, unlike the standalone `0xFF3BEF94` family.

```text
example.iff  -> names, internal IDs, type hashes, virtual offsets,
                CDF segment-location descriptors
example.cdf  -> [segment header][payload][segment header][payload]...
```

The IFF describes two virtual blocks: one for record-header-related data and another for payload-related data. The physical CDF alternates record headers and payloads. Thus the virtual block offsets in the primary records are not the physical byte offsets of the CDF.

### 4.2 Paired IFF header

| Offset | Representation |
|---|---|
| `0x00` | u32 BE magic `0xF0985030` |
| `0x04` | Metadata end / internal name-table start |
| `0x08` | Duplicate of metadata-end value in observed samples |
| `0x0C` | Zero in observed samples |
| `0x10` | Virtual block count, observed 2 |
| `0x14` | Observed constant `0x15` |
| `0x18` | Internal record count |
| `0x1C` | Observed constant `0x4D` |
| `0x20` | Relative pointer to secondary CDF segment-pointer table |
| `0x24` | Relative pointer to UTF-16BE `.cdf` filename |
| `0x28` | First 0x20-byte virtual block descriptor |
| `0x48` | Second 0x20-byte virtual block descriptor |
| `0x68` | Primary relative record-pointer table begins |

The relative-pointer convention remains:

```text
target = pointerWordOffset + pointerValue - 1
```

### 4.3 Primary record and physical segment descriptor

Each primary record contains 20 bytes:

| Offset | Meaning |
|---|---|
| `+0x00` | Internal subasset ID/hash, u32 BE |
| `+0x04` | Type hash, u32 BE |
| `+0x08` | Offset count, observed 2 |
| `+0x0C` | Virtual header-block offset |
| `+0x10` | Virtual payload-block offset |

A separate table points to a **16-byte physical descriptor** per record:

| Offset | Meaning |
|---|---|
| `+0x00` | CDF segment-header physical offset |
| `+0x04` | CDF segment-header length |
| `+0x08` | CDF payload physical offset |
| `+0x0C` | CDF payload length |

Observed paired-family type hashes include `AUDO = 0x1AEDDA1F` and `TXTR = 0x5C36FB69`. The CDF `TXTR` hash differs from the standalone-IFF TXTR hash `0x5C369069`.

### 4.4 Paired bank sample results

Eight fully paired samples were documented:

| Base name | Record count | Record family |
|---|---:|---|
| `cwd-cheer-lrg-front_small` | 2 | AUDO |
| `cwd-cheer-lrg-rear_large` | 7 | AUDO |
| `cwd-cheer-lrg-rear_small` | 2 | AUDO |
| `cwd-cheer-med-front_large` | 15 | AUDO |
| `cwd-cheer-med-front_small` | 2 | AUDO |
| `gameintro_drums` | 4 | AUDO |
| `gameintro_playerspeech` | 4 | AUDO |
| `teamselectlogo` | 520 | TXTR |

For these pairs, every recorded physical descriptor was within its CDF file, and the last segment reached the CDF end exactly. One additional audio CDF, `cwd-cheer-med-rear_large.cdf`, was examined without its paired IFF; 15 audio record sequences were found, with the expected terminal boundary.

### 4.5 Paired texture bank observations

The `teamselectlogo` bank contained 520 named TXTR records. The physical segment-header length was variable, generally near `0x5E`, with values `0x5B`, `0x5C`, `0x5E`, and `0x5F` observed. The header included:

| Offset within segment header | Observed content |
|---|---|
| `+0x00` | Magic `0x0E4837C3` |
| `+0x04` | Constant `0xB0` in this sample |
| `+0x08` | Physical segment-header length field |
| `+0x0C` | Values 7 or 8 |
| `+0x10` | Value 8 |
| `+0x15` | Unaligned u32 BE asset ID |

The unaligned ID matched the corresponding IFF record ID in all 520 examined records. The embedded texture payload began with `0x0E4837C3` at each physical payload offset. The exact meanings of several texture-segment header words have not been fully established.

---

## 5. Texture data and uniforms

### 5.1 Native texture organization

Observed textures occur in at least three contexts:

1. `TXTR` records inside standard standalone IFFs, including uniforms and many UI assets.
2. `TXTR` records inside paired IFF/CDF banks, including `teamselectlogo`.
3. Texture records inside `SCNE` packages, alongside scene/geometry data.

Texture records contain header/descriptor information and stored image data. The PS3 texture structures include GTF-oriented descriptor fields. Observed format classes in the examined textures include **L8, ARGB8, DXT1, DXT3, and DXT5**. Linear versus swizzled organization, image dimensions, mip levels, and row pitch affect the physical byte layout. Not every TXTR family uses identical wrapping or header organization.

### 5.2 Common TXTR/SCNE texture descriptor fields

For the characterized header layout, a texture descriptor begins at byte `+0x58` of its header-side record.

| Record offset | Observed field |
|---|---|
| `+0x58` | Texture format byte |
| `+0x59` | Mipmap count |
| `+0x5A` | Dimensionality |
| `+0x5B` | Cube flag |
| `+0x60` | Width, u16 BE |
| `+0x62` | Height, u16 BE |
| `+0x64` | Depth, u16 BE |
| `+0x68` | Pitch/row-layout value, u32 BE |
| `+0x90` | Repeated packed dimension word in examined SCNE texture headers |
| `+0xA4` | Image-data offset plus one in applicable inline/SCNE packages |

In the examined scene packages, individual texture-header records are `0xB0` bytes. Other texture variants may require additional fields not characterized by this table.

### 5.3 Uniform families and subfiles

Gameplay uniforms `uh###`, `ua###`, and `ux###` are **standalone standard IFFs**, not `.iff/.cdf` pairs. Examined normal uniform archives contained two data blocks and eleven subfiles, typically **nine TXTR** and **two NAME** records.

Documented subfile names and meanings include:

| Internal name | Type | Observed association |
|---|---|---|
| `unif` | TXTR | Main jersey image |
| `short` | TXTR | Shorts image |
| `logo` | TXTR | Uniform logo image |
| `unifbump` | TXTR | Jersey normal/bump image |
| `shortbump` | TXTR | Shorts normal/bump image |
| `jersey_numbers` | TXTR | Jersey-number glyph atlas |
| `names` | TXTR | Jersey-name glyph atlas |
| `numbers` | NAME | Number positioning/layout metadata |
| `names` | NAME | Name positioning/layout metadata |

A name can therefore occur in different internal type classes (for example, an image atlas and a metadata record), with different data meanings. The `NAME` records are **not image textures**. Recorded NAME content includes pairs of 16-bit coordinate-like values (examples `0x0020, 0x000B`, `0x0040, 0x000E`, and `0x0060, 0x001B`); their full field schema and glyph placement semantics are not conclusively mapped.

Uniform selection assets use separate `seluh`, `selua`, and `selux` IFFs. Examined menu-selection uniform IFFs contained **four TXTR** and **one NAME** subfiles, rather than the gameplay uniform's nine TXTR/two NAME layout.

### 5.4 Atlas distinctions

Some jersey-name/number atlases have a documented **linear L8** texture layout, unlike other conventional uniform images. The format observations distinguish the actual atlas image bytes from their companion NAME layout data. The evidence does not establish that every uniform shares the same glyph ordering, atlas metadata, or texture subtype.

---

## 6. SCNE scenes, courts, and geometry

### 6.1 Scene package structure

`SCNE` records occur in courts/arenas, scene models, and presentation assets. The examined `floor.scne` data has a header-side logical block and a data-side logical block:

- **Header-side block:** package header, texture headers, model-part records, materials, draw batches, vertex-buffer descriptors, vertex declarations, names and metadata.
- **Data-side block:** texture bytes and geometry buffers, including index and vertex data.

The package header is `0x54` bytes:

| Header offset | Meaning |
|---|---|
| `+0x00` | Relative name offset plus one |
| `+0x20` | Texture count |
| `+0x24` | Texture-table relative pointer |
| `+0x44` | Model-part count |
| `+0x48` | Model-part table relative pointer |

The table pointer relations documented for this package are `textureTable = word(+0x24) + 0x23` and `partTable = word(+0x48) + 0x47` when measured from the beginning of the header-side block.

### 6.2 Named floor parts and materials

Repeated floor-model part names in the court study are:

| Part | Observed role |
|---|---|
| `floor` | Floor and apron surface geometry |
| `paint` | Colored/key region surfaces |
| `centerlogo` | Center logo/circle surfaces |
| `lines` | Court-line overlays and colored line surfaces |

Observed material names include `floor`, `apron`, `apron2`, `paint`, `centerlogo`, `lines`, `key_hash_3`, `outer_lines`, `lane_line1`, and `lane_line2`.

### 6.3 Model-part record (`0xB0` bytes)

| Record offset | Observed content |
|---|---|
| `+0x00` | Relative pointer to part name, UTF-16BE |
| `+0x04` | Part identity hash/ID |
| `+0x08` | Flags/visibility-related word |
| `+0x10` | Float-like radius/scale/bound field; precise meaning not identified |
| `+0x30..+0x38` | Bounding center X, Y, Z floats |
| `+0x4C..+0x54` | Scale X, Y, Z floats |
| `+0x60` / `+0x64` | Material count / relative material pointer |
| `+0x7C` / `+0x80` | Draw-run count / relative draw-run pointer |
| `+0x84` / `+0x88` | Vertex-buffer descriptor count / relative pointer |
| `+0x94` / `+0x9C` | Vertex declaration count / relative pointer |
| `+0xA4` | Primitive/index flags, commonly `0x20000010` |
| `+0xA8` | Index count |
| `+0xAC` | Index-buffer offset plus one into the data-side block |

The word at `+0xA4` is **not** the index count; the count is `+0xA8`.

### 6.4 Material records, draw runs, and vertex descriptors

**Material records** are `0x30` bytes. Their `+0x20` field points to a material name; `+0x24` is an ID/hash; `+0x28` and `+0x2C` contain material/color/layer-routing values. The first `0x20` bytes include material/color-related parameters.

**Draw-run records** are `0x30` bytes:

| Offset | Content |
|---|---|
| `+0x00` | Commonly 6 |
| `+0x04` | Index start |
| `+0x08` | Index count |
| `+0x0C` | Triangle-strip span, normally index count minus 2 |
| `+0x14` | Vertex start |
| `+0x18` | Vertex count |
| `+0x20` | Draw/pass ID |
| `+0x2C` | Render/pass flag |

Other draw-run words were zero in the documented example layout.

**Vertex-buffer descriptors** are `0x30` bytes, with the operative fields beginning at `+0x10`:

| Offset | Content |
|---|---|
| `+0x10` | Vertex count |
| `+0x14` | Stream/buffer count; usually 1 |
| `+0x18` | Attribute/declaration count; usually 5 |
| `+0x1C` | Buffer flags; commonly `0x40000003` |
| `+0x20` | Vertex stride, commonly `0x24` (36 bytes) |
| `+0x24` | Vertex buffer byte length |
| `+0x28` | Vertex data offset plus one |

**Vertex declaration records** are `0x40` bytes; the first 0x10 bytes contain observed semantic IDs and packed declaration/format information, while the remainder is reserved/padding in characterized floor files.

### 6.5 Known floor vertex bytes

The floor samples include vertices with a **36-byte stride**:

| Vertex-relative offset | Type and role |
|---|---|
| `+0x00` | Three float32 BE position values: X, Y, Z |
| `+0x0C` | Four float32 BE auxiliary values |
| `+0x1C` | Two half-float BE UV0 values: U, V |
| `+0x20` | Four packed auxiliary/color bytes |

The stride is taken from the vertex-buffer descriptor at `+0x20` within that descriptor, not from the high byte of a packed vertex declaration.

### 6.6 Floor and apron arrangements

Two arrangements were documented in examined court assets:

- **Split floor/apron:** the `floor` part has two draw runs, often base floor on pass ID 0 and apron on pass ID 1. Base-floor UV coordinates can extend outside `0..1` because the texture is tiled.
- **One-run floor/apron:** one combined floor/apron run; some native examples have approximately **292 vertices and 686 indices** with draw/pass ID 0.

Measured geometry bounds from several floor samples were approximately:

```text
X: -1132.8995 to +1132.8994
Z: -1829.0146 to +1829.0150
```

The distinction between floor, apron, paint, line, and center-logo materials matters to the scene's rendering and team-color routing. The semantic meaning of every draw/pass flag and material parameter is not fully established.

---

## 7. Audio data

### 7.1 AUDO storage contexts

`AUDO` records occur inside some standard IFFs (including large frontend/global packages) and inside paired audio IFF/CDF banks such as `gameintro_drums`, `gameintro_playerspeech`, and crowd sound packages.

### 7.2 Paired AUDO segment header (`0x24` bytes)

In the studied audio CDFs, each physical segment consists of a 36-byte record header followed by encoded audio bytes.

| Segment header offset | Observed u32 BE word |
|---|---|
| `+0x00` | 1 |
| `+0x04` | 5 |
| `+0x08` | 15 (`0x0F`) |
| `+0x0C` | Size-like value, larger than compressed payload length |
| `+0x10` | 48000 (sample-rate field) |
| `+0x14` | 0 |
| `+0x18` | Encoded payload length |
| `+0x1C` | 0 |
| `+0x20` | 0 |

The header's payload length matched the CDF physical segment descriptor for all corresponding audio samples. The `+0x0C` value was around 3.35 times the compressed payload length in the documented set, but its exact units are unknown. The **audio encoding/codec has not been identified** from the available records.

---

## 8. ROST roster database and PS3 save data

### 8.1 Base roster and sampled custom roster

The game's `roster_english.iff` is a standard IFF with a single `ROST` record. In the studied data:

| Roster source | Observed payload |
|---|---:|
| Base `roster_english.iff` ROST | 3,981,216 bytes |
| Decrypted custom PS3 save ROST | 4,061,184 bytes |
| Difference | 79,968 bytes |

The examined decrypted saved-roster `USERDATA` begins with a four-byte BE length field, followed by the ROST bytes:

```text
[u32 BE payload length][ROST payload]
```

In the sample, the prefix was `0x003DF800` and the total `USERDATA` size was 4,061,188 bytes. The associated PS3 save archive also contained entries such as `PARAM.SFO`, `PARAM.PFD`, and `ICON0.PNG`. The format observations concern **decrypted data**; they do not define the console's encrypted/signed save-layer internals.

### 8.2 ROST table layout

| Table | Start offset | Number of rows | Row size |
|---|---:|---:|---:|
| Players | `0x000271AC` | 5,685 | 308 (`0x134`) |
| Arenas | `0x001D5C84` | 379 | 28 (`0x1C`) |
| Teams | `0x001D85E0` | 443 | 704 (`0x2C0`) |
| Coaches | `0x0023F78C` | 1,373 | 44 (`0x2C`) |

These table boundaries and row counts are established for the characterized roster data, not demonstrated as universal maximum capacities. Calculating the arena range with all 379 rows reaches `0x001D85F8`, **0x18 bytes after** the nominal team-table start `0x001D85E0`; the documented addresses therefore have a small overlap and should not be described as strictly disjoint.

### 8.3 ROST relative pointers

ROST references use signed relative offsets, unlike standard IFF's one-based relative-pointer convention:

```text
recordTarget = pointerFieldByteOffset + readS32BE(pointerFieldByteOffset)
```

There is **no subtraction of one** in this relation. Referenced strings use UTF-16LE. Row references often address a specific point *inside* the target row rather than the row's first byte.

| Reference | Target bias within referenced row |
|---|---:|
| Team's arena reference | `+0x19` inside arena row |
| Team's rival reference | `+0x31` inside team row |
| Team's coach/assistant reference | `+0x15` inside coach row |
| Team's player-roster-slot reference | `+0x11` inside player row |

### 8.4 Player fields

| Player-row relative offset | Observed content |
|---|---|
| `+0x10` | Signed relative pointer to UTF-16LE last name |
| `+0x14` | Signed relative pointer to UTF-16LE first name |
| `+0x18..+0x1B` | Four-byte packed player/index ID and jersey number |
| `+0x18` (high halfword) | Player/index identifier |
| `+0x1A` (low halfword) | Jersey number, u16 BE |
| `+0x3A` | Height in inches, u8 |
| `+0x3B` | Position enumeration, u8 |

Position values:

| Value | Position |
|---|---|
| 0 | Point guard (PG) |
| 1 | Shooting guard (SG) |
| 2 | Small forward (SF) |
| 3 | Power forward (PF) |
| 4 | Center (C) |

Other player bytes vary with player records. A definitive mapping of the complete appearance, skin-tone, face, accessories, and rating fields was not established in the consulted binary descriptions.

### 8.5 Team fields

Each examined team row is 704 bytes. Documented fields include:

| Team-row relative offset | Observed content |
|---|---|
| `+0x00` | Team code/name pointer |
| `+0x30` | Short/team name pointer |
| `+0x34` | Abbreviation pointer |
| `+0x38` | School/full name pointer |
| `+0x3C` | Mascot plural pointer |
| `+0x40` | Mascot name pointer |
| `+0x44` | Arena reference |
| `+0x4C`, `+0x50`, `+0x54` | Three rival references |
| `+0x60`, `+0x64`, `+0x68` | Head coach and two assistants |
| `+0x6C..+0xA8` | Sixteen relative references to player records |
| `+0x18C` | Upper 16 bits: asset ID; lower 16 bits: team row/check value |
| `+0x190` | Upper 16 bits: repeated asset ID; lower 16 bits: mascot-related ID or `0xFFFF` |
| `+0x194` | Upper 16 bits: repeated asset ID; lower 16 bits: observed zero in sample |
| `+0x198` | Student-section name pointer |
| `+0x19C` | Midnight Madness/event string pointer |
| `+0x1A0..+0x218` | Region with 31 four-byte color/material-like values |

In documented samples the asset ID is stored in the high u16 portion of each of the words at `+0x18C`, `+0x190`, and `+0x194`.

### 8.6 Team row number versus asset ID

The team's row number in the roster table and its art/asset ID are distinct.

Examples from the recorded mappings:

| Team | Documented asset ID | Associated archive-name family |
|---|---:|---|
| Georgia | 256 | `uh256`, `ua256`, `ux256`, selection uniforms, `s256`, `m256` where present |
| Central Connecticut | 212 | `uh212`, `ua212`, `s212`; mascot availability varies |

Community roster arrangements have different row ordering while retaining links to existing asset-numbered game files. The existence of an alternate uniform is a separate property of the game asset inventory; an asset ID does not by itself imply the presence of `ux###` or `selux###`.

### 8.7 Arena and coach records

In the documented roster samples:

- **Arena rows:** 379 records of 28 bytes; the row contains arena-identifying data, including arena code and name. The characterized string pointers include arena code at `+0x04` and arena name at `+0x18`.
- **Coach rows:** 1,373 records of 44 bytes; strings include coach name at `+0x14` and abbreviation at `+0x18`.

The referenced-row biases in §8.3 apply to relationships from team records into the arena and coach tables.

### 8.8 Observed school-associated color data

Each examined team row contains an approximately 31-word region from `+0x1A0` through `+0x218` inclusive. Many words resemble packed four-channel color values and recur as whites, near-blacks, grays, and school-associated hues. Recorded examples include:

| Team | Asset ID | Examples among its region's raw words |
|---|---:|---|
| Duke | 11 | `FFFFFFFF`, `002F86FF`, `003A94FF` |
| Georgia | 256 | `FFFFFFFF`, `AD3640FF`, `0A0A0AFF` |
| North Carolina | 15 | `FFFFFFFF`, `91BBF4FF`, `A9C8E7FF` |
| Notre Dame | 46 | `FFFFFFFF`, `08226FFF`, `00965AFF` |
| Kentucky | 257 | `FFFFFFFF`, `004584FF`, `0055DFFF` |
| Kansas | 87 | `FFFFFFFF`, `00529BFF`, `D3123BFF` |

The region's exact channel interpretation and per-word assignments to uniform, paint, court line, trim, lighting, UI, or other rendering uses have **not** been verified. These values establish stored team-associated color-like data, not a fully decoded palette schema.

---

## 9. Distinctions established by the examined game files

| Distinction | Observed result |
|---|---|
| Standard versus paired IFF | Different magic values (`FF3BEF94` versus `F0985030`) and different payload placement |
| Gameplay uniforms versus paired texture banks | `ua/uh/ux` are standalone standard IFFs with embedded TXTR/NAME; `teamselectlogo` is paired IFF/CDF |
| Gameplay uniforms versus menu representations | `selua/seluh/selux` are separate archives |
| Jersey glyph image versus layout metadata | `jersey_numbers`/`names` TXTR store image data; corresponding NAME records store non-image metadata |
| Archive filename versus IFF subfile name | TOC identity and optional internal name-table identity are independent |
| Team row index versus team asset ID | Stored as distinct identity values within ROST |
| Physical versus virtual offsets in paired IFF/CDF | Secondary descriptors contain actual CDF segment positions |
| Standard IFF pointers versus ROST pointers | Standard relative offsets use `field + value - 1`; ROST signed pointers use `field + delta` |
| `floor.scne` draw fields | `+0xA4` is primitive/index flags; `+0xA8` is the index count |
| Confirmed structure versus unknown semantics | Several type hashes, texture fields, color words, appearance bytes, and the audio codec remain semantically unidentified |

## 10. Primary supplied research sources

The observations in this reference derive from these supplied data reports and inventories:

- `ps3_standard_iff_format_report.md` — 37 standalone IFF examples, header/record/type/name-table and compression findings.
- `ps3_standard_iff_file_summary.csv` — example-by-example IFF block and file counts.
- `ps3_standard_iff_subfiles.csv` — observed internal subfile names and type distributions.
- `ps3_standard_iff_type_map.csv` — observed type string and hash associations.
- `ps3_cdf_iff_format_report.md` — paired IFF/CDF structures, 520-logo bank and audio-record evidence.
- `floor_scne_format.md` — court scene, draw-run, vertex, texture, and material layouts.
- The supplied full PS3 asset-name inventory, base roster study, and decrypted custom roster study.

The references describe the examined PS3 samples. Where field semantics remain uncertain, this document reports their observed representation without assigning unverified gameplay meanings.
