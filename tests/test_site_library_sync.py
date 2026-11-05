"""Website free library import integrity and no duplicate/unsafe publication."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
import wave
import zipfile

from site_library_sync import import_release


def make_fixture(root, *, tamper=False):
    folder=Path(root)/"assets"
    folder.mkdir()
    name="comedy_bonk_01.wav"
    path=folder/name
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes(b"\x00\x00"*4800)
    blob=path.read_bytes()
    sha=hashlib.sha256(blob).hexdigest()
    entry={
      "id":"free-123-1-comedy_bonk_01",
      "file":name,"title":"Comedy Bonk","context":"comedy",
      "description":"Original procedural accent","duration_seconds":0.1,
      "sha256":sha,"public_tier":"FREE_DEMO",
      "creative_review":"AUTOMATED_SIGNAL_SCREEN_ONLY",
      "source":"Lokal Audio Lab original procedural SFX"
    }
    data={
      "version":1,"date_wib":"2026-11-06","source_run":"123-1",
      "source_release_tag":"sfx-123-1","status":"AUTOMATED_FREE_DEMO",
      "sounds":[entry]
    }
    catalog=json.dumps(data).encode()
    (folder/"free-demo-catalog.json").write_bytes(catalog)
    with zipfile.ZipFile(folder/"free-demo-pack.zip","w") as z:
        z.write(path,name)
        z.writestr("free-demo-catalog.json",catalog)
    if tamper:
        entry["sha256"]="a"*64
        (folder/"free-demo-catalog.json").write_text(json.dumps(data))
    return folder


class ImportTests(unittest.TestCase):
    def test_import_and_repeat_idempotently(self):
        with tempfile.TemporaryDirectory() as root:
            asset=make_fixture(root)
            lib=Path(root)/"library"
            self.assertEqual(import_release(asset,lib,"sfx-123-1"),1)
            self.assertEqual(import_release(asset,lib,"sfx-123-1"),0)
            data=json.loads((lib/"catalog.json").read_text())
            self.assertEqual(len(data["sounds"]),1)
            target=Path(root)/data["sounds"][0]["url"]
            self.assertTrue(target.is_file())
            self.assertTrue(target.read_bytes().startswith(b"RIFF"))

    def test_reject_mismatched_tag_and_corruption(self):
        with tempfile.TemporaryDirectory() as root:
            asset=make_fixture(root,tamper=True)
            with self.assertRaises(ValueError):
                import_release(asset,Path(root)/"library","sfx-123-1")
            with self.assertRaises(ValueError):
                import_release(asset,Path(root)/"library","sfx-111-1")
            self.assertFalse((Path(root)/"library/catalog.json").exists())


if __name__=="__main__":
    unittest.main()
