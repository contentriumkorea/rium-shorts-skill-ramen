#!/usr/bin/env python3
"""Read-only footage inventory. Requires ffprobe; never changes source media."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


EXTENSIONS = {'.mp4', '.mov', '.mxf', '.mkv', '.avi', '.mts', '.m2ts',
              '.webm', '.m4v', '.mpg', '.mpeg', '.wmv', '.mp3', '.wav',
              '.m4a', '.aac', '.flac', '.ogg', '.aif', '.aiff', '.opus'}


def parse_time(raw):
    value = datetime.fromisoformat(raw.strip().replace('Z', '+00:00'))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('timezone_missing')
    return value


def is_link(path):
    s = path.lstat()
    return stat.S_ISLNK(s.st_mode) or getattr(s, 'st_reparse_tag', None) in {
        getattr(stat, 'IO_REPARSE_TAG_MOUNT_POINT', 0xA0000003),
        getattr(stat, 'IO_REPARSE_TAG_SYMLINK', 0xA000000C),
    }


def inside(path, root):
    try:
        path.resolve().relative_to(root)
        return True
    except (ValueError, OSError):
        return False


def signature(s):
    return (s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_dev, s.st_ino)


def load_corrections(path):
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict):
        raise ValueError('metadata-map must be an object keyed by relative paths')
    for key, row in data.items():
        rel = PurePosixPath(key)
        if (not key or '\\' in key or ':' in key or rel.is_absolute()
                or '..' in rel.parts or str(rel) != key):
            raise ValueError('metadata-map keys must be normalized relative paths: ' + key)
        if not isinstance(row, dict):
            raise ValueError('metadata-map entry must be an object: ' + key)
        for field in ('shot_at', 'location', 'evidence'):
            if field in row and (not isinstance(row[field], str) or not row[field].strip()):
                raise ValueError(f'{key}: {field} must be a nonempty string')
        if ('shot_at' in row or 'location' in row) and not row.get('evidence'):
            raise ValueError(key + ': corrected time/location requires evidence')
        if 'shot_at' in row:
            parse_time(row['shot_at'])
    return data


def choose_time(probe, correction, zone):
    candidates = []
    sources = [('format', probe.get('format', {}))]
    sources += [('stream:' + str(s.get('index', i)), s)
                for i, s in enumerate(probe.get('streams', []))]
    for source, data in sources:
        for tag, raw in (data.get('tags') or {}).items():
            if tag.lower() != 'creation_time':
                continue
            item = {'source': source, 'raw': raw}
            try:
                dt = parse_time(raw)
                item.update(status='offset_present', utc=dt.astimezone(timezone.utc).isoformat(),
                            local=dt.astimezone(zone).isoformat())
            except (ValueError, TypeError, AttributeError) as exc:
                item['status'] = 'timezone_missing' if str(exc) == 'timezone_missing' else 'invalid'
            candidates.append(item)
    instants = {c['utc'] for c in candidates if 'utc' in c}
    conflict = len(instants) > 1
    ambiguous = any(c['status'] != 'offset_present' for c in candidates)
    result = {'creation_time_candidates': candidates, 'metadata_conflict': conflict,
              'timezone_ambiguous_or_invalid': ambiguous, 'shot_at': None,
              'source': 'unknown', 'evidence': None}
    if correction.get('shot_at'):
        result.update(shot_at=parse_time(correction['shot_at']).astimezone(zone).isoformat(),
                      source='user_verified_map', evidence=correction['evidence'])
    elif len(instants) == 1 and not ambiguous:
        result.update(shot_at=candidates[0]['local'], source='consistent_creation_time_candidate',
                      evidence='Explicit timezone and matching container/stream tags; camera clock not verified')
    return result


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def inspect_file(path, root, zone, correction, hash_files, ffprobe):
    before = path.stat()
    row = {'relative_path': path.relative_to(root).as_posix(), 'size_bytes': before.st_size,
           'mtime_utc': datetime.fromtimestamp(before.st_mtime, timezone.utc).isoformat(),
           'mtime_ns': before.st_mtime_ns, 'source_stability': 'unchecked', 'sha256': None,
           'duration_seconds': None, 'streams': [], 'probe_error': None}
    probe = {}
    try:
        p = subprocess.run([ffprobe, '-v', 'error', '-show_format', '-show_streams',
                            '-of', 'json', str(path)], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=120)
        if p.returncode:
            row['probe_error'] = (p.stderr.strip() or 'ffprobe failed')[:2000]
        else:
            probe = json.loads(p.stdout)
            duration = probe.get('format', {}).get('duration')
            row['duration_seconds'] = float(duration) if duration is not None else None
            fields = ('index', 'codec_type', 'codec_name', 'width', 'height',
                      'avg_frame_rate', 'r_frame_rate', 'sample_rate', 'channels',
                      'channel_layout', 'duration')
            row['streams'] = [{k: s[k] for k in fields if k in s}
                              for s in probe.get('streams', [])]
        if hash_files:
            row['sha256'] = sha256(path)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        row['probe_error'] = str(exc)[:2000]
    try:
        stable = (not is_link(path) and inside(path, root)
                  and signature(before) == signature(path.stat()))
    except OSError:
        stable = False
    row['source_stability'] = 'stat_unchanged' if stable else 'unstable'
    # Stat comparison detects common concurrent writes, not a filesystem lock.
    row['hash_usable_for_duplicates'] = bool(stable and row['sha256'])
    row['capture_time'] = choose_time(probe, correction, zone)
    row['location'] = correction.get('location', '장소 미확인')
    row['location_evidence'] = correction.get('evidence') if correction.get('location') else None
    selected = row['capture_time']['shot_at'] if stable else None
    row['group'] = {'date': selected[:10] if selected else '날짜 미확인',
                    'hour': selected[11:13] if selected else '시간 미확인',
                    'location': row['location']}
    return row


def inventory(source, zone, corrections, hash_files, ffprobe):
    rows, skipped = [], []
    def walk_error(exc):
        skipped.append({'path': str(exc.filename), 'reason': str(exc)})
    for parent, dirs, files in os.walk(source, followlinks=False, onerror=walk_error):
        parent = Path(parent)
        for name in list(dirs):
            child = parent / name
            try:
                unsafe = is_link(child) or not inside(child, source)
            except OSError:
                unsafe = True
            if unsafe:
                dirs.remove(name)
                skipped.append({'path': child.relative_to(source).as_posix(), 'reason': 'linked_or_unreadable_directory'})
        dirs.sort()
        for name in sorted(files):
            child = parent / name
            if child.suffix.lower() not in EXTENSIONS:
                continue
            relative = child.relative_to(source).as_posix()
            try:
                if is_link(child) or not inside(child, source):
                    skipped.append({'path': relative, 'reason': 'linked_file'})
                    continue
                rows.append(inspect_file(child, source, zone, corrections.get(relative, {}), hash_files, ffprobe))
            except OSError as exc:
                skipped.append({'path': relative, 'reason': str(exc)})
    hashes = {}
    for row in rows:
        if row['hash_usable_for_duplicates']:
            hashes.setdefault(row['sha256'], []).append(row['relative_path'])
    return {'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(),
            'source_root': str(source), 'group_timezone': zone.key,
            'notes': ['mtime is file metadata, never a shooting date.',
                      'Consistent creation_time tags remain unverified camera-clock candidates.',
                      'stat_unchanged is a comparison, not an exclusive lock.'],
            'files': rows, 'skipped': skipped,
            'unused_metadata_map_keys': sorted(set(corrections) - {r['relative_path'] for r in rows}),
            'duplicate_hash_groups': [{'sha256': h, 'relative_paths': paths}
                                      for h, paths in hashes.items() if len(paths) > 1]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--timezone', default='Asia/Seoul')
    p.add_argument('--hash', action='store_true', dest='hash_files')
    p.add_argument('--metadata-map', type=Path)
    args = p.parse_args()
    try:
        if not args.source.is_dir() or is_link(args.source):
            raise ValueError('source must be an existing non-linked directory')
        source = args.source.resolve()
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('output already exists; choose a new JSON path')
        if not args.output.parent.is_dir():
            raise ValueError('output parent must already exist')
        zone = ZoneInfo(args.timezone)
        corrections = load_corrections(args.metadata_map)
        ffprobe = shutil.which('ffprobe')
        if not ffprobe:
            raise ValueError('ffprobe is required and was not found; no install was attempted')
        result = inventory(source, zone, corrections, args.hash_files, ffprobe)
        with args.output.open('x', encoding='utf-8', newline='\n') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write('\n')
        print(f"Saved {len(result['files'])} files; {len(result['skipped'])} skipped: {args.output}")
        return 0
    except (OSError, ValueError, ZoneInfoNotFoundError) as exc:
        print('Inventory failed: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
