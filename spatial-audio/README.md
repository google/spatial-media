# Spatial Audio Resources
Google VR Audio enables Ambisonic spatial audio playback in [Google VR SDK](https://developers.google.com/vr/), [YouTube 360/VR](http://yt.be/spatialaudiovrhelp), and [Omnitone](https://googlechrome.github.io/omnitone/#home). It provides ambisonic binaural decoding via Head Related Transfer Functions (HRTFs). This repository contains information and resources that can be used in order to build binaural preview software or to directly monitor the binaural output when creating content in Digital Audio Workstations (DAWs).

# Contents of the directories
## raw symmetric cube hrirs 
This is a set of binaural measurements (Head Related Impulse Responses or HRIRs) taken from a cube loudspeaker configuration. This configuration is used in the Google VR Audio first-order ambisonic binaural decoder.

This set has been derived from the [SADIE binaural measurements](https://www.york.ac.uk/sadie-project/binaural.html) and  is provided as individual time-domain FIR filters.

### Specification & modifications:
subject: 002 (KU100 binaural head)  
sampling rate: 48kHz  
bit depth: 16 bit  
length: 256 samples  
fade-in: none  
fade-out: half-hann (16 samples)  
symmetric: yes (left hemisphere only)  
applied gain: 0dB (none)

Also provided is a preset configuration file for the [ambiX](https://github.com/kronihias/ambix) binaural decoder plugin.

**Note**: Using these filters directly (or via the [ambiX](https://github.com/kronihias/ambix) preset) with your ambisonic mix will **not** result in an output equivalent to Google VR Audio unless you use phase-matched shelf-filters, as recommended by A. J. Heller, R. Lee and  E. M. Benjamin in their paper "[Is My Decoder Ambisonic?](http://www.ai.sri.com/ajh/ambisonics/BLaH3.pdf)". To solve that problem, we also provide a set called *symmetric ambisonic binaural decoder* which contains shelf-filtered, symmetric spherical harmonic HRIRs which can be directly applied to an ambisonic mix via a simple filter operation (please see below).

## symmetric ambisonic binaural decoder
This set represents spherical harmonic HRIR filters used for first-order ambisonic binaural decode in Google VR Audio. To produce the binaural output, these filters should be applied to an ambisonic mix directly and the output routed to the stereo L & R channels as shown in the following diagram:

![symmetric binaural ambisonic decoder - signal flow diagram](https://cloud.githubusercontent.com/assets/26985965/24811254/2143fb12-1b7a-11e7-99a0-cef55c3f8365.png)

The filtering operation (* symbol) can be done using freely available tools, for example, free multichannel convolver plugins like  [LAConvolver](http://audio.lernvall.com/) (mac) or  [Freeverb3](http://www.nongnu.org/freeverb3/) (win). The dotted red line with the Ø symbol denotes 180° phase inversion.

## ambisonic correction filters
This is a set of filters which compensate for the change of HRTFs in the binaural ambisonic decoder. If the ambisonic audio has been mixed against our previous THRIVE HRTFs, applying these filters to the ambiX tracks will minimize the timbral changes after the switch to SADIE KU100 HRTFs. For example, the below diagram shows a frequency response of a decoded sound fields containing a single, broadband sound source in front of the listener. If no compensation is used, switching the binaural decoder from THRIVE to SADIE KU100 will result in spectral changes:

![decoder output before correction](https://cloud.githubusercontent.com/assets/26985965/24811252/21399d66-1b7a-11e7-953c-2357d6be8f3a.png)

After applying the compensation filters, frequency response differences will be minimized:

![decoder output after correction](https://cloud.githubusercontent.com/assets/26985965/24811250/2137f42a-1b7a-11e7-9ff5-e09718293401.png)

The filtering operation (* symbol) can be done using freely available tools, for example, free multichannel convolver plugins like  [LAConvolver](http://audio.lernvall.com/) (mac) or  [Freeverb3](http://www.nongnu.org/freeverb3/) (win).

![ambiX correction filters - signal flow diagram](https://cloud.githubusercontent.com/assets/26985965/24811249/21269c84-1b7a-11e7-8139-91e4fd0d0a20.png)

# FAQs
### Why did you change HRTFs?
Binaural decoding of ambisonic spatial audio relies on Head Related Transfer Functions (or their time-domain equivalents - HRIRs) which are unique to each individual. However, our studies showed that some datasets perform better on average than other datasets, in the case when an individualized set is not available.

We tested a large number of available HRTF datasets in a mobile VR application and using a variety of different sound samples. A panel of 53 experienced listeners (20 of whom were expert assessors) compared the overall subjective audio quality of the interactive binaural renders. We found that SADIE KU100 set performed best for majority of the participants:

![perceived decoder quality](https://cloud.githubusercontent.com/assets/26985965/24811253/213b6628-1b7a-11e7-9079-f7a906e963a0.png)

### Should I use HRTF monitoring when creating ambisonic content for binaural reproduction (e.g. YouTube 360/VR)?
When creating content for YouTube 360/VR it is recommended that you monitor your ambisonic audio using the provided *symmetric ambisonic binaural decoder* and/or preview the final mix directly on YouTube to control the timbre (coloration) and loudness of your mix (please see below).

### What is timbral coloration of HRTFs?
HRTFs add specific coloration to the decoded binaural output signal. However, this coloration is dependent on the HRTF set used (due to individual nature of HRTFs). For example, here is an example HRTF frequency response of the THRIVE set and a similar response of the SADIE KU100 set:

![HRTF coloration](https://cloud.githubusercontent.com/assets/26985965/24811251/2139476c-1b7a-11e7-865b-f37ac10b197f.png)

### Can I adjust my existing ambisonic mix to make it sound the same with the new binaural decoder? 
If you already have produced an ambisonic soundtrack using our THRIVE HRTF set for monitoring, you can simply correct the frequency response of your ambiX tracks to match the frequency response of the new SADIE KU100 HRTF set. This can be done by applying the filters we share in the [ambisonic correction filters](#ambisonic-correction-filters) directory.

### What is expected loudness of the Google VR Audio binaural decoder?
Due to HRTF processing, the output amplitude of your Ambisonic track may differ depending which HRTF set you use. That is why it is important to monitor the binaural output when working on an ambisonic soundtrack using the binaural decoder which is going to be used to render your ambisonic content. Our binaural decoder's loudness should be the same as the loudness of a standard M-S stereo decoder.

For example, the table below shows loudness measured in compliance with the [ITU-R BS.1770-4 recommendation](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-4-201510-I!!PDF-E.pdf) and absolute amplitude peak values when a 0.5 normalized pink noise bursts signal is played at 8 different spatial locations around the listener:

|Decoder     | Loudness [dB LUFS] | Absolute Peak Amplitude |
|------------|--------------------|-------------------------|
|M-S Stereo  |-10.59              |0.5000                   |
|THRIVE      |-10.99              |0.9478                   |
|SADIE KU100 |-11.20              |0.9642                   |

Please note, although the loudness is matched between different decoders and the stereo decoder, the binaural output may result in the peak amplitude exceeding 0dB FS.

### Is there third party software for monitoring binaural output when working with ambisonic audio for YouTube?
Some third party tools like [BlueRippleSound O3A View](http://www.blueripplesound.com/products/o3a-view-vst), [Noisemakers AmbiHead](http://www.noisemakers.fr/ambi-head/) and [SoundParticles](http://soundparticles.com/) (coming soon) implement their own binaural preview tools using the HRTFs from this repository which match those used by YouTube 360/VR.
