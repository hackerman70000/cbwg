import os
import tempfile
import unittest

from src.sources.file import FileSource


class TestFileSource(unittest.TestCase):
    """Test cases for the FileSource class."""

    def setUp(self):
        """Set up temporary test files."""
        # Create temporary files for testing
        self.temp_dir = tempfile.TemporaryDirectory()

        # Create a test file with some content
        self.test_file_path = os.path.join(self.temp_dir.name, "test_file.txt")
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write("line1\nline2\nline3\n")

        # Create a second test file
        self.test_file_path2 = os.path.join(self.temp_dir.name, "test_file2.txt")
        with open(self.test_file_path2, "w", encoding="utf-8") as f:
            f.write("fileA\nfileB\nfileC\n")

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_init_with_single_file(self):
        """Test initialization with a single file path."""
        source = FileSource(self.test_file_path)
        self.assertEqual([self.test_file_path], source.file_paths)
        self.assertEqual(source.config["encoding"], "utf-8")  # Default encoding

    def test_init_with_multiple_files(self):
        """Test initialization with multiple file paths."""
        file_paths = [self.test_file_path, self.test_file_path2]
        source = FileSource(file_paths)
        self.assertEqual(file_paths, source.file_paths)

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = {"encoding": "latin-1", "chunk_size": 1024, "binary_mode": True}
        source = FileSource(self.test_file_path, config)
        self.assertEqual("latin-1", source.config["encoding"])
        self.assertEqual(1024, source.config["chunk_size"])
        self.assertTrue(source.config["binary_mode"])

    def test_validate_config_with_invalid_path(self):
        """Test validation with non-existent file path."""
        with self.assertRaises(ValueError):
            FileSource("non_existent_file.txt")

    def test_connect_and_close(self):
        """Test connecting to and closing file sources."""
        source = FileSource(self.test_file_path)
        self.assertTrue(source.connect())
        self.assertEqual(1, len(source.files))

        # Test file is open
        self.assertFalse(source.files[0].closed)

        # Test closing
        source.close()
        self.assertEqual(0, len(source.files))

    def test_get_data_text_mode(self):
        """Test getting data from files in text mode."""
        source = FileSource(self.test_file_path)
        data = list(source.get_data())
        self.assertEqual(["line1", "line2", "line3"], data)

    def test_get_data_multiple_files(self):
        """Test getting data from multiple files."""
        file_paths = [self.test_file_path, self.test_file_path2]
        source = FileSource(file_paths)
        data = list(source.get_data())
        self.assertEqual(["line1", "line2", "line3", "fileA", "fileB", "fileC"], data)

    def test_get_data_binary_mode(self):
        """Test getting data from files in binary mode."""
        config = {"binary_mode": True, "chunk_size": 10}  # Small chunk size for testing
        source = FileSource(self.test_file_path, config)
        data = list(source.get_data())
        # In binary mode with chunk_size=10, we should get chunks of decoded data
        expected = ["line1\nline", "2\nline3\n"]
        self.assertEqual(expected, data)

    def test_context_manager(self):
        """Test using the file source as a context manager."""
        with FileSource(self.test_file_path) as source:
            self.assertEqual(1, len(source.files))
            self.assertFalse(source.files[0].closed)
            data = list(source.get_data())
            self.assertEqual(["line1", "line2", "line3"], data)

        # After exiting context, files should be closed
        self.assertEqual(0, len(source.files))

    def test_get_metadata(self):
        """Test getting metadata about the files."""
        source = FileSource(self.test_file_path)
        metadata = source.get_metadata()

        self.assertEqual("file", metadata["source_type"])
        self.assertEqual(1, len(metadata["files"]))
        self.assertEqual(self.test_file_path, metadata["files"][0]["path"])
        self.assertIn("size", metadata["files"][0])
        self.assertIn("modified", metadata["files"][0])
        self.assertIn("created", metadata["files"][0])


if __name__ == "__main__":
    unittest.main()
