# Anki OCR Service

A very stripped down port of
[vgtranslate](https://gitlab.com/spherebeaker/vgtranslate) with a focus on
running OCR through [Retroarch's AI
Service](https://docs.libretro.com/guides/ai-service/) and copying the results
to the clipboard, rather than automatic translations. It is packaged as an Anki
addon for ease of installation for language learners.

## Installation

This is experimental and not yet available on AnkiWeb. However, you may
alternatively download it from the GitHub releases page, then install in Anki
via `Tools -> Add-ons -> Install from file…`

## Configuration

Configuration is different (and much simpler) than vgtranslate. You can
configure it through Anki after installing via `Tools -> Add-ons -> OCR Service
-> Config`. See [config.md](config.md).

**Note: Google Cloud Vision support is not yet working.**

**Note: Tesseract/OpenCV support has been gutted from vgtranslate for ease of
porting to an Anki plugin. I may reintroduce it, I may not.**

On the RetroArch side, open `Settings -> Accessibility -> AI Service`, enable
it, and set the `AI Service Output` to `Speech Mode`. (Anki OCR Service does not
actually do any Text-to-Speech, but out of the three options available, it's the
least intrusive to fake.) Set your source language to your desired language;
Anki OCR Service ignores the target language.

Additionally, ensure that you have a hotkey set for activating the service
(`Settings -> Input -> Hotkeys -> AI Service`).

As long as Anki is running with Anki OCR Service installed and properly
configured, you can now activate the AI Service in RetroArch and the resulting
text will be copied to the clipboard automatically.
