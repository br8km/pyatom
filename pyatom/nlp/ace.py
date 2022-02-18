"""ACEngine Paraphrase Wrapper."""

import bz2
import os
import os.path as osp
from pathlib import Path
import platform

import subprocess
import gdown

from pyatom.base.io import dir_create, dir_del


__all__ = ("ACEngine",)


class ACEngine:
    """ACEngine, English Only.

    Reference:
        - `https://github.com/iory/ACEngine`

    """

    ace_version = "0.9.31"
    grammar_version = "2018"

    def __init__(self, dir_ace: str) -> None:
        """Init ACEngine."""
        self.dir_ace = dir_ace
        self.dir_bin = osp.join(dir_ace, "bin")
        self.dir_grammar = osp.join(dir_ace, "grammar")

    def get_ace(self) -> str:
        """Download ace."""
        os_name = platform.system()
        base = "http://sweaglesw.org/linguistics/ace/download/ace-{}-{}.tar.gz"
        if os_name == "Windows":
            raise NotImplementedError("Not supported in Windows.")
        if os_name == "Darwin":
            url = base.format(self.ace_version, "osx")
            bin_filename = "ace-{}-{}".format(self.ace_version, "osx")
        else:
            url = base.format(self.ace_version, "x86-64")
            bin_filename = "ace-{}-{}".format(self.ace_version, "x86-64")
        bin_filename = osp.join(self.dir_bin, bin_filename)

        name = osp.splitext(osp.basename(url))[0]
        if not osp.exists(bin_filename):
            gdown.cached_download(
                url=url,
                path=osp.join(self.dir_bin, name),
                postprocess=gdown.extractall,
                quiet=True,
            )
            os.rename(
                osp.join(self.dir_bin, "ace-{}".format(self.ace_version), "ace"),
                bin_filename,
            )
        return bin_filename

    def get_resource_grammar(self) -> str:
        """Get Precompiled grammar images."""
        os_name = platform.system()
        base = "http://sweaglesw.org/linguistics/ace/download/erg-{}-{}-{}.dat.bz2"
        if os_name == "Windows":
            raise NotImplementedError("Not supported in Windows.")
        if os_name == "Darwin":
            url = base.format(self.grammar_version, "osx", self.ace_version)
            name = "erg-{}-{}-{}.dat".format(
                self.grammar_version, "osx", self.ace_version
            )
        else:
            url = base.format(self.grammar_version, "x86-64", self.ace_version)
            name = "erg-{}-{}-{}.dat".format(
                self.grammar_version, "x86-64", self.ace_version
            )

        dat_filename = osp.join(self.dir_grammar, name)
        bz2_file = osp.join(self.dir_grammar, name + ".bz2")
        if not osp.exists(dat_filename):
            gdown.cached_download(
                url=url,
                path=bz2_file,
                quiet=True,
            )
            with open(bz2_file, "rb") as file:
                data = file.read()
                with open(dat_filename, "wb") as file_to:
                    file_to.write(bz2.decompress(data))
        return dat_filename

    def paraphrase(self, text: str, debug: bool = False) -> list[str]:
        """Paraphrase text into list of string."""
        grammar = self.get_resource_grammar()
        ace_binary = self.get_ace()
        cmd = f'echo "{text}" | {ace_binary} -g {grammar} -1T 2>/dev/null | {ace_binary} -g {grammar} -e'
        if debug:
            print(cmd)

        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        ) as proc:
            proc.wait()
            stdout_data, _ = proc.communicate()
            if debug:
                for some in proc.communicate():
                    print(some.decode("utf8"))

            return [
                phrase
                for phrase in stdout_data.decode("utf8").splitlines()
                if len(phrase) > 0
            ]


class TestACEngine:
    """Testcase for ACEngine."""

    dir_app = Path(__file__).parent
    dir_ace = dir_app / "ace"
    dir_ace_str = str(dir_ace.absolute())

    def test_acengine(self) -> None:
        """Test ACEngine Paraphrase."""
        assert dir_create(self.dir_ace)

        ace = ACEngine(dir_ace=self.dir_ace_str)
        text = "The quick brown fox that jumped over the lazy dog took a nap."

        # debug set True
        list_phrase = ace.paraphrase(text=text, debug=True)
        assert len(list_phrase) > 0

        # debug set False
        list_phrase = ace.paraphrase(text=text, debug=False)
        assert len(list_phrase) > 0

        assert dir_del(self.dir_ace)


if __name__ == "__main__":
    TestACEngine()
