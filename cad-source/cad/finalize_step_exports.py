"""Recover missing/zero STEP files from validated immutable bytes after writers stop.
Default is read-only. Run with --restore only after all legacy/unlocked writers stop.
Nonzero files with a different checksum are reported and NEVER overwritten.
"""
from pathlib import Path
import argparse,fcntl,hashlib,json
from common import ROOT,atomic_bytes

def finalize(root,restore=False):
 root=Path(root);results=[];cache_root=root/'.step-cache'
 if not cache_root.exists():return [{'status':'no_validated_cache'}]
 for folder in sorted(cache_root.iterdir()):
  mp=folder/'manifest.json'
  if not mp.is_file():continue
  slug=folder.name;lockdir=root/'.export-locks';lockdir.mkdir(exist_ok=True)
  with open(lockdir/(slug+'.lock'),'a+b') as lock:
   try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:
    results.append({'slug':slug,'status':'active_writer_skipped'});continue
   try:
    manifest=json.loads(mp.read_text())
    metadata=root/slug/'design.json'
    if not metadata.is_file() or hashlib.sha256(metadata.read_bytes()).hexdigest()!=manifest.get('design_sha256'):
     results.append({'slug':slug,'status':'generation_mismatch_skipped'});continue
    for name,rec in manifest.get('files',{}).items():
     if Path(name).name!=name or not name.endswith('.step') or Path(rec['blob']).name!=rec['blob']:
      results.append({'slug':slug,'file':name,'status':'unsafe_manifest_entry_skipped'});continue
     blob=folder/rec['blob'];data=blob.read_bytes() if blob.is_file() else b''
     if len(data)!=rec['bytes'] or len(data)<100 or hashlib.sha256(data).hexdigest()!=rec['sha256']:
      results.append({'slug':slug,'file':name,'status':'invalid_cache_skipped'});continue
     target=root/slug/name;existing=target.read_bytes() if target.is_file() else b''
     if existing:
      status='verified' if hashlib.sha256(existing).hexdigest()==rec['sha256'] else 'different_nonzero_preserved'
     elif restore:
      atomic_bytes(target,data)
      if hashlib.sha256(target.read_bytes()).hexdigest()!=rec['sha256']:raise ValueError('Recovery checksum failure')
      status='restored'
     else:status='missing_or_zero_recoverable'
     results.append({'slug':slug,'file':name,'status':status,'validated_bytes':len(data)})
   finally:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
 return results

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--root',type=Path,default=ROOT)
 parser.add_argument('--restore',action='store_true')
 args=parser.parse_args();report=finalize(args.root,args.restore);print(json.dumps(report,indent=2))
 raise SystemExit(1 if any(r['status'] in ['different_nonzero_preserved','invalid_cache_skipped','active_writer_skipped','unsafe_manifest_entry_skipped','generation_mismatch_skipped','missing_or_zero_recoverable'] for r in report) else 0)
