# MCS Reference Textures

Processed Minecraft 1.21.1 block textures for use as AI generation references.

## What this is

907 block textures, upscaled to 256×256 using nearest-neighbour interpolation.

For **334 transparent/sprite textures** (plants, saplings, flowers, vines etc.):
transparent pixels are replaced with solid magenta (`#FF00FF`) so AI models
have a clear visual boundary — they cannot accidentally generate content
into areas that should remain transparent.

## Usage in MCS Texture Pack Generator

Set the **Texture Source URL** field to:
```
https://cdn.jsdelivr.net/gh/YOUR_GITHUB_USERNAME/mcs-refs@main/block/
```

## Source

Original 16×16 vanilla textures from:  
[InventivetalentDev/minecraft-assets](https://github.com/InventivetalentDev/minecraft-assets) (1.21.1)
