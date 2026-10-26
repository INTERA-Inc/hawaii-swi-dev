# hawaii-swi-dev
R&amp;D Development repo that sets up USGS Groundwater Availability model runs for modflow 6 with swi

## Setup

Install [pixi](https://pixi.sh), then from the repository root

```
pixi install
pixi run install
```

`pixi run install` installs the latest MODFLOW 6 release from
[modflow6-feat-swi-preview](https://github.com/jdhughes-dev/modflow6-feat-swi-preview)
(linux, macOS on Apple silicon, and Windows) into the pixi environment using
`get-modflow` from the develop branch of flopy. The release DFN files are
extracted to `dfn/` and the flopy MODFLOW 6 classes are regenerated from them,
so flopy supports the SWI package. The first `pixi run` or `pixi shell` does the
same automatically if it has not been done.

Run `pixi run get-mf6` to update to a newer preview release, or
`pixi run get-mf6 --force` to reinstall. `pixi run check-mf6` reports the
installed version and `pixi run smoke-test` builds and runs a small SWI model.

## Model output

Model output is always written to an `output/` directory beside the model input
files, for example

```
models/oahu/
    mfsim.nam
    oahu.dis
    ...
    output/
        oahu.hds
        oahu.cbc
        oahu.zta
```

Set the output file names in flopy with the `output/` prefix (e.g.
`head_filerecord="output/oahu.hds"`) and create the directory before running
mf6, which does not create it. `output/` directories and MODFLOW 6 output files
(`*.hds`, `*.cbc`, `*.grb`, `*.lst`, etc.) are excluded from the repository.
