"""Stage ONLY same-day, QC-passing marketing MP4s for social publishing.

Input files come from the private owner GitHub release and are copied into
an ephemeral GitHub Pages deployment directory. Private source WAVs, masters,
source videos and release ZIPs are never copied wholesale to the public site.

Posting is intentionally handled separately by an authorized scheduler.
"""
from __future__ import annotations
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

BASE="https://lokalaudiolab.github.io"
NETWORKS=("tiktok","instagram")
TAG=re.compile(r"^marketing-(20\d{2}-\d{2}-\d{2})$")
MIN_MP4_BYTES=100_000
MAX_MP4_BYTES=80_000_000

def inspect_mp4(path):
    data=Path(path).read_bytes()
    if not MIN_MP4_BYTES < len(data) < MAX_MP4_BYTES:
        raise ValueError("MP4 size outside safe distribution range")
    if data[4:8]!=b"ftyp":
        raise ValueError("MP4 signature missing")
    probe=subprocess.run(["ffprobe","-v","error","-show_entries",
      "stream=codec_type,codec_name,width,height:format=duration",
      "-of","json",str(path)],capture_output=True,text=True,timeout=25,check=True)
    details=json.loads(probe.stdout)
    stream=next((s for s in details.get("streams",[]) if s.get("codec_type")=="video"),None)
    duration=float(details.get("format",{}).get("duration",0))
    if not stream or stream.get("codec_name")!="h264" or not 12<=duration<=90:
        raise ValueError("Bad video codec or duration")
    if stream.get("width",0)/max(1,stream.get("height",1))>.65:
        raise ValueError("Video not vertical")
    return {"width":stream["width"],"height":stream["height"],
            "duration_seconds":round(duration,2),
            "sha256":hashlib.sha256(data).hexdigest()}

def create_manifest(asset_dir,output_root,tag,expected_day):
    asset_dir=Path(asset_dir)
    output_root=Path(output_root)
    match=TAG.fullmatch(tag)
    if not match or match[1]!=expected_day or date.fromisoformat(expected_day).isoformat()!=expected_day:
        raise ValueError("Source release does not match current date")
    qc=json.loads((asset_dir/"creative-qc.json").read_text(encoding="utf-8"))
    queue=json.loads((asset_dir/"publish-queue.json").read_text(encoding="utf-8"))
    if qc.get("approval")!="PENDING" or qc.get("summary",{}).get("objective_pass") is not True:
        raise ValueError("Marketing QC failed or unexpected creative approval")
    if queue.get("run_date_wib")!=expected_day or queue.get("status")!="REVIEW_REQUIRED":
        raise ValueError("Invalid publication source provenance")
    # The source pipeline is still private and human approval pending.
    # These are merely candidate public URLs, not permission to post.
    data={"version":1,"date_wib":expected_day,"source_release":tag,
          "status":"MEDIA_STAGED__NOT_PUBLISHED",
          "creative_approval":"PENDING",
          "auto_publish_policy":"LIMITED_QC_PILOT_FROM_2026-11-07",
          "user_requested_daily_autopublish":True,
          "canva_design_id":queue.get("canva",{}).get("master_design_id"),
          "canva_video_rendered":False,
          "review_gate":"Explicit user-autopilot request plus technical QC; creative excellence not guaranteed",
          "media":{}}
    for network in NETWORKS:
        check=qc["platforms"][network]
        queued=queue["assets"][network]
        if check.get("objective_checks")!="PASS" or check.get("warnings"):
            raise ValueError("QC warnings forbid external staging for "+network)
        if queued.get("video_filename")!=network+".mp4" or queued.get("quality_gate")!="PASS":
            raise ValueError("Source manifest mismatch for "+network)
        p=asset_dir/(network+".mp4")
        video=inspect_mp4(p)
        if queued.get("video_sha256")!=video["sha256"]:
            raise ValueError("MP4 differs from QA-reviewed source")
        caption=(asset_dir/(network+".txt")).read_text(encoding="utf-8").strip()
        if not 30<len(caption)<2200 or "lokalaudiolab.github.io" not in caption:
            raise ValueError("Missing product CTA or invalid caption")
        dest=output_root/"social"/"daily"/expected_day/(network+".mp4")
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dest)
        data["media"][network]={
            "url":BASE+"/social/daily/"+expected_day+"/"+network+".mp4",
            "caption":caption,"video":video,"provider":"Metricool",
            "is_ai_generated":True,
            "auto_publish_authorized":expected_day>="2026-11-07"}
    m=output_root/"social"/"latest.json"
    m.parent.mkdir(parents=True,exist_ok=True)
    m.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("STAGED source",tag,"2 verified videos","approval PENDING")
    return data

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--assets",type=Path,required=True)
    p.add_argument("--site",type=Path,default=Path("site-dist"))
    p.add_argument("--tag",required=True)
    p.add_argument("--date",required=True)
    args=p.parse_args()
    create_manifest(args.assets,args.site,args.tag,args.date)

if __name__=="__main__":
    main()
