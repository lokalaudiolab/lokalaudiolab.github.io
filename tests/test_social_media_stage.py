"""Contract tests for daily public marketing media staging."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from social_media_stage import create_manifest

class MediaStageTests(unittest.TestCase):
    def make_sources(self,root,valid=True):
        root=Path(root);src=root/"source";src.mkdir()
        for platform in ("tiktok","instagram"):
            subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
              "-f","lavfi","-i","color=c=black:s=360x640:r=24",
              "-t","12.3","-c:v","libx264","-pix_fmt","yuv420p",
              str(src/(platform+".mp4"))],check=True,timeout=40)
            (src/(platform+".txt")).write_text("Sound design story. Free SFX: https://lokalaudiolab.github.io/ #SoundDesign")
        import hashlib
        assets={}
        for platform in ("tiktok","instagram"):
            b=(src/(platform+".mp4")).read_bytes()
            assets[platform]={"video_filename":platform+".mp4","quality_gate":"PASS",
                               "video_sha256":hashlib.sha256(b).hexdigest()}
        queue={"status":"REVIEW_REQUIRED","run_date_wib":"2026-11-06",
               "canva":{"master_design_id":"DAHaGSVP3fw"},"assets":assets}
        qc={"approval":"PENDING","summary":{"objective_pass":valid},
            "platforms":{p:{"objective_checks":"PASS" if valid else "REVIEW_FLAGS",
                "warnings":[] if valid else ["MOTION:video_too_static"]} for p in ("tiktok","instagram")}}
        (src/"creative-qc.json").write_text(json.dumps(qc))
        (src/"publish-queue.json").write_text(json.dumps(queue))
        return src

    def test_stage_and_keep_private_audio_out(self):
        with tempfile.TemporaryDirectory() as root:
            src=self.make_sources(root)
            site=Path(root)/"site"
            manifest=create_manifest(src,site,"marketing-2026-11-06","2026-11-06")
            self.assertEqual(manifest["status"],"MEDIA_STAGED__NOT_PUBLISHED")
            self.assertFalse(manifest["media"]["tiktok"]["auto_publish_authorized"])
            self.assertTrue((site/"social/daily/2026-11-06/tiktok.mp4").exists())
            self.assertEqual(set(p.name for p in (site/"social/daily/2026-11-06").iterdir()),
                             {"tiktok.mp4","instagram.mp4"})
    def test_refuse_failed_qc_or_stale_source(self):
        with tempfile.TemporaryDirectory() as root:
            src=self.make_sources(root,False)
            with self.assertRaises(ValueError):create_manifest(src,Path(root)/"public","marketing-2026-11-06","2026-11-06")
            with self.assertRaises(ValueError):create_manifest(src,Path(root)/"public","marketing-2026-11-05","2026-11-06")
if __name__=="__main__":unittest.main()
