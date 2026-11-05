"""Safely import explicitly free, QC-gated SFX release audio to GitHub Pages.

No access to private masters is required after downloading the two free-only
release assets. Invoked by .github/workflows/daily-free-library.yml.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import zipfile

ALLOWED_CONTEXTS={"cinematic","comedy","audio_drama","commercial","gaming","shortform"}
FILENAME=re.compile(r"^[a-z][a-z0-9_]{1,70}_[0-9]{2}\.wav$")
RELEASE=re.compile(r"^sfx-([0-9]{1,20})-([0-9]{1,5})$")
DATE=re.compile(r"^20[0-9]{2}-[0-9]{2}-[0-9]{2}$")
MAX_BYTES_PER_WAV=650_000
MAX_PUBLIC_BYTES=800_000_000


def load_catalog(library):
    file=library/"catalog.json"
    if not file.exists():
        return {"version":1,"sounds":[],"updated_at":None}
    value=json.loads(file.read_text(encoding="utf-8"))
    if value.get("version")!=1 or not isinstance(value.get("sounds"),list):
        raise ValueError("Existing public catalog is invalid; stopping to avoid data loss")
    return value


def import_release(asset_dir, library_dir, expected_tag):
    asset_dir=Path(asset_dir)
    library=Path(library_dir)
    if not RELEASE.fullmatch(expected_tag):
        raise ValueError("Invalid source release tag")
    data=(asset_dir/"free-demo-catalog.json").read_bytes()
    new=json.loads(data)
    if (new.get("version")!=1 or new.get("status")!="AUTOMATED_FREE_DEMO"
            or new.get("source_release_tag")!=expected_tag
            or new.get("source_run")!=expected_tag.removeprefix("sfx-")):
        raise ValueError("Missing explicit free/demo provenance")
    day=new.get("date_wib")
    if not isinstance(day,str) or not DATE.fullmatch(day):
        raise ValueError("Invalid publication date")
    entries=new.get("sounds")
    if not isinstance(entries,list) or len(entries)>3:
        raise ValueError("Unexpected free file count")

    catalog=load_catalog(library)
    existing={entry["id"]:entry for entry in catalog["sounds"]}
    paths=[]
    new_entries=[]
    archive=asset_dir/"free-demo-pack.zip"
    with zipfile.ZipFile(archive) as zip_file:
        expected_names={item["file"] for item in entries}|{"free-demo-catalog.json"}
        if set(zip_file.namelist())!=expected_names or zip_file.testzip() is not None:
            raise ValueError("Free-only ZIP has unexpected files or invalid CRC")
        if zip_file.read("free-demo-catalog.json")!=data:
            raise ValueError("Free catalog differs from ZIP copy")
        for entry in entries:
            name=entry.get("file")
            digest=entry.get("sha256")
            if (not isinstance(name,str) or not FILENAME.fullmatch(name)
                or entry.get("public_tier")!="FREE_DEMO"
                or entry.get("creative_review")!="AUTOMATED_SIGNAL_SCREEN_ONLY"
                or entry.get("context") not in ALLOWED_CONTEXTS
                or not isinstance(digest,str) or not re.fullmatch("[0-9a-f]{64}",digest)):
                raise ValueError("Free catalog contains unsafe or unapproved field")
            if not (0.1 <= float(entry.get("duration_seconds",0)) <= 4):
                raise ValueError("Invalid WAV duration")
            blob=zip_file.read(name)
            if len(blob)>MAX_BYTES_PER_WAV or len(blob)<100:
                raise ValueError("Free file unexpectedly large/small")
            if not blob.startswith(b"RIFF") or blob[8:12]!=b"WAVE":
                raise ValueError("Free file must be a RIFF WAVE")
            if hashlib.sha256(blob).hexdigest()!=digest:
                raise ValueError("Free WAV checksum mismatch")
            url="library/audio/"+day+"/"+new["source_run"]+"/"+name
            output=library.parent/url
            item={
                "id":entry["id"],
                "title":str(entry["title"])[:70],
                "context":entry["context"],
                "description":str(entry.get("description",""))[:220],
                "duration_seconds":float(entry["duration_seconds"]),
                "date_wib":day,
                "url":url,
                "sha256":digest,
                "tier":"FREE_DEMO",
                "source_release":expected_tag,
            }
            if item["id"] in existing:
                if existing[item["id"]].get("sha256")!=digest:
                    raise ValueError("Duplicate ID with different audio")
                if not output.is_file() or hashlib.sha256(output.read_bytes()).hexdigest()!=digest:
                    raise ValueError("Previously imported public WAV missing/corrupt")
                continue
            paths.append((output,blob))
            new_entries.append(item)
    if not new_entries:
        print("Already synchronized:",expected_tag)
        return 0
    current_size=sum(f.stat().st_size for f in (library/"audio").rglob("*.wav")) if (library/"audio").exists() else 0
    if current_size+sum(len(b) for _,b in paths)>MAX_PUBLIC_BYTES:
        raise ValueError("Public sound library approaching Pages storage limit; use external object storage")

    for path, blob in paths:
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            raise ValueError("Public output already exists without catalog entry: "+str(path))
        path.write_bytes(blob)
    catalog["sounds"]=(new_entries+catalog["sounds"])
    catalog["updated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
    library.mkdir(parents=True,exist_ok=True)
    (library/"catalog.json").write_text(
        json.dumps(catalog,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Imported",len(new_entries),"new free SFX from",expected_tag,
          "; total library",len(catalog["sounds"]))
    return len(new_entries)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--assets",type=Path,required=True)
    p.add_argument("--library",type=Path,default=Path("library"))
    p.add_argument("--tag",required=True)
    args=p.parse_args()
    import_release(args.assets,args.library,args.tag)


if __name__=="__main__":
    main()
