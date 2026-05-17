import wraplorenzmie.pylorenzmie
from wraplorenzmie.pylorenzmie.theory import Instrument
from wraplorenzmie.utilities.utilities import normalize
from wraplorenzmie.utilities.utilities import crop
from tqdm import tqdm
from pathlib import Path
import re
import numpy as np
import matplotlib.pyplot as plt

from wraplorenzmie.pylorenzmie.analysis import Feature
from wraplorenzmie.pylorenzmie.theory import LMHologram
from wraplorenzmie.pylorenzmie.utilities import coordinates
from wraplorenzmie.pylorenzmie.utilities import azistd
import matplotlib as mpl

mpl.rcParams["xtick.direction"] = "in"
mpl.rcParams["ytick.direction"] = "in"
mpl.rcParams["lines.markeredgecolor"] = "k"
mpl.rcParams["lines.markeredgewidth"] = 0.1
mpl.rcParams["figure.dpi"] = 130
from matplotlib import rc

rc("font", family="serif")
rc("text", usetex=False)
rc("xtick", labelsize="medium")
rc("ytick", labelsize="medium")


def cm2inch(value):
    return value / 2.54


class fitting(object):
    """All the wrap aroud the pylorenzmie toolbox
    available at the grier lab github
    https://github.com/davidgrier/pylorenzmie"""

    def __init__(
        self,
        image,
        wavelength,
        magnification,
        n_m=1.33,
        dark_count=0,
        background=1,
        double_precision=False,
        model=LMHologram,
        mask="fast",
        percentpix=0.1,
    ):
        if mask not in ["uniform", "radial", "donut", "fast"]:
            raise ValueError(
                "Mask should be one of the following : uniform, radial, donut or fast"
            )
        self.image = image
        self.magnification = magnification
        self.shape = image.shape

        self.feature = Feature(model=model(double_precision=double_precision))
        self.feature.data = image / np.mean(image)
        self.feature.coordinates = coordinates(image.shape)
        self.feature.mask.percentpix = percentpix
        self.feature.mask.distribution = mask
        self.ins = self.feature.model.instrument
        self.ins.wavelength = wavelength
        self.ins.magnification = magnification
        self.ins.n_m = n_m

    def show_mask(self):
        fig, (axa, axb) = plt.subplots(
            ncols=2,
            figsize=(5 * 1.2, 2.5 * 1.2),
            sharex=True,
            sharey=True,
            constrained_layout=True,
        )
        axa.imshow(self.feature.mask.selected.reshape(self.image.shape))
        axa.axis("off")
        index = self.feature.mask.selected
        coords = self.feature.coordinates[:, index]
        axb.scatter(
            coords[0, :],
            coords[1, :],
            c=self.feature.data.flatten()[index],
            cmap="gray",
        )
        axb.axis("off")
        plt.show()

    def make_guess(
        self,
        a_p,
        n_p,
        z,
        r_p = None,
        alpha=1,
        show_estimate=False,
    ):
        """Add the guess to the object to fit more nicely, z is to be put in
        µm for easier usage, it will be put in pixels in the actual guess dict
        !!! You need to give it an already cropped image."""

        self.shape = self.image.shape

        # self.feature.properties["alpha"] = alpha
        # self.feature.properties.update(self.aberrations.properties)

        p = self.feature.particle
        if r_p == None:
            p.r_p = [self.shape[0] // 2, self.shape[1] // 2, z / self.ins.magnification]
        else:
            p.r_p = [r_p[0], r_p[1], z / self.ins.magnification]
        p.a_p = a_p
        p.n_p = n_p

        if show_estimate:
            fig, (axa, axb) = plt.subplots(
                ncols=2,
                figsize=(5 * 1.2, 2.5 * 1.2),
                sharex=True,
                sharey=True,
                constrained_layout=True,
            )
            axa.imshow(self.feature.data, cmap="gray")
            axb.imshow(self.feature.hologram(), cmap="gray")

            axa.axis("off")
            axa.set_title("Data")

            axb.axis("off")
            axb.set_title("Initial Estimate")

            plt.show()

    def set_vary(self, vary):
        parameters = [
            "k_p",
            "n_m",
            "alpha",
            "wavelength",
            "magnification",
            "piston",
            "xtilt",
            "ytilt",
            "defocus",
            "xastigmatism",
            "yastigmatism",
            "xcoma",
            "ycoma",
            "spherical",
            "x_p",
            "y_p",
            "z_p",
            "a_p",
            "n_p",
        ]
        fixed = [i for i in parameters if (i not in vary)]

        self.feature.optimizer.fixed = fixed

    def _crop_fit(self, image):
        return np.array(crop(image, self.xc, self.yc, self.h))

    def report(self, result):
        def value(val, err, dec=4):
            fmt = "{" + ":.{}f".format(dec) + "}"
            return (fmt + " +- " + fmt).format(val, err)

        keys = self.feature.optimizer.variables
        res = [i + " = " + value(result[i], result["d" + i]) for i in keys]

        print("npixels = {}".format(result.npix))
        print(*res, sep="\n")
        print("chisq = {:.2f}".format(result.redchi))

    def present(self, feature):
        fig, axes = plt.subplots(
            ncols=3, figsize=(5 * 1.2, 2.5 * 1.2), constrained_layout=True
        )

        vmin = np.min(feature.data) * 0.9
        vmax = np.max(feature.data) * 1.1
        style = dict(vmin=vmin, vmax=vmax, cmap="gray")

        images = [feature.data, feature.hologram(), feature.residuals() + 1]
        labels = ["Data", "Fit", "Residuals"]

        for ax, image, label in zip(axes, images, labels):
            ax.imshow(image, **style)
            ax.axis("off")
            ax.set_title(label)

        plt.show()

    def radial_profile(self, exp, theo, center):
        plt.figure(figsize=(5 * 1.2, 2.5 * 1.2))
        th_avg, expe_std = azistd(theo, center)
        rad_th = np.arange(len(th_avg)) * self.ins.magnification
        plt.plot(rad_th, th_avg, linewidth=2, label="Theory")

        expe_avg, expe_std = azistd(exp, center)
        rad_exp = np.arange(len(expe_avg)) * self.ins.magnification
        plt.plot(rad_exp, expe_avg, linewidth=2, label="Experimental")

        plt.fill_between(rad_exp, expe_avg - expe_std, expe_avg + expe_std, alpha=0.3)
        plt.xlabel("radius ($\mathrm{\mu m}$)", fontsize="large")
        plt.ylabel("$I/I_0$", fontsize="large")
        plt.legend()
        plt.title("Radial profile")

        plt.tight_layout()
        plt.show()

    def optimize(
        self,
        method="trf",
        loss="cauchy",
        report=False,
        present=False,
        radial_profile=False,
    ):
        """Fit an hologram with the given guesses"""
        # self.set_vary(self.fitter) TO DO UPDATE THIS METHOD

        self.feature.optimizer.settings["method"] = method
        self.feature.optimizer.settings["loss"] = loss
        result = self.feature.optimize()
        if report:
            self.report(result)

        if present:
            self.present(self.feature)

        if radial_profile:
            center = (result["x_p"], result["y_p"])
            self.radial_profile(self.feature.data, self.feature.hologram(), center)
        return result

    def update_guess(self, z):
        self.p = self.feature.particle.r_p[2] = z

    def fit_video(
        self,
        xc,
        yc,
        vid,
        savefile,
        h,
        n_start=1,
        n_end=None,
        method="lm",
        loss="linear",
        dark_count_mode="min",
        update_mask=True,
        percentpix = 0.1,
    ):
        """Fit a full movie by just using the guesses of the first image
        the guesses for the next image will take the precedent ones.
        Box_size is the fitted square. To initialize correctly the fitter
        it's needed to give it the the position of the crop"""
        self.xc = int(xc)
        self.yc = int(yc)
        self.h = h
        self.feature.mask.percentpix = percentpix
        if n_end == None:
            print("Computing the length of the video")
            n_end = vid.get_length()
            print("length of video = {}".format(self.number))

        image = vid.get_image(1)
        _crop_fit = self._crop_fit
        if dark_count_mode == "min":
            image = normalize(
                _crop_fit(image),
                _crop_fit(vid.background),
                dark_count=np.min(_crop_fit(image)),
            )
        elif dark_count_mode == "zero":
            image = normalize(_crop_fit(image), _crop_fit(vid.background), dark_count=0)
        elif dark_count_mode == "set":
            image = normalize(
                _crop_fit(image), _crop_fit(vid.background), dark_count=vid.dark_count
            )

        image = image / np.mean(image)
        self.fp = np.memmap(
            savefile,
            dtype="float64",
            mode="w+",
            shape=(int(n_end - n_start), len(self.feature.optimizer.variables) * 2 + 3),
        )
        for n, i in enumerate(tqdm(range(n_start, n_end))):
            if i > n_start:
                image = normalize(vid.get_next_image(), vid.background)
                image = self._crop_fit(image)
                try:
                    image = image / np.mean(image)
                except:
                    image = image

            if update_mask:
                self.feature.mask._update()
                index = self.feature.mask.selected
                coords = self.feature.coordinates[:, index]

            self.feature.data = image
            self.result = self.optimize(method=method, loss=loss)
            self._globalize_result()
            self.save_result(n)
            self.update_guess(self.result.z_p)
        del self.fp

    def fit_image_sequence(
        self,
        xc,
        yc,
        images,
        savefile,
        h,
        background=None,
        n_start=1,
        n_end=None,
        method="lm",
        loss="linear",
        dark_count_mode="min",
        dark_count=0,
        update_mask=True,
        percentpix=0.1,
        channel=1,
        continue_on_error=True,
    ):
        """Fit a TIFF image sequence and write raw memmap results.

        Parameters
        ----------
        xc, yc : int
            Initial global particle center in pixel coordinates. The fitted
            crop is recentered after each successful frame, matching
            ``fit_video`` tracking behavior.
        images : str, pathlib.Path, or sequence of paths
            Folder containing TIFF files, or an explicit list/tuple of image
            paths. Folder inputs include ``.tif`` and ``.tiff`` files and are
            sorted by natural filename order, so ``image2.tif`` comes before
            ``image10.tif``.
        savefile : str or pathlib.Path
            Destination for a raw ``numpy.memmap`` with ``dtype=float64``.
        h : int
            Side length of the square crop used for fitting.
        background : None, scalar, array, or image path, optional
            Background used for normalization. ``None`` uses an array of ones
            with the same shape as each frame. Image paths are read with the
            same TIFF reader and channel handling as sequence frames.
        n_start, n_end : int, optional
            One-based frame-number range to fit. ``n_start`` is inclusive and
            defaults to 1, so frame 1 is the first image in the naturally
            sorted list. ``n_end`` is one-based and exclusive. If ``n_end`` is
            ``None``, it is set to ``number_of_images + 1`` so the default
            call processes every image. Internally, frame number ``k`` reads
            ``image_paths[k - 1]``.
        method, loss : str
            Passed to the existing optimizer settings, preserving the same
            fitting parameter selection mechanism as ``fit_video``.
        dark_count_mode : {"min", "zero", "set"}
            Dark-count handling for normalization. ``"min"`` uses the minimum
            value in the current cropped frame, ``"zero"`` uses 0, and
            ``"set"`` uses ``dark_count``.
        dark_count : float
            Dark-count value used when ``dark_count_mode="set"``.
        update_mask : bool
            If true, refresh the existing feature mask before each fit.
        percentpix : float
            Fraction of pixels selected by the existing mask.
        channel : int or None
            Channel used for RGB/RGBA TIFFs. The default is 1, matching the
            current ``video_reader`` behavior. ``None`` keeps the array as-is
            and requires it to be two-dimensional.
        continue_on_error : bool
            If true, failed frames are recorded as failure rows and fitting
            continues. If false, the first frame error is re-raised after
            restoring the last successful fitting state.

        Output format
        -------------
        Results are written frame-by-frame to a raw ``numpy.memmap`` with
        shape ``(n_end - n_start, len(optimizer.variables) * 2 + 3)``. Columns
        are ``variables + d<variable> uncertainty columns + success + npix +
        redchi``, exactly like ``fit_video``.

        Failure handling
        ----------------
        If a frame cannot be read, normalized, or fitted, this method writes a
        row with NaN parameter/uncertainty values, ``success=0``, and NaN
        statistics, flushes the memmap, restores the last successful model
        properties and crop-center state, and continues with the next frame
        when ``continue_on_error=True``. Only successful frames update the crop
        center and initial guess for subsequent frames.
        """
        image_paths = self._image_sequence_paths(images)
        if n_end is None:
            n_end = len(image_paths) + 1
        if n_start < 1 or n_end < n_start or n_end > len(image_paths) + 1:
            raise ValueError(
                "n_start and n_end must define a valid 1-based frame range"
            )

        self.xc = int(xc)
        self.yc = int(yc)
        self.h = h
        self.feature.mask.percentpix = percentpix
        variables = self.feature.optimizer.variables
        width = len(variables) * 2 + 3
        background_image = self._load_sequence_background(background, channel)
        last_good_properties = self.feature.model.properties.copy()
        last_good_xc = self.xc
        last_good_yc = self.yc
        last_good_h = self.h
        last_good_result = getattr(self, "result", None)

        mm = np.memmap(
            savefile,
            dtype="float64",
            mode="w+",
            shape=(int(n_end - n_start), width),
        )
        self.fp = mm
        try:
            for row, frame_number in enumerate(tqdm(range(n_start, n_end))):
                try:
                    frame = self._read_sequence_image(
                        image_paths[frame_number - 1], channel
                    )
                    bg = self._background_for_frame(background_image, frame)
                    image = self._normalize_sequence_frame(
                        frame, bg, dark_count_mode, dark_count
                    )

                    if update_mask:
                        self.feature.mask._update()

                    self.feature.data = image
                    self.result = self.optimize(method=method, loss=loss)
                    if not bool(self.result["success"]):
                        raise RuntimeError("optimizer did not converge")

                    self._globalize_result()
                    mm[row, :] = self._result_row()
                    mm.flush()
                    self.update_guess(self.result.z_p)
                    last_good_properties = self.feature.model.properties.copy()
                    last_good_xc = self.xc
                    last_good_yc = self.yc
                    last_good_h = self.h
                    last_good_result = self.result
                except Exception:
                    self.feature.model.properties = last_good_properties.copy()
                    self.xc = last_good_xc
                    self.yc = last_good_yc
                    self.h = last_good_h
                    if last_good_result is not None:
                        self.result = last_good_result
                    if not continue_on_error:
                        raise
                    mm[row, :] = self._failed_result_row(width)
                    mm.flush()
        finally:
            del self.fp
            del mm

    def show_results(self):
        fit = self.fitter.model.hologram().reshape(self.shape)
        noise = self.fitter.noise
        mega_image = np.hstack([self.image, fit])
        fig, ax = plt.subplots(figsize=(12, 36))
        ax.imshow(mega_image, cmap="gray", interpolation=None)

    def _globalize_result(self):
        self.result.x_p = self.result.x_p + self.xc - self.h // 2
        self.result.y_p = self.result.y_p + self.yc - self.h // 2
        self.xc = int(self.result.x_p)
        self.yc = int(self.result.y_p)

    def save_result(self, n):
        buf = np.array([])
        variables_to_save = self.feature.optimizer.variables + ['d' + x for x in self.feature.optimizer.variables] + ['success', 'npix', 'redchi']
        for i in self.result[variables_to_save]:
            buf = np.append(buf, i)
        self.fp[n, :] = buf

    def _save_failed_result(self, n, width):
        self.fp[n, :] = self._failed_result_row(width)

    def _result_row(self):
        buf = np.array([])
        variables_to_save = self.feature.optimizer.variables + ['d' + x for x in self.feature.optimizer.variables] + ['success', 'npix', 'redchi']
        for i in self.result[variables_to_save]:
            buf = np.append(buf, i)
        return buf

    def _failed_result_row(self, width):
        buf = np.full(width, np.nan)
        buf[-3] = 0
        return buf

    def _normalize_sequence_frame(
        self, frame, background, dark_count_mode="min", dark_count=0
    ):
        cropped = self._crop_fit(frame)
        cropped_background = self._crop_fit(background)
        if dark_count_mode == "min":
            count = np.min(cropped)
        elif dark_count_mode == "zero":
            count = 0
        elif dark_count_mode == "set":
            count = dark_count
        else:
            raise ValueError("dark_count_mode should be 'min', 'zero', or 'set'")

        image = normalize(cropped, cropped_background, dark_count=count)
        return image / np.mean(image)

    def _background_for_frame(self, background, frame):
        if background is None:
            return np.ones_like(frame)
        if np.isscalar(background):
            return np.full_like(frame, background, dtype=float)
        return background

    def _load_sequence_background(self, background, channel):
        if background is None or np.isscalar(background):
            return background
        if isinstance(background, (str, Path)):
            return self._read_sequence_image(background, channel)
        return np.asarray(background)

    def _image_sequence_paths(self, images):
        if isinstance(images, (str, Path)):
            root = Path(images)
            if root.is_dir():
                paths = [
                    path
                    for path in root.iterdir()
                    if path.suffix.lower() in [".tif", ".tiff"]
                ]
            else:
                paths = [root]
        else:
            paths = [Path(path) for path in images]

        paths = [path for path in paths if path.suffix.lower() in [".tif", ".tiff"]]
        paths = sorted(paths, key=lambda path: self._natural_sort_key(path.name))
        if not paths:
            raise ValueError("No .tif or .tiff images were found")
        return paths

    def _natural_sort_key(self, value):
        return [
            int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", value)
        ]

    def _read_sequence_image(self, path, channel=1):
        try:
            import tifffile

            image = tifffile.imread(path)
        except ImportError:
            import imageio

            image = imageio.imread(path)

        image = np.asarray(image)
        if image.ndim == 2:
            return image
        if image.ndim == 3 and channel is not None:
            return image[:, :, channel]
        raise ValueError("Expected a 2D grayscale image or RGB/RGBA image")


def globalize_result(result, xc, yc, h):
    result.x_p = result.x_p + xc - h // 2
    result.y_p = result.y_p + yc - h // 2
    return result
