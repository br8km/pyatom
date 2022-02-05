"""Image operation."""

import random
import hashlib
from pathlib import Path
from typing import Union

import filetype
from PIL import Image, ImageSequence
import imageio


__all__ = ("Rehash",)


class ImageBase:
    """Base cls for Image Operation."""

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


class Rehash(ImageBase):
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
            duration = image.info.get("duration", 100)
            loop = image.info.get("loop", 1)
            list_frame = []
            for frame in ImageSequence.Iterator(image):
                frame = frame.convert("RGB")
                width, height = frame.width, frame.height
                for _ in range(number):
                    pos = self.rnd_pos(width, height)
                    pixel_old = image.getpixel(xy=pos)
                    pixel_new = self.new_pixel(pixel_old)
                    frame.putpixel(xy=pos, value=pixel_new)
                list_frame.append(frame)

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
