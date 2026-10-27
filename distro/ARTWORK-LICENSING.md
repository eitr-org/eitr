# Artwork licensing

This is the project's policy, not legal advice. Have it reviewed before a public
release if the project grows.

`distro/artwork.json` lists every image the package ships, by pattern: where it
came from, its license, and whether it is cleared for public distribution.
`python3 distro/artwork-check.py` (run by the tests) fails when a shipped image
has no entry; `--public` also fails while any entry is not `cleared`, and
`build-iso.sh` runs that when `EITR_PUBLIC_RELEASE=1`.

## Licenses

- **EITR artwork** (generated wallpapers and lockscreen backgrounds, SVG
  geometry, screenshots): Creative Commons Attribution 4.0 International
  ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode)), credited
  to "the EITR project". Anyone may reuse and adapt it with credit.
- **The EITR logo and wordmark**: the files are shipped for EITR itself. Forks
  and derivative distributions must use their own name and logo; describing a
  project as "based on EITR" is fine.
- **Third-party marks**: none ship. Icons a user's web apps download stay on that
  machine under their owners' terms.
- **Code** keeps its own licenses (for example the lockscreen layouts' GPL notice
  in `quickshell/lockscreen/LICENSE`); `NOTICE.md` lists them all.

## AI-generated images

The wallpapers and lockscreen backgrounds were generated with Codex, with prompts
recorded in `themes/artwork-*.json` and `quickshell/lockscreen/ARTWORK.md`.
Whether purely generated images are protected by copyright differs by country
(in the United States, works without human authorship are not), so the
CC BY 4.0 grant covers whatever rights the project holds in them. Generation also
does not clear content: an image that depicts a recognizable character, logo or
franchise setting carries that owner's rights however it was made. Prompts asked
for original imagery, with references guiding only mood and palette.

Batch 06 adds ten original realm environments under the same EITR artwork
license. The owner requested scenic landscapes and painterly rendering for this
set only. They were generated from written briefs without image references;
exact prompts and native-source provenance are in `themes/artwork-batch-06.json`.
The approved Batch 05 illustrations remain the realm previews.

## Before a public release

`python3 distro/artwork-check.py --public` lists any shipped image that is not
cleared. Franchise artwork was removed or renamed, and EITR ships no third-party
brand marks: AI providers use neutral glyphs, and web apps download their site's
icon on the user's machine when created (Walker > Install > Web Apps).

When adding artwork, add or extend an entry in `distro/artwork.json` and record
the prompt or source next to the image.
