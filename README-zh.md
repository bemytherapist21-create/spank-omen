# spank-omen

[English README](./README.md)

This short file is kept as a pointer to the English README.

Current status:

- Windows users should run the Python microphone backend with `python main.py`.
- macOS Apple Silicon users can still run the Go accelerometer backend.
- The AI classifier hook exists, but a trained PyTorch model is not included yet.

Quick Windows test:

```powershell
python main.py --simulate --duration 3 --no-playback
```

Calibration:

```powershell
python main.py --calibrate --duration 6 --device 9
```

For full setup, usage, roadmap, and attribution, see [README.md](./README.md).
