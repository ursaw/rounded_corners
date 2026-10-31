# Baglabs RoundCorners Inkscape Extension

This repository contains the Baglabs RoundCorners Inkscape extension that collects key panel dimensions.

## Structure

```
extensions/
└── baglabs_roundcorners/
    ├── baglabs_roundcorners.inx
    └── baglabs_roundcorners.py
```

## Installation

1. Copy the contents of `extensions/baglabs_roundcorners` to your Inkscape extensions directory:
   - **Linux:** `~/.config/inkscape/extensions/`
   - **Windows:** `%APPDATA%\Inkscape\extensions`
   - **macOS:** `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions`
2. Restart Inkscape if it was running.

## Usage

Open Inkscape and find the extension under **Extensions → Baglabs → Parts → Baglabs RoundCorners**.

The dialog collects the following inputs (all interpreted as centimeters):

- Länge (L)
- Breite (Br)
- Höhe (Ho)
- Segmenthöhe (Hs)
- Radius Top (Rt)
- Radius Bottom (Rb)

Click **Apply** (then close the dialog). The extension plots the UPPER and LOWER patches 1:1 in cm next to each other and resizes the page to fit them (press `5` to fit the page into the window if you see nothing):

- solid outer line (corner radius R + 1 cm), dashed sewing line 1 cm inside
- thick marks between the two lines, with the clock numbers printed on the inner side; corner marks sit in the middle of each arc
- blue dimensions: overall width/height and one radius per patch
- an info box per patch with its name, the date and all input parameters

A message box confirms the plotted sizes. Formulas follow `dev/Baglab_roundedCorners_WIP.xlsx`.

## Running standalone (without the Inkscape GUI)

The script can be run from the command line. It reads an SVG, adds the patches and writes a new SVG. This needs the `inkex` module that ships with Inkscape (`/usr/share/inkscape/extensions` on Linux) and a few Python packages:

```bash
python3 -m pip install lxml cssselect numpy
```

1. Create an empty input document (any SVG works; the page is resized automatically):

   ```bash
   cat > /tmp/empty.svg <<'EOF2'
   <svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="210mm" height="297mm" viewBox="0 0 210 297"><g inkscape:groupmode="layer" id="layer1" inkscape:label="Layer 1"/></svg>
   EOF2
   ```

2. Run the extension (all values in cm; the defaults are the values of the XLSX file):

   ```bash
   PYTHONPATH=/usr/share/inkscape/extensions python3 extensions/baglabs_roundcorners/baglabs_roundcorners.py \
       --length=50 --width=30 --height=30 --segment_height=20 \
       --radius_top=11 --radius_bottom=5 \
       --output=/tmp/patches.svg /tmp/empty.svg
   ```

3. Open `/tmp/patches.svg` in Inkscape or any SVG viewer, or export it, e.g. to PNG or PDF:

   ```bash
   inkscape /tmp/patches.svg --export-type=png --export-filename=/tmp/patches.png -w 1800
   inkscape /tmp/patches.svg --export-type=pdf --export-filename=/tmp/patches.pdf
   ```

Notes:

- Without `--output` the SVG is written to stdout. A short summary message is printed to stderr (its hint "Press 5 to fit the page into the window" only applies inside Inkscape and can be ignored).
- `python3 extensions/baglabs_roundcorners/baglabs_roundcorners.py --help` lists all options.
- If `inkex` is installed elsewhere (e.g. macOS: `/Applications/Inkscape.app/Contents/Resources/share/inkscape/extensions`), adjust `PYTHONPATH`. On Windows use `set PYTHONPATH=...` and Inkscape's bundled Python.

## DXF export

`baglabs_dxf.py` in the project base writes the two patches to a DXF file (CAD/laser/plotter). It uses the same model as the extension, so marks and sizes are identical. Units are cm (1 drawing unit = 1 cm), the Y axis points up. It needs the same setup as the standalone run above (`inkex` via `PYTHONPATH`), but no extra DXF package.

```bash
PYTHONPATH=/usr/share/inkscape/extensions python3 baglabs_dxf.py            # writes baglabs_patches.dxf
PYTHONPATH=/usr/share/inkscape/extensions python3 baglabs_dxf.py --length=60 --radius_top=12 --output=/tmp/my.dxf
```

Layers: `OUTLINE` (solid), `SEWING` (dashed, 1 cm inside), `MARKS` (each mark is drawn as a double line, since DXF R12 has no line width) and `TEXT` (mark numbers, patch name and date). The dimension lines, the info box and the mark tables of the SVG are not exported.

## Development

- The extension is written using the `inkex` Python module (bundled with Inkscape).
- You can test syntax quickly with `python3 -m compileall extensions/baglabs_roundcorners/baglabs_roundcorners.py`.

Feel free to expand the scaffold by adding additional parameters, validation, or actions.