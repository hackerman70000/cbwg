import os
from typing import Any, Dict, Iterator, List, Optional, Union

from src.sources.base import DataSource


class FileSource(DataSource):
    """
    A data source that reads from one or more files.

    This class handles reading data from local files, supporting different
    file formats and reading strategies.
    """

    def __init__(
        self, file_paths: Union[str, List[str]], config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a file-based data source.

        Args:
            file_paths: Path to a file or list of file paths
            config: Optional configuration dictionary with the following options:
                - encoding: File encoding (default: 'utf-8')
                - chunk_size: Size of chunks to read (default: 4096)
                - binary_mode: Whether to read in binary mode (default: False)
        """
        self.file_paths = [file_paths] if isinstance(file_paths, str) else file_paths
        self.files = []
        super().__init__(config)

    def _validate_config(self) -> None:
        """Validate the configuration for file source."""

        self.config.setdefault("encoding", "utf-8")
        self.config.setdefault("chunk_size", 4096)
        self.config.setdefault("binary_mode", False)

        invalid_paths = [path for path in self.file_paths if not os.path.exists(path)]
        if invalid_paths:
            raise ValueError(f"The following file paths do not exist: {invalid_paths}")

    def connect(self) -> bool:
        """
        Open the files for reading.

        Returns:
            bool: True if all files were opened successfully

        Raises:
            FileNotFoundError: If a file is not found
            PermissionError: If a file cannot be accessed
        """
        try:
            self.close()

            for path in self.file_paths:
                mode = "rb" if self.config["binary_mode"] else "r"
                kwargs = (
                    {}
                    if self.config["binary_mode"]
                    else {"encoding": self.config["encoding"]}
                )
                self.files.append(open(path, mode, **kwargs))

            return True
        except (FileNotFoundError, PermissionError) as e:
            self.close()
            raise e

    def get_data(self) -> Iterator[str]:
        """
        Read data from the files in chunks.

        Returns:
            Iterator[str]: An iterator over chunks of file content

        Raises:
            IOError: If reading fails
        """
        if not self.files:
            if not self.connect():
                raise IOError("Failed to connect to file sources")

        try:
            for file in self.files:
                if self.config["binary_mode"]:
                    while True:
                        chunk = file.read(self.config["chunk_size"])
                        if not chunk:
                            break
                        yield chunk.decode(self.config["encoding"], errors="replace")
                else:
                    for line in file:
                        yield line.rstrip("\r\n")
        except (IOError, UnicodeDecodeError) as e:
            raise IOError(f"Error reading file: {e}")

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the files.

        Returns:
            Dict[str, Any]: Dictionary with file metadata
        """
        metadata = {"source_type": "file", "files": []}

        for path in self.file_paths:
            try:
                stat = os.stat(path)
                file_metadata = {
                    "path": path,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "created": stat.st_ctime,
                }
                metadata["files"].append(file_metadata)
            except OSError:
                metadata["files"].append({"path": path})

        return metadata

    def close(self) -> None:
        """Close all open files."""
        for file in self.files:
            try:
                file.close()
            except Exception:
                pass
        self.files = []
