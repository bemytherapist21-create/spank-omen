from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from detector.calibration import calibrate
from detector.mic_input import AudioFrame, _downmix_mono, _preferred_devices, simulated_frames
from detector.slap_detector import SlapDetector
from main import apply_fast_preset, parse_args, selected_device
from modes import create_mode
from utils.cooldown import Cooldown
from utils.player import _next_power_of_two, _volume_from_amplitude


class WindowsBackendTests(unittest.TestCase):
    def test_simulated_frames_trigger_detector(self) -> None:
        detector = SlapDetector(min_amplitude=0.25, min_rms=0.015)
        events = [
            event
            for frame in simulated_frames(duration=2.0)
            if (event := detector.process(frame)) is not None
        ]

        self.assertGreaterEqual(len(events), 2)
        self.assertTrue(all(event.confidence > 0 for event in events))

    def test_cooldown_blocks_repeated_events(self) -> None:
        cooldown = Cooldown(500)

        self.assertTrue(cooldown.ready(10.0))
        cooldown.mark(10.0)
        self.assertFalse(cooldown.ready(10.2))
        self.assertTrue(cooldown.ready(10.5))

    def test_random_mode_loads_mp3s(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pain").mkdir()
            audio_file = root / "pain" / "00.mp3"
            audio_file.write_bytes(b"fake")

            mode = create_mode("pain", root)
            self.assertEqual(mode.choose(0.5, 1.0), audio_file)

    def test_escalation_mode_can_skip_short_intro_clips(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sexy").mkdir()
            for index in range(3):
                (root / "sexy" / f"{index:02d}.mp3").write_bytes(b"fake")

            mode = create_mode("sexy", root, min_index=2)

            self.assertEqual(mode.choose(0.5, 1.0).name, "02.mp3")

    def test_volume_scaling_is_bounded(self) -> None:
        self.assertGreaterEqual(_volume_from_amplitude(0.0), 0.0)
        self.assertLessEqual(_volume_from_amplitude(10.0), 1.0)
        self.assertLess(_volume_from_amplitude(0.1), _volume_from_amplitude(0.8))

    def test_calibration_recommends_thresholds(self) -> None:
        result = calibrate(simulated_frames(duration=2.0))

        self.assertGreater(result.frames, 0)
        self.assertGreater(result.recommended_min_amplitude, 0)
        self.assertGreater(result.recommended_min_rms, 0)
        self.assertIn("--min-amplitude", result.command)

    def test_calibration_handles_quiet_laptop_mics(self) -> None:
        quiet_frames = [
            AudioFrame(samples=[0.0, 0.0001, -0.0001, 0.008, -0.004], sample_rate=48000, timestamp=1.0),
            AudioFrame(samples=[0.0, 0.0001, -0.0001, 0.006, -0.003], sample_rate=48000, timestamp=1.1),
        ]

        result = calibrate(quiet_frames)

        self.assertLess(result.recommended_min_amplitude, 0.02)
        self.assertLess(result.recommended_min_rms, 0.01)

    def test_selected_device_parses_integer_indices(self) -> None:
        self.assertEqual(selected_device("9"), 9)
        self.assertEqual(selected_device("Microphone Array"), "Microphone Array")
        self.assertIsNone(selected_device(None))

    def test_downmix_mono_averages_multichannel_rows(self) -> None:
        self.assertEqual(_downmix_mono([[1.0, -1.0], [0.25, 0.75]]), [0.0, 0.5])

    def test_preferred_devices_avoids_wdmks_outputs(self) -> None:
        devices = [
            {
                "index": 14,
                "name": "Headset (HD 350BT)",
                "channels": 1,
                "default_sample_rate": 16000,
                "hostapi": "Windows WASAPI",
            },
            {
                "index": 18,
                "name": "PC Speaker (Realtek HD Audio output with HAP)",
                "channels": 2,
                "default_sample_rate": 48000,
                "hostapi": "Windows WDM-KS",
            },
            {
                "index": 15,
                "name": "Microphone Array (AMD Audio Device)",
                "channels": 2,
                "default_sample_rate": 48000,
                "hostapi": "Windows WASAPI",
            },
        ]

        self.assertEqual(_preferred_devices(devices)[0]["index"], 15)

    def test_parse_args_supports_monitor(self) -> None:
        args = parse_args(["--monitor", "--duration", "1", "--simulate"])

        self.assertTrue(args.monitor)
        self.assertTrue(args.simulate)
        self.assertEqual(args.duration, 1)

    def test_parse_args_supports_play_test(self) -> None:
        args = parse_args(["--mode", "halo", "--play-test", "--play-index", "2"])

        self.assertTrue(args.play_test)
        self.assertEqual(args.mode, "halo")
        self.assertEqual(args.play_index, 2)

    def test_parse_args_supports_min_audio_index(self) -> None:
        args = parse_args(["--mode", "sexy", "--min-audio-index", "20"])

        self.assertEqual(args.min_audio_index, 20)

    def test_fast_mode_uses_low_latency_settings(self) -> None:
        args = parse_args(["--fast", "--block-ms", "20", "--cooldown", "650", "--audio-buffer-ms", "12"])

        apply_fast_preset(args)

        self.assertEqual(args.block_ms, 5)
        self.assertEqual(args.cooldown, 250)
        self.assertEqual(args.audio_buffer_ms, 8)

    def test_next_power_of_two_for_mixer_buffer(self) -> None:
        self.assertEqual(_next_power_of_two(128), 128)
        self.assertEqual(_next_power_of_two(129), 256)


if __name__ == "__main__":
    unittest.main()
