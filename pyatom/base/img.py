"""Image operation."""

import random
import hashlib
from pathlib import Path
from typing import Union
from abc import ABC

import filetype
from PIL import Image, ImageSequence
from PIL.Image import Image as ImageObj
import imageio
import numpy as np


__all__ = ("ReHasher",)


class AbsImage(ABC):
    """Abstract cls for Image Operation."""

    @staticmethod
    def read_bytes(file_image: Path) -> bytes:
        """Read byte of image file."""
        with open(file_image, "rb") as file:
            return file.read()

    @staticmethod
    def save_bytes(obj: bytes, file_new: Path) -> bool:
        """Save image obj into local file."""
        with file_new.open("wb") as file:
            file.write(obj)
        return file_new.is_file()

    def get_hash(self, obj: Union[bytes, Path]) -> str:
        """Get hash of bytes obj or of file path."""
        if isinstance(obj, Path):
            obj = self.read_bytes(obj)
        return hashlib.md5(obj).hexdigest()

    @staticmethod
    def get_type(obj: bytes) -> str:
        """Guess type of obj."""
        some = filetype.guess_mime(obj)
        return str(some) if some else ""

    @staticmethod
    def get_ext(file_type: str) -> str:
        """Get file extention string."""
        return file_type.lower().split("/")[1] if file_type else ""


class ReHasher(AbsImage):
    """Simple Example Code for Rehash Image by random pixels.

    To fight against new algorithm like this:
        http://nghiaho.com/?p=1765
    """

    @staticmethod
    def rnd_pos(width: float, height: float) -> tuple[int, int]:
        """Get randomized position as (x, y)."""
        return (
            random.randint(int(width / 100), int(width * 99 / 100)),
            random.randint(int(height / 100), int(height * 99 / 100)),
        )

    @staticmethod
    def rnd_pixel() -> tuple[int, int, int]:
        """Get randomized color as (red, green, blue)."""
        return (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )

    @staticmethod
    def new_color(old: int, move: int = 10) -> int:
        """Generate random integer number for 2^8."""
        new = random.randint(old - move, old + move)
        if new > 255:
            new = new - 255
        elif new < 0:
            new = new + 255
        return new

    def new_pixel(self, color: tuple[int, int, int]) -> tuple[int, int, int]:
        """Get new pixel."""
        red, green, blue = color
        return (
            self.new_color(red),
            self.new_color(green),
            self.new_color(blue),
        )

    def new_image(
        self, file_old: Path, file_new: Path, number: int = 10
    ) -> tuple[Path, bytes]:
        """Generate new image bytes."""
        image = Image.open(file_old)
        if image.format in ("JPEG", "PNG"):
            width, height = image.width, image.height
            for _ in range(number):
                pos = self.rnd_pos(width, height)
                pixel_old = image.getpixel(xy=pos)
                pixel_new = self.new_pixel(pixel_old)
                image.putpixel(xy=pos, value=pixel_new)

            # note for quality control
            image.save(fp=file_new, format=image.format, quality=95, subsampling=0)
            return file_new, self.read_bytes(file_new)

        if image.format == "GIF":
            duration = image.info.get("duration") or 100
            loop = image.info.get("loop") or 1
            list_frame = []
            for frame in ImageSequence.Iterator(image):
                frame = frame.convert("RGB")
                width, height = frame.width, frame.height
                for _ in range(number):
                    pos = self.rnd_pos(width, height)
                    pixel_old = frame.getpixel(xy=pos)
                    pixel_new = self.new_pixel(pixel_old)
                    frame.putpixel(xy=pos, value=pixel_new)

                # for better compitable with linux
                list_frame.append(np.array(frame))

            # for better quality than using PIL image.save method.
            imageio.mimsave(
                uri=file_new,
                ims=list_frame,
                format=image.format,
                duration=duration / 1000,
                loop=loop,
            )
            return file_new, self.read_bytes(file_new)

        raise TypeError(f"image format {image.format} not support!")


class TestRehash:
    """TeseCase for Rehash Image."""

    width = 100
    height = 100
    frames = 10

    rehasher = ReHasher()

    def gen_image(self) -> ImageObj:
        """Generate new image with random color."""
        return Image.new(
            mode="RGB", size=(self.width, self.height), color=self.rehasher.rnd_pixel()
        )

    def test_png_rehash(self) -> None:
        """Test rehash png image."""
        file_old = Path(Path(__file__).parent, "old.png")
        file_new = Path(Path(__file__).parent, "new.png")

        file_old.unlink(missing_ok=True)
        file_new.unlink(missing_ok=True)

        assert file_old.is_file() is False
        assert file_new.is_file() is False

        img = self.gen_image()
        img.save(fp=file_old, format="PNG")

        assert file_old.is_file()
        hash_old = self.rehasher.get_hash(file_old)
        assert hash_old

        file_new, obj_new = self.rehasher.new_image(file_old, file_new)
        assert file_new.is_file()

        hash_new = self.rehasher.get_hash(obj_new)
        assert hash_new
        assert hash_old != hash_new

        file_old.unlink(missing_ok=True)
        file_new.unlink(missing_ok=True)

        assert file_old.is_file() is False
        assert file_new.is_file() is False

    def test_jpg_rehash(self) -> None:
        """Test rehash jpg image."""
        file_old = Path(Path(__file__).parent, "old.jpg")
        file_new = Path(Path(__file__).parent, "new.jpg")

        file_old.unlink(missing_ok=True)
        file_new.unlink(missing_ok=True)

        assert file_old.is_file() is False
        assert file_new.is_file() is False

        img = self.gen_image()
        img.save(fp=file_old, format="JPEG")
        assert file_old.is_file()
        hash_old = self.rehasher.get_hash(file_old)
        assert hash_old

        file_new, obj_new = self.rehasher.new_image(file_old, file_new)
        assert file_new.is_file()

        hash_new = self.rehasher.get_hash(obj_new)
        assert hash_new
        assert hash_old != hash_new

        file_old.unlink(missing_ok=True)
        file_new.unlink(missing_ok=True)

        assert file_old.is_file() is False
        assert file_new.is_file() is False

    def test_gif_rehash(self) -> None:
        """Test rehash gif image."""
        file_old = Path(Path(__file__).parent, "old.gif")
        file_new = Path(Path(__file__).parent, "new.gif")

        file_old.unlink(missing_ok=True)
        file_new.unlink(missing_ok=True)

        assert file_old.is_file() is False
        assert file_new.is_file() is False

        img, *imgs = [self.gen_image() for _ in range(self.frames)]
        img.save(
            fp=file_old,
            format="GIF",
            append_images=imgs,
            save_all=True,
            druation=100,
            loop=1,
        )

        assert file_old.is_file()
        hash_old = self.rehasher.get_hash(file_old)
        assert hash_old

        file_new, obj_new = self.rehasher.new_image(file_old, file_new)
        assert file_new.is_file()

        hash_new = self.rehasher.get_hash(obj_new)
        assert hash_new
        assert hash_old != hash_new

        file_old.unlink(missing_ok=True)
        file_new.unlink(missing_ok=True)

        assert file_old.is_file() is False
        assert file_new.is_file() is False


if __name__ == "__main__":
    TestRehash()
