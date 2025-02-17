import logging
import pathlib
from sys import exit
from typing import Any, Callable, Dict, List, Optional, Tuple
from pelican.generators import Generator
from .file_formats import JSON, TOML


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DataGenerator(Generator):
    """
    Load data from files
    """

    SUPPORTED_FORMATS = [JSON, TOML]
    CONTEXT_PREFIX = "DATA_"

    def __init__(
        self,
        context,
        settings,
        path,
        theme,
        output_path,
        readers_cache_name="",
        **kwargs,
    ):
        super().__init__(
            context,
            settings,
            path,
            theme,
            output_path,
            readers_cache_name=readers_cache_name,
            **kwargs,
        )
        log.info("PLUGIN: pelican-data-files was successfully loaded")
        self.settings.setdefault("DATA_FILES_DIR", "data")

    def _get_file_type(self, file: pathlib.Path) -> Optional[Dict[str, Any]]:
        """Gets the file format. If the file format is unsupported, return
        None.

        params:

        - file -- pathlib.Path object
        """
        for file_format in self.SUPPORTED_FORMATS:
            if file.suffix in file_format["extensions"]:
                return file_format
        return None

    def _get_data_files(self) -> List[Tuple[Dict[str, Any], pathlib.Path]]:
        """Return list of valid files to load into context"""

        data_dir = pathlib.Path(self.settings["DATA_FILES_DIR"])
        valid_files = []

        # turn path into absolute if not already
        if not data_dir.is_absolute():
            data_dir = pathlib.Path(self.settings["PATH"]).joinpath(data_dir)

        # check if path exists
        if not data_dir.exists():
            log.error("pelican-data-files: DATA_FILES_DIR path doesn't exists.")
            exit(1)

        if not data_dir.is_dir():
            log.error("pelican-data-files: DATA_FILES_DIR path isn't a directory.")
            exit(1)

        # return all valid files in path
        # TODO check for duplicates (eg: profile.json and profile.yaml)
        for file in data_dir.iterdir():
            file_type = self._get_file_type(file)
            if file_type is not None:
                valid_files.append((file_type, file))

        return valid_files

    def _format_filename(self, file):
        """Format context var name from filename.

        params:

        - file -- pathlib.Path object
        """
        return file.stem.replace(".", "_").upper()

    def _read_file(self, file, parser: Callable) -> Optional[Dict]:
        """Read and parse data from file.

        params:

        - file -- pathlib.Path object
        - parser -- the parser to read the format of the file
        """
        with file.open('rb') as f:
            try:
                return parser(f)
            except ValueError:
                return None

    def _add_data_to_context(self, name, data):
        """Add data into context.

        params:

        - name -- str
        - data -- dict
        """
        ctx_name = self.CONTEXT_PREFIX + name
        self.context[ctx_name] = data

    def generate_context(self):
        """Generate context from data files"""
        for file_type, file in self._get_data_files():
            name = self._format_filename(file)
            data = self._read_file(file, file_type["parser"])

            if data:
                self._add_data_to_context(name, data)
                log.info(f"{file.name} was loaded.")
            else:
                log.error(f"{file.name} wasn't loaded.")


def get_generators(pelican_object):
    return DataGenerator
