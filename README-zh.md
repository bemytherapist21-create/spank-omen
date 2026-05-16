# spank-omen

[English README](./README.md)

`spank-omen` 是 [`taigrr/spank`](https://github.com/taigrr/spank) 的实验性 fork。

当前版本仍然使用 Apple Silicon 加速度传感器检测笔记本撞击，并播放音频回应。这个 fork 的目标是逐步演进为 Windows 麦克风输入 + 声音分类 + 可扩展动作系统。

## 当前状态

- 当前 Go 版本仍然适用于受支持的 Apple Silicon macOS 设备。
- 当前仍然需要 `sudo` 访问 IOKit HID 加速度传感器。
- Windows 原生麦克风检测还在计划中。
- 已加入更多运行时调节能力、自定义音频、JSON stdin 控制、音量缩放、播放速度控制等方向。

## 规划路线

```text
Mic Input
-> Audio Processing
-> Slap Classification
-> Cooldown Check
-> Mode Handler
-> Audio Playback
-> Optional RGB / OBS / AI Actions
```

## 说明

上传到 GitHub 前，请以英文 README 为准。那里包含当前构建方式、使用方式、发布说明、路线图和原项目署名。

本项目保留原 MIT 许可证和原项目署名。
