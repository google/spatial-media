# Spatial Audio RFC (draft)
*This document describes an open metadata scheme by which MP4 multimedia containers may accommodate spatial and non-diegetic audio. Comments are welcome on the [spatial-media-discuss](https://groups.google.com/forum/#!forum/spatial-media-discuss) mailing list or by [filing an issue](https://github.com/google/spatial-media/issues) on GitHub.*

------------------------------------------------------

## Metadata Format

### MP4
Spatial audio metadata is stored in a new box, `SA3D`, defined in this RFC. Non-diegetic audio metadata is stored in a new box, `SAND`, defined in this RFC. The metadata is applicable to individual tracks in an MP4 container.

#### Spatial Audio Box (SA3D)
##### Definition
Box Type: `SA3D`  
Container: Sound Sample Description box (e.g., `mp4a`, `lpcm`, `sowt`, etc.)  
Mandatory: No  
Quantity: Zero or one  

When present, provides additional information about the spatial audio content contained in this audio track.

##### Syntax
```
aligned(8) class SpatialAudioBox extends Box(‘SA3D’) {
    unsigned int(8)  version;
    unsigned int(8)  ambisonic_type;
    unsigned int(32) ambisonic_order;
    unsigned int(8)  ambisonic_channel_ordering;
    unsigned int(8)  ambisonic_normalization;
    unsigned int(32) num_channels;
    for (i = 0; i < num_channels; i++) {
        unsigned int(32) channel_map;
    }
}
```

##### Semantics
- `version` is an 8-bit unsigned integer that specifies the version of this box. Must be set to `0`.

- `ambisonic_type` is an 8-bit unsigned integer that specifies the type of ambisonic audio represented; the following values are defined:

| `ambisonic_type` | Ambisonic Type Description |
|:-----------------|:---------------------------|
|   `0`   | **Periphonic**: Indicates that the audio stored is a periphonic ambisonic sound field (i.e., full 3D). |

- `ambisonic_order` is a 32-bit unsigned integer that specifies the order of the ambisonic sound field. If the `ambisonic_type` is `0` (*periphonic*), this is a non-negative integer representing the periphonic ambisonic order; in this case, it should take a value of `sqrt(n) - 1`, where `n` is the number of channels in the represented ambisonic audio data. For example, a *periphonic* ambisonic sound field with `ambisonic_order = 1` requires `(ambisonic_order + 1)^2 = 4` ambisonic components.

- `ambisonic_channel_ordering` is an 8-bit integer specifying the channel ordering (i.e., spherical harmonics component ordering) used in the represented ambisonic audio data; the following values are defined:

| `ambisonic_channel_ordering` | Channel Ordering Description |
|:-----------------------------|:-----------------------------|
|   `0`   | **ACN**: The channel ordering used is the *Ambisonic Channel Number* (ACN) system. In this, given a spherical harmonic of degree `l` and order `m`, the corresponding ordering index `n` is given by `n = l * (l + 1) + m`. |

- `ambisonic_normalization` is an 8-bit unsigned integer specifying the normalization (i.e., spherical harmonics normalization) used in the represented ambisonic audio data; the following values are defined:

| `ambisonic_normalization` | Normalization Description |
|:--------------------------|:--------------------------|
|   `0`   | **SN3D**: The normalization used is *Schmidt semi-normalization* (SN3D). In this, the spherical harmonic of degree `l` and order `m` is normalized according to `sqrt((2 - δ(m)) * ((l - m)! / (l + m)!))`, where `δ(m)` is the *Kronecker delta* function, such that `δ(0) = 1` and `δ(m) = 0` otherwise. |

- `num_channels` is a 32-bit unsigned integer specifying the number of audio channels contained in the given audio track.

- `channel_map` is a sequence of 32-bit unsigned integers that maps audio channels in a given audio track to ambisonic components, given the defined `ambisonic_channel_ordering`. The sequence of `channel_map` values should match the channel sequence within the given audio track.

  For example, consider a 4-channel audio track containing ambisonic components *W*, *X*, *Y*, *Z* at channel indexes 0, 1, 2, 3, respectively. For `ambisonic_channel_ordering = 0` (ACN), the ordering of components should be *W*, *Y*, *Z*, *X*, so the `channel_map` sequence should be `0`, `2`, `3`, `1`.

  As a simpler example, for a 4-channel audio track containing ambisonic components *W*, *Y*, *Z*, *X* at channel indexes 0, 1, 2, 3, respectively, the `channel_map` sequence should be specified as `0`, `1`, `2`, `3` when `ambisonics_channel_odering = 0` (ACN).

##### Example

Here is an example MP4 box hierarchy for a file containing the `SA3D` box:

- moov
  - trak
    - mdia
      - minf
        - stbl
          - stsd
            - mp4a
              - esds
              - SA3D

where the `SA3D` box has the following data:

| Field Name | Value |
|:-----------|:-----|
| `version` | `0` |
| `ambisonic_type` | `0` |
| `ambisonic_order` | `1` |
| `ambisonic_channel_ordering` | `0` |
| `ambisonic_normalization` | `0` |
| `num_channels` | `4` |
| `channel_map` | `0` |
| `channel_map` | `2` |
| `channel_map` | `3` |
| `channel_map` | `1` |

------------------------------------------------------

#### Non-Diegetic Audio Box (SAND)
##### Definition
Box Type: `SAND`  
Container: Sound Sample Description box (e.g., `mp4a`, `lpcm`, `sowt`, etc.)  
Mandatory: No  
Quantity: Zero or one  

When present, provides additional information about the non-diegetic audio content contained in this audio track. This can be used alongisde `SA3D` in a head-tracked virtual reality experience to provide audio which should remain unchanged by listener head rotation; e.g., narration or stereo music.

##### Syntax
```
aligned(8) class NonDiegeticAudioBox extends Box(‘SAND’) {
    unsigned int(8)  version;
}
```

##### Semantics
- `version` is an 8-bit unsigned integer that specifies the version of this box. Must be set to `0`.

##### Example

Here is an example MP4 box hierarchy for a file containing the `SA3D` and `SAND` boxes, to mix spatial audio with non-diegetic audio:

- moov
  - trak
    - mdia
      - minf
        - stbl
          - stsd
            - mp4a
              - esds
              - SA3D
  - trak
    - mdia
      - minf
        - stbl
          - stsd
            - mp4a
              - esds
              - SAND 

where the `SAND` box has the following data:

| Field Name | Value |
|:-----------|:-----|
| `version` | `0` |

------------------------------------------------------

## Appendix 1 - Ambisonics
The traditional notion of ambisonics is used, where the sound field is represented by spherical harmonics coefficients using the *associated Legendre polynomials* (without *Condon-Shortley phase*) as the basis functions. Thus, the spherical harmonic of degree `l` and order `m` at elevation `E` and azimuth `A` is given by:

    N(l, abs(m)) * P(l, abs(m), sin(E)) * T(m, A)

where:
- `N(l, m)` is the spherical harmonics normalization function used.
- `P(l, m, x)` is the (unnormalized) *associated Legendre polynomial*, without *Condon-Shortley phase*, of degree `l` and order `m` evaluated at `x`.
- `T(m, x)` is `sin(-m * x)` for `m < 0` and `cos(m * x)` otherwise.

### Conventions
#### Azimuth
- `A = 0`: The source is in front of the listener.
- `A` in `(0, pi/2)`: The source is in the forward-left quadrant.
- `A` in `(pi/2, pi)`: The source is in the back-left quadrant.
- `A` in `(-pi/2, 0)`: The source is in the forward-right quadrant.
- `A` in `(-pi, -pi/2)`: The source is in the back-right quadrant.

#### Elevation
- `E = 0`: The source is in the horizontal plane.
- `E` in `(0, pi/2]`: The source is above the listener.
- `E` in `[-pi/2, 0)`: The source is below the listener.
