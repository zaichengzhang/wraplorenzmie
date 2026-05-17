# TIFF Image Sequence Fitting Example

`fit_image_sequence` fits TIFF frames from a folder or an explicit path list without changing the existing `fit_video` workflow.

```python
import numpy as np
from wraplorenzmie.fits.fit import fitting

sequence_dir = r"E:\ResearchData\lorenzmie\raw\sample_sequence"
background = r"E:\ResearchData\lorenzmie\backgrounds\background.tiff"
savefile = r"E:\ResearchData\lorenzmie\results\trajectory.dat"

# Use a representative cropped/normalized image to initialize the fitter.
initial_crop = np.ones((200, 200), dtype=float)
fitter = fitting(
    initial_crop,
    wavelength=0.532,
    magnification=0.08,
    n_m=1.33,
    mask="fast",
    percentpix=0.1,
)

fitter.make_guess(a_p=1.0, n_p=1.45, z=20.0)
fitter.set_vary(["x_p", "y_p", "z_p", "a_p", "n_p"])

fitter.fit_image_sequence(
    xc=640,
    yc=480,
    images=sequence_dir,
    savefile=savefile,
    h=200,
    background=background,
    n_start=1,
    n_end=None,
    method="lm",
    loss="linear",
    dark_count_mode="min",
    continue_on_error=True,
)
```

Folder inputs include `.tif` and `.tiff` files, sorted naturally. `n_start` and `n_end` use one-based frame numbers: `n_start` is inclusive, `n_end` is exclusive, and `n_end=None` processes through the last image.
