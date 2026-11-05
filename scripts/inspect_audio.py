#!/usr/bin/env python3
"""Measure local audio without changing files or identifying sounds. Python 3.9+."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

EXTENSIONS = {'.mp4', '.mov', '.mxf', '.mkv', '.avi', '.mts', '.m2ts', '.webm',
              '.m4v', '.mpg', '.mpeg', '.wmv', '.mp3', '.wav', '.m4a', '.aac',
              '.flac', '.ogg', '.aif', '.aiff', '.opus'}


def linked(path):
    return path.is_symlink() or getattr(path.lstat(), 'st_reparse_tag', None) in {
        0xA0000003, 0xA000000C}  # Windows junctions and symbolic links.


def fingerprint(path):
    s = path.stat()
    return (s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_dev, s.st_ino)


def number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def run(args):
    p = subprocess.run(args, capture_output=True, timeout=300)
    if p.returncode:
        raise RuntimeError(p.stderr.decode('utf-8', errors='replace')[-1500:])
    return p


def beat_estimate(path, ffmpeg):
    if importlib.util.find_spec('librosa') is None:
        return {'status': 'not_checked', 'reason': 'optional librosa is not installed'}
    try:
        import librosa
        import numpy as np
        # Bound the optional analysis: footage/audio can otherwise be hours long.
        raw = run([ffmpeg, '-v', 'error', '-i', str(path), '-map', '0:a:0',
                   '-t', '300', '-ac', '1', '-ar', '22050', '-f', 'f32le', '-'])
        y = np.frombuffer(raw.stdout, dtype='<f4').copy()
        seconds = len(y) / 22050
        if seconds < 2 or not np.any(y):
            return {'status': 'not_checked', 'reason': 'silent or shorter than 2 seconds',
                    'analyzed_start_s': 0, 'analyzed_end_s': seconds}
        onset = librosa.onset.onset_strength(y=y, sr=22050, hop_length=512)
        bpm, _ = librosa.beat.beat_track(onset_envelope=onset, sr=22050, hop_length=512)
        bpm = float(np.asarray(bpm).reshape(-1)[0])
        if not math.isfinite(bpm) or bpm <= 0:
            return {'status': 'not_checked', 'reason': 'no positive tempo estimate'}
        return {'status': 'approximate', 'bpm': round(bpm, 2),
                'half_bpm': round(bpm / 2, 2), 'double_bpm': round(bpm * 2, 2),
                'analyzed_start_s': 0, 'analyzed_end_s': round(seconds, 3),
                'method': 'librosa onset envelope and beat_track, first 300 seconds maximum',
                'warning': 'May follow speech, transients or half/double pulse; not proof of musical tempo'}
    except Exception as exc:
        return {'status': 'not_checked', 'reason': 'optional beat analysis failed: ' + str(exc)[:500]}


def inspect(path, root, ffprobe, ffmpeg):
    row = {'relative_path': path.relative_to(root).as_posix(), 'size_bytes': None,
           'duration_seconds': None, 'audio_stream_index': None,
           'measurement_scope': 'first audio stream, complete mixed track; not isolated BGM/SFX',
           'integrated_lufs': None, 'true_peak_dbtp': None, 'loudness_range_lu': None,
           'measurement_status': 'not_checked', 'tempo': {'status': 'not_checked'},
           'source_stability': 'unchecked', 'usable': False}
    try:
        before = fingerprint(path)
        if linked(path):
            raise OSError('source became a symlink/junction before inspection')
        row['size_bytes'] = before[0]
    except OSError as exc:
        row.update(measurement_status='error', source_stability='unavailable',
                   error=str(exc)[:1500])
        return row
    try:
        probe = json.loads(run([ffprobe, '-v', 'error', '-show_entries',
                               'format=duration:stream=index,codec_type,sample_rate,channels',
                               '-of', 'json', str(path)]).stdout)
        row['duration_seconds'] = number(probe.get('format', {}).get('duration'))
        streams = [s for s in probe.get('streams', []) if s.get('codec_type') == 'audio']
        if streams:
            row['audio_stream_index'] = streams[0]['index']
            row['audio_stream_count'] = len(streams)
            loud = run([ffmpeg, '-hide_banner', '-nostats', '-i', str(path), '-map',
                        '0:a:0', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json',
                        '-f', 'null', '-'])
            matches = re.findall(r'\{\s*"input_i".*?\}', loud.stderr.decode('utf-8', errors='replace'), re.S)
            if not matches:
                raise RuntimeError('ffmpeg did not return loudnorm input measurements')
            stats = json.loads(matches[-1])
            row.update(integrated_lufs=number(stats.get('input_i')),
                       true_peak_dbtp=number(stats.get('input_tp')),
                       loudness_range_lu=number(stats.get('input_lra')),
                       measurement_status='measured')
            if row['integrated_lufs'] is None:
                row['measurement_note'] = 'Non-finite loudness (for example silence) is stored as null'
            row['tempo'] = beat_estimate(path, ffmpeg)
        else:
            row['measurement_status'] = 'no_audio_stream'
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        row['measurement_status'] = 'error'
        row['error'] = str(exc)[:1500]
    try:
        unchanged = not linked(path) and before == fingerprint(path)
    except OSError:
        unchanged = False
    row['source_stability'] = 'stat_unchanged' if unchanged else 'unstable'
    row['usable'] = unchanged and row['measurement_status'] == 'measured'
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path, help='Local audio/video file or folder')
    parser.add_argument('--output', required=True, type=Path, help='New JSON file; parent must exist')
    args = parser.parse_args()
    try:
        if not args.source.exists() or linked(args.source):
            raise ValueError('source must exist and cannot be a symlink/junction')
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('output already exists; choose a new JSON path')
        if not args.output.parent.is_dir():
            raise ValueError('output parent must already exist')
        ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
        if not ffmpeg or not ffprobe:
            raise ValueError('ffmpeg and ffprobe are required; no installation was attempted')
        source = args.source.resolve()
        root = source if source.is_dir() else source.parent
        paths, skipped = [], []
        if source.is_file():
            paths = [source]
        else:
            def walk_error(exc):
                skipped.append({'path': str(exc.filename), 'reason': str(exc)})
            for parent, dirs, files in os.walk(source, followlinks=False, onerror=walk_error):
                for d in list(dirs):
                    child = Path(parent) / d
                    try:
                        unsafe = linked(child) or not child.resolve().is_relative_to(root)
                    except OSError as exc:
                        dirs.remove(d)
                        skipped.append({'path': str(child.relative_to(root)), 'reason': str(exc)})
                        continue
                    if unsafe:
                        dirs.remove(d)
                        skipped.append({'path': str(child.relative_to(root)), 'reason': 'linked directory'})
                for f in files:
                    child = Path(parent) / f
                    if child.suffix.lower() not in EXTENSIONS:
                        continue
                    try:
                        unsafe = linked(child) or not child.resolve().is_relative_to(root)
                    except OSError as exc:
                        skipped.append({'path': str(child.relative_to(root)), 'reason': str(exc)})
                        continue
                    if unsafe:
                        skipped.append({'path': str(child.relative_to(root)), 'reason': 'linked file'})
                    else:
                        paths.append(child)
        result = {'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(),
                  'source_root': str(root),
                  'method': 'ffmpeg loudnorm input_* measurements; null sink; source media unchanged',
                  'limits': ['No listening, sound identity or BGM/SFX separation is claimed.',
                             'Tempo is optional, approximate, and may be half/double actual musical pulse.',
                             'stat_unchanged is a before/after comparison, not an exclusive lock.'],
                  'files': [inspect(p, root, ffprobe, ffmpeg) for p in sorted(paths)], 'skipped': skipped}
        with args.output.open('x', encoding='utf-8', newline='\n') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write('\n')
        print(f"Saved {len(result['files'])} audio inspections: {args.output}")
        return 0
    except (OSError, ValueError) as exc:
        print('Audio inspection failed: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
