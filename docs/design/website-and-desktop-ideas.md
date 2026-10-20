# Website and desktop ideas for review

These are proposals, not supported features or implementation commitments.

## Website direction

Shipped: the editorial homepage, real desktop captures in the tour, ISO
downloads with checksums, and the Sköll and Hati day/night switch (`website/README.md`).

Still open:

- A web Handbook that consumes the existing Markdown/catalog sources rather than
  a second set of instructions.
- Paired light/dark theme screenshots in the theme gallery, accurately labeled
  and using cleared artwork.
- Project details: architecture, requirements, and measured sizes or
  timings, published only with reproducible test conditions.
- ISO signatures and per-release notes beside the checksums.
- Serve each artwork at several widths (`srcset` 800/1600/2400) with explicit
  `width`/`height`, so phones download smaller images and nothing shifts while
  they load.

## Potential desktop improvements

| Proposal | Existing Eitr foundation | Suggested next step |
| --- | --- | --- |
| First-run tour | Offline Handbook, Learn sources, native panels | Offer an optional tour linking to existing controls and Handbook chapters; no forced setup or duplicated shortcuts. |
| Theme metadata and previews | Theme carousel and coordinated app styles | Add validated metadata for theme name, light/dark pairing, artwork provenance, and preview assets; retain both current selection workflows. |
| Hardware compatibility record | GPU detection and VM testing guide | Record tested guest/real hardware, versions, known limitations, and reproducible results. Avoid inferring compatibility from a successful package install. |
| Searchable package overview | Official/AUR/local manifests and installation menus | Offer an informational categorized inventory generated from existing manifests; keep installation/removal in the current confirmed workflow. |

## Constraints

Preserve Eitr's existing backends, menu structure, installer safety, and theme
regeneration. Review each proposal separately before implementation. New documented
workflows need the matching Handbook updates and generated catalog checks.
